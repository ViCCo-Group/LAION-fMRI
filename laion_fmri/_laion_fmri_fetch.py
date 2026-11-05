"""Fetch LAION-fMRI data directly from the S3 bucket.

The bucket is BIDS-shaped, so callers can target individual files
through standard BIDS entities (``ses``, ``task``, ``space``,
``desc``, ``stat``, ``suffix``, ``extension``). Each filter is
optional, accepts a string or a list of strings, and is applied
permissively -- a file that lacks an entity is not excluded by a
filter on that entity (so subject-level summaries survive a
``ses=`` filter).
"""

import os
import re
import subprocess
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from laion_fmri._bidsify import bidsify_local_key
from laion_fmri._errors import NoMatchingDataError
from laion_fmri._paths import r2mean_path
from laion_fmri._progress import DownloadProgress
from laion_fmri._s3_engine import (
    download_key,
    list_prefix_objects,
    list_top_level_objects,
)
from laion_fmri._sources import (
    HELD_OUT_EXEMPT_PREFIX,
    HELD_OUT_EXEMPT_TASKS,
    HELD_OUT_SESSIONS,
    LAION_FMRI_BUCKET,
    MAPPING_SESSIONS,
    SHARED_ANATOMY_SESSION,
)

DATASET_LEVEL_KEYS = (
    "dataset_description.json",
    "participants.tsv",
    "participants.json",
    "README",
)

#: BIDS entities exposed as filter kwargs (in BIDS short form).
BIDS_ENTITIES = (
    "ses", "task", "space", "desc", "stat", "run", "echo", "part",
)


def _clamp_n_jobs(n_jobs):
    """Validate ``n_jobs``; warn and fall back to a working value.

    Returns ``1`` if ``n_jobs`` is not a positive int, or clamps
    excessively-high values to a sensible upper bound based on
    available CPUs.
    """
    if not isinstance(n_jobs, int) or isinstance(n_jobs, bool):
        warnings.warn(
            f"n_jobs must be a positive int; got {n_jobs!r}. "
            "Falling back to sequential downloads (n_jobs=1).",
            UserWarning,
            stacklevel=3,
        )
        return 1
    if n_jobs < 1:
        warnings.warn(
            f"n_jobs must be a positive int; got {n_jobs}. "
            "Falling back to sequential downloads (n_jobs=1).",
            UserWarning,
            stacklevel=3,
        )
        return 1

    cpu_count = os.cpu_count() or 4
    upper = max(32, cpu_count * 2)
    if n_jobs > upper:
        warnings.warn(
            f"n_jobs={n_jobs} is higher than recommended for this "
            f"machine; clamping to n_jobs={upper}.",
            UserWarning,
            stacklevel=3,
        )
        return upper
    return n_jobs


def _normalize(entity, value):
    """Return ``value`` with any leading ``entity-`` prefix stripped."""
    prefix = f"{entity}-"
    if value.startswith(prefix):
        return value[len(prefix):]
    return value


def _entity_in_key(key, entity):
    """True if ``entity-<value>`` appears anywhere in the key."""
    pattern = (
        rf"(?:^|/|_){re.escape(entity)}-[A-Za-z0-9]+(?=[_./]|$)"
    )
    return re.search(pattern, key) is not None


def _entity_value_matches(key, entity, value):
    """True if the token ``entity-value`` is present in the key."""
    token = f"{entity}-{value}"
    pattern = rf"(?:^|/|_){re.escape(token)}(?=[_./]|$)"
    return re.search(pattern, key) is not None


def _matches_filters(key, filters):
    """Apply every active BIDS filter to ``key``.

    ``filters`` is a dict mapping entity short name (or
    ``"suffix"`` / ``"extension"``) to a string or list of strings.

    ``ses`` is **strict**: a file lacking a ses entity is rejected
    by a ses filter unless the literal value ``"averages"`` is in
    the filter list. Other entities remain permissive (lacking the
    entity does not exclude the file).
    """
    filename = key.rsplit("/", 1)[-1]
    base, _, ext = filename.partition(".")
    suffix = base.rsplit("_", 1)[-1] if "_" in base else base

    # JSON sidecars carry the BIDS metadata for their NIfTI sibling.
    # When the caller filtered by ``suffix=`` and a sidecar matches
    # that suffix, pull it through regardless of the ``extension``
    # filter so the data file and its sidecar always travel together.
    suffix_filter = filters.get("suffix")
    if isinstance(suffix_filter, str):
        suffix_filter_values = [suffix_filter]
    elif suffix_filter is None:
        suffix_filter_values = None
    else:
        suffix_filter_values = list(suffix_filter)
    sidecar_override = (
        ext == "json"
        and suffix_filter_values is not None
        and suffix in suffix_filter_values
    )

    for fname, fvalues in filters.items():
        if fvalues is None:
            continue
        if isinstance(fvalues, str):
            fvalues = [fvalues]

        if fname == "suffix":
            if suffix not in fvalues:
                return False
            continue
        if fname == "extension":
            if sidecar_override:
                continue
            if ext not in fvalues:
                return False
            continue

        if fname == "ses":
            if not _matches_ses(key, fvalues):
                return False
            continue

        # Permissive logic for other BIDS entities
        normalized = [_normalize(fname, v) for v in fvalues]
        if not _entity_in_key(key, fname):
            continue
        if not any(
            _entity_value_matches(key, fname, v) for v in normalized
        ):
            return False

    return True


def _is_held_out(key):
    """True if ``key`` is in a held-out session and not an exempt
    localizer derivative."""
    for ses in HELD_OUT_SESSIONS:
        if f"/{ses}/" in key or key.endswith(f"/{ses}"):
            if not key.startswith(HELD_OUT_EXEMPT_PREFIX):
                return True
            return not any(f"task-{t}_" in key or f"task-{t}." in key
                           for t in HELD_OUT_EXEMPT_TASKS)
    return False


def _matches_ses(key, fvalues):
    """Strict ses match.

    A file matches when:

    * its ses entity (in path or filename) equals one of the
      requested values, OR
    * it has no ses entity at all *and* ``"averages"`` is among
      the requested values.
    """
    normalized = [_normalize("ses", v) for v in fvalues]
    wants_averages = "averages" in normalized
    ses_values = [v for v in normalized if v != "averages"]

    if _entity_in_key(key, "ses"):
        return any(
            _entity_value_matches(key, "ses", v)
            for v in ses_values
        )
    return wants_averages


def _local_matches(path, expected_size):
    """True iff ``path`` exists with exactly ``expected_size`` bytes."""
    return path.exists() and path.stat().st_size == expected_size


def _fetch_dataset_level_files(bucket, data_dir):
    """Download the :data:`DATASET_LEVEL_KEYS` at the bucket root.

    Every fetch calls this, so a file already complete locally (same
    size as on S3) is skipped, as in :func:`_filtered_download`;
    ``download`` followed by ``download_mapping`` fetches each once.
    """
    for obj in list_top_level_objects(bucket, ""):
        key = obj["Key"]
        if key not in DATASET_LEVEL_KEYS:
            continue
        local = Path(data_dir) / key
        if not _local_matches(local, obj["Size"]):
            download_key(bucket, key, local)


def _filtered_download(
    bucket, prefix, data_dir, filters,
    n_jobs=1, force_keys=(), exclude_sessions=(), top_level_only=False,
):
    """List ``prefix``, filter, skip already-complete files, download.

    Files whose local size already matches the S3 size are skipped
    entirely -- so a re-run of an interrupted download only fetches
    what's missing. Keys under ``HELD_OUT_SESSIONS`` are excluded
    (their bucket-policy deny rule would 403 every GET) unless they
    belong to a task in ``HELD_OUT_EXEMPT_TASKS``.

    Parameters
    ----------
    n_jobs : int
        Number of worker threads issuing AWS CLI copies in parallel.
        ``1`` (default) is fully sequential.
    force_keys : iterable of str
        S3 keys to keep regardless of the filter result. Used by
        the caller to pin essentials (e.g. the subject brain mask
        when filtering by ``ses``).
    exclude_sessions : iterable of str
        Session directories (``"ses-Foveal"``) whose keys are skipped.
    top_level_only : bool
        List only the objects directly under ``prefix``.
    """
    n_jobs = _clamp_n_jobs(n_jobs)
    force_keys = set(force_keys)
    result = {
        "prefix": prefix,
        "matched": [],
        "downloaded": [],
        "skipped": [],
        "access_denied": [],
    }

    if top_level_only:
        objects = list_top_level_objects(bucket, prefix)
    else:
        objects = list_prefix_objects(bucket, prefix)
    matching = []
    for o in objects:
        key = o["Key"]
        if _is_held_out(key):
            continue
        if any(f"/{s}/" in key for s in exclude_sessions):
            continue
        if key in force_keys:
            matching.append(o)
            continue
        if not _matches_filters(key, filters):
            continue
        matching.append(o)

    result["matched"] = [o["Key"] for o in matching]
    if not matching:
        return result

    todo = [
        o for o in matching
        if not _local_matches(
            Path(data_dir) / bidsify_local_key(o["Key"]),
            o["Size"],
        )
    ]
    todo_keys = {o["Key"] for o in todo}
    result["skipped"] = [
        o["Key"] for o in matching if o["Key"] not in todo_keys
    ]
    if not todo:
        return result

    def _fetch(obj):
        key = obj["Key"]
        local_path = Path(data_dir) / bidsify_local_key(key)
        try:
            download_key(bucket, key, local_path)
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr or ""
            if (
                "AccessDenied" in stderr
                or "Forbidden" in stderr
                or "(403)" in stderr
            ):
                warnings.warn(
                    f"Access denied for s3://{bucket}/{key}; "
                    "skipping (the bucket's deny rule blocks public "
                    "GET on this key).",
                    UserWarning,
                    stacklevel=2,
                )
                return "access_denied", key
            raise
        return "downloaded", key

    sizes = {o["Key"]: o["Size"] for o in todo}
    progress = DownloadProgress(prefix, len(todo), sum(sizes.values()))
    try:
        if n_jobs <= 1:
            for obj in todo:
                status, key = _fetch(obj)
                result[status].append(key)
                progress.advance(sizes[key])
        else:
            with ThreadPoolExecutor(max_workers=n_jobs) as pool:
                for status, key in pool.map(_fetch, todo):
                    result[status].append(key)
                    progress.advance(sizes[key])
    finally:
        progress.close()

    return result


def _format_active_filters(filters):
    """Return a compact human-readable filter summary."""
    active = [
        f"{name}={value!r}"
        for name, value in filters.items()
        if value is not None
    ]
    return ", ".join(active) if active else "none"


def fetch_laion_fmri(
    data_dir,
    subject,
    ses=None,
    task=None,
    space=None,
    desc=None,
    stat=None,
    suffix=None,
    extension=None,
    n_jobs=1,
    include_freesurfer=False,
    include_anatomical=False,
    include_raw=False,
    include_localizers=False,
    include_retinotopy=False,
):
    """Download fMRI / derivatives for one subject.

    Optionally narrowed by BIDS entities. Stimulus images are not
    fetched here — they're dataset-wide and gated through the
    access service (see
    :func:`laion_fmri.download.download_stimuli`).

    Parameters
    ----------
    data_dir : str
    subject : str
        BIDS subject ID (e.g. ``"sub-03"``).
    ses, task, space, desc, stat : str or list[str], optional
        BIDS-entity filters. Each may be a bare value (``"04"``) or
        the full BIDS token (``"ses-04"``). A file that lacks the
        entity is not excluded by a filter on it.
    suffix : str or list[str], optional
        BIDS suffix filter (e.g. ``"statmap"``, ``"events"``).
    extension : str or list[str], optional
        File extension filter (e.g. ``"nii.gz"``, ``"tsv"``).
    n_jobs : int
        Number of parallel AWS CLI copy workers. ``1`` (default) is
        sequential. Each worker is one subprocess that itself runs
        AWS-CLI's internal multipart concurrency, so doubling this
        number more than doubles the open S3 connections.
    include_freesurfer : bool
        If True, also pull the per-subject FreeSurfer recon under
        ``derivatives/freesurfer/{subject}/``. The recon files do
        not carry BIDS-entity tokens (``brain.mgz``, ``lh.white``,
        ``talairach.lta``, ...), so the BIDS filters above are NOT
        applied to the recon -- it's pulled as a whole.
    include_anatomical : bool
        If True, also pull the per-subject anatomical derivatives
        under ``derivatives/anatomical/{subject}/ses-PrismaAnat/
        anat/`` (T1w, T2w, brain mask and tissue masks at three
        resolutions). The
        anat files sit under ``ses-PrismaAnat`` and use
        ``T1w`` / ``T2w`` / ``mask`` suffixes -- both axes are
        orthogonal to typical functional filters, so the anat
        prefix is pulled with no BIDS filters applied (same
        convention as ``include_freesurfer``).
    include_raw : bool
        If True, also pull the raw BIDS tree under ``sub-XX/``
        (multi-echo BOLD, sbref, events, fieldmaps, raw MEGRE).
        The BIDS filters above (including ``run``, ``echo``,
        ``part``) apply.
    include_localizers : bool
        If True, also pull the subject's localizer derivatives under
        ``derivatives/localizers/{subject}/`` (contrast z-maps and
        per-run effect maps, a few hundred MB). Like the recon and anat
        trees, they are pulled in full; the BIDS filters do not apply.
    include_retinotopy : bool
        If True, also pull the subject's pRF parameter maps under
        ``derivatives/retinotopy/{subject}/``, in full, like the
        localizer tree.
    """
    bucket = LAION_FMRI_BUCKET
    filters = {
        "ses": ses,
        "task": task,
        "space": space,
        "desc": desc,
        "stat": stat,
        "suffix": suffix,
        "extension": extension,
    }
    raw_filters = dict(filters)

    # Root metadata files always go through, regardless of filters.
    _fetch_dataset_level_files(bucket, data_dir)

    # Brain mask is pinned when ``ses`` filters to specific
    # session(s) without "averages" -- it lives at the subject
    # level (no ses entity) so the strict ses filter would
    # otherwise drop it, and the loader needs it.
    glm_force = set()
    if _ses_filters_specific_sessions(ses):
        bm_local = r2mean_path(data_dir, subject)
        glm_force.add(
            bm_local.relative_to(data_dir).as_posix()
        )

    glm_result = _filtered_download(
        bucket, f"derivatives/glmsingle-tedana/{subject}/",
        data_dir, filters, n_jobs=n_jobs, force_keys=glm_force,
    )
    # ROI files are subject-level (no ses entity), so the strict
    # ses semantic would drop them all when the caller filters to a
    # specific session. Drop ses from the ROI-side filter dict so
    # ROIs come along for any ses= the user passes.
    roi_filters = {k: v for k, v in filters.items() if k != "ses"}
    roi_result = _filtered_download(
        bucket, f"derivatives/rois/{subject}/",
        data_dir, roi_filters, n_jobs=n_jobs,
    )

    if (
        not glm_result["matched"]
        and not roi_result["matched"]
        and not include_freesurfer
        and not include_anatomical
        and not include_raw
        and not include_localizers
        and not include_retinotopy
    ):
        prefixes = (
            f"s3://{bucket}/{glm_result['prefix']}",
            f"s3://{bucket}/{roi_result['prefix']}",
        )
        raise NoMatchingDataError(
            "No LAION-fMRI files matched "
            f"subject={subject!r} with filters "
            f"({_format_active_filters(filters)}) under "
            f"{prefixes[0]} or {prefixes[1]}. "
            "Check the subject ID and BIDS filters."
        )

    if include_freesurfer:
        # Recon files don't carry BIDS-entity tokens, so the
        # strict ses filter and the BIDS suffix/extension filters
        # would otherwise drop them. Pull the recon prefix with
        # no filters; the recon is a whole-tree atomic unit.
        _filtered_download(
            bucket, f"derivatives/freesurfer/{subject}/",
            data_dir, {}, n_jobs=n_jobs,
        )

    if include_anatomical:
        # Anatomical files use ``ses-PrismaAnat`` and suffixes
        # ``T1w`` / ``T2w`` / ``mask`` -- both axes are
        # orthogonal to typical functional filters
        # (``suffix=["statmap", "trials", ...]`` would otherwise
        # drop T1w / T2w outright). Pull the anat prefix with
        # no filters; downstream readers want the whole anat
        # tree.
        _filtered_download(
            bucket, f"derivatives/anatomical/{subject}/",
            data_dir, {}, n_jobs=n_jobs,
        )

    if include_raw:
        _download_raw_prefix(
            bucket, subject, data_dir, raw_filters, n_jobs=n_jobs,
        )

    if include_localizers:
        _filtered_download(
            bucket, f"derivatives/localizers/{subject}/",
            data_dir, {}, n_jobs=n_jobs,
        )

    if include_retinotopy:
        _filtered_download(
            bucket, f"derivatives/retinotopy/{subject}/",
            data_dir, {}, n_jobs=n_jobs,
        )

    return {
        "glmsingle": glm_result,
        "rois": roi_result,
    }


def fetch_retinotopy_stimuli(data_dir, n_jobs=1):
    """Download the retinotopy aperture libraries.

    Dataset-wide, under ``stimuli/retinotopy/``: one HDF5 of
    full-resolution apertures per defining task, each with a JSON
    sidecar. Public, unlike the LAION images.
    """
    return _filtered_download(
        LAION_FMRI_BUCKET, "stimuli/retinotopy/",
        data_dir, {}, n_jobs=n_jobs,
    )


#: Derivative trees of the precision-mapping dataset, by the
#: ``download_mapping`` flag that adds them (``None``: always).
MAPPING_TREES = (
    (None, "derivatives/retinotopy/"),
    (None, "derivatives/localizers/"),
    (None, "derivatives/rois/"),
    ("include_anatomical", "derivatives/anatomical/"),
    ("include_freesurfer", "derivatives/freesurfer/"),
    ("include_preproc", "derivatives/preproc-mapping/"),
)

#: Trees with per-session files; ``ses`` filters only these. The
#: others hold subject-level files (pRF maps, ROIs, anatomy) that carry
#: no ``ses`` entity, which a ``ses`` filter would drop.
_SESSION_TREES = ("derivatives/localizers/", "derivatives/preproc-mapping/")

#: Trees pulled whole, like in :func:`fetch_laion_fmri`: their files
#: carry no BIDS entities (FreeSurfer) or use their own sessions.
_WHOLE_TREES = ("derivatives/anatomical/", "derivatives/freesurfer/")


def fetch_mapping(
    data_dir,
    subject,
    ses=None,
    task=None,
    space=None,
    n_jobs=1,
    include_anatomical=False,
    include_freesurfer=False,
    include_preproc=False,
    include_raw=False,
):
    """Download one subject's precision-mapping files.

    Always the pRF maps, localizer maps and ROIs; the other trees on
    request. ``ses`` applies to the per-session trees (localizers,
    preprocessed data, raw) only; ``task`` and ``space`` apply wherever
    a file carries the entity.

    Parameters
    ----------
    data_dir : str
    subject : str
        BIDS subject ID (e.g. ``"sub-04"``).
    ses, task, space : str or list[str], optional
        BIDS-entity filters.
    n_jobs : int
        Number of parallel AWS CLI copy workers.
    include_anatomical, include_freesurfer : bool
        Also pull ``derivatives/anatomical/{subject}/`` or
        ``derivatives/freesurfer/{subject}/``, whole.
    include_preproc : bool
        Also pull ``derivatives/preproc-mapping/{subject}/``: the
        preprocessed BOLD, design matrices and frame tables.
    include_raw : bool
        Also pull the raw precision-mapping sessions
        (:data:`MAPPING_SESSIONS`) and ``ses-PrismaAnat``. LAION's
        numbered sessions are not included; use
        :func:`laion_fmri.download.download_raw` for those. ``sub-04``
        has no raw anatomy on the bucket. Its anatomy
        (``ses-ConnectomAnat``) is released as derivatives only
        (``include_anatomical``).
    """
    bucket = LAION_FMRI_BUCKET
    flags = {
        "include_anatomical": include_anatomical,
        "include_freesurfer": include_freesurfer,
        "include_preproc": include_preproc,
    }
    session_filters = {"ses": ses, "task": task, "space": space}
    subject_filters = {"task": task, "space": space}

    _fetch_dataset_level_files(bucket, data_dir)

    results = {}
    for flag, tree in MAPPING_TREES:
        if flag is not None and not flags[flag]:
            continue
        if tree in _WHOLE_TREES:
            filters = {}
        elif tree in _SESSION_TREES:
            filters = session_filters
        else:
            filters = subject_filters
        results[tree] = _filtered_download(
            bucket, f"{tree}{subject}/", data_dir, filters, n_jobs=n_jobs,
        )

    if include_raw:
        for session in MAPPING_SESSIONS + (SHARED_ANATOMY_SESSION,):
            results[f"{subject}/{session}/"] = _filtered_download(
                bucket, f"{subject}/{session}/", data_dir,
                session_filters, n_jobs=n_jobs,
            )

    if not any(r["matched"] for r in results.values()):
        raise NoMatchingDataError(
            "No precision-mapping files matched "
            f"subject={subject!r} with filters "
            f"({_format_active_filters(session_filters)}). "
            "Check the subject ID and BIDS filters."
        )
    return results


def fetch_mapping_dataset_files(
    data_dir, n_jobs=1, include_anatomical=False,
    include_freesurfer=False, include_preproc=False,
):
    """Download the dataset-wide files of the precision-mapping trees.

    The files directly under each derivative tree that
    :func:`fetch_mapping` pulls (``dataset_description.json``, lookup
    tables such as ``seg-winner_dseg.tsv``) and the aperture libraries
    under ``stimuli/retinotopy/``.
    """
    flags = {
        "include_anatomical": include_anatomical,
        "include_freesurfer": include_freesurfer,
        "include_preproc": include_preproc,
    }
    for flag, tree in MAPPING_TREES:
        if flag is not None and not flags[flag]:
            continue
        _filtered_download(
            LAION_FMRI_BUCKET, tree, data_dir, {},
            n_jobs=n_jobs, top_level_only=True,
        )
    fetch_retinotopy_stimuli(data_dir, n_jobs=n_jobs)


def _download_raw_prefix(
    bucket, subject, data_dir, filters, n_jobs=1,
):
    """Walk ``sub-{subject}/`` (raw BIDS root) with BIDS filters applied.

    Shared by :func:`fetch_laion_fmri` (additive) and
    :func:`fetch_laion_fmri_raw` (raw-only). Held-out session
    filtering and JSON sidecar handling reuse the generic
    ``_filtered_download`` machinery; both operate on BIDS-entity
    tokens so raw keys are handled by the same path. The
    precision-mapping sessions (:data:`MAPPING_SESSIONS`) are left
    out; :func:`fetch_mapping` fetches them.
    """
    return _filtered_download(
        bucket, f"{subject}/",
        data_dir, filters, n_jobs=n_jobs,
        exclude_sessions=MAPPING_SESSIONS,
    )


def fetch_laion_fmri_raw(
    data_dir,
    subject,
    ses=None,
    task=None,
    run=None,
    echo=None,
    part=None,
    suffix=None,
    extension=None,
    n_jobs=1,
):
    """Download raw BIDS files for one subject.

    Walks ``sub-{subject}/`` on the S3 bucket and applies the same
    BIDS-entity filter grammar as :func:`fetch_laion_fmri`.
    Held-out sessions (``HELD_OUT_SESSIONS``) are excluded
    automatically.

    Parameters
    ----------
    data_dir : str
    subject : str
        BIDS subject ID.
    ses, task, run, echo, part, suffix, extension : str or list[str], optional
        BIDS filters. ``run``/``echo``/``part`` are new here; the
        rest match :func:`fetch_laion_fmri`.
    n_jobs : int
        Parallel AWS CLI copy workers.

    Raises
    ------
    NoMatchingDataError
        If no raw keys match the filters.
    """
    bucket = LAION_FMRI_BUCKET
    filters = {
        "ses": ses,
        "task": task,
        "run": run,
        "echo": echo,
        "part": part,
        "suffix": suffix,
        "extension": extension,
    }

    _fetch_dataset_level_files(bucket, data_dir)

    raw_result = _download_raw_prefix(
        bucket, subject, data_dir, filters, n_jobs=n_jobs,
    )

    if not raw_result["matched"]:
        raise NoMatchingDataError(
            "No LAION-fMRI files matched "
            f"subject={subject!r} with filters "
            f"({_format_active_filters(filters)}) under "
            f"s3://{bucket}/{subject}/. "
            "Check the subject ID and BIDS filters."
        )

    return {"raw": raw_result}


def _ses_filters_specific_sessions(ses):
    """True if ``ses`` filters to specific sessions (not 'averages')."""
    if ses is None:
        return False
    values = [ses] if isinstance(ses, str) else list(ses)
    normalized = [_normalize("ses", v) for v in values]
    return any(v != "averages" for v in normalized)
