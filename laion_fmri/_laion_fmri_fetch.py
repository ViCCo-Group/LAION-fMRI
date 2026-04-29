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
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from laion_fmri._paths import brain_mask_path
from laion_fmri._s3_engine import (
    download_key,
    has_aws_credentials,
    list_prefix_objects,
)
from laion_fmri._sources import LAION_FMRI_BUCKET

DATASET_LEVEL_KEYS = (
    "dataset_description.json",
    "participants.tsv",
    "participants.json",
    "README",
)

#: BIDS entities exposed as filter kwargs (in BIDS short form).
BIDS_ENTITIES = ("ses", "task", "space", "desc", "stat")


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


def _filtered_download(
    bucket, prefix, data_dir, filters,
    n_jobs=1, force_keys=(),
):
    """List ``prefix``, filter, skip already-complete files, download.

    Files whose local size already matches the S3 size are skipped
    entirely -- so a re-run of an interrupted download only fetches
    what's missing.

    Parameters
    ----------
    n_jobs : int
        Number of worker threads issuing ``aws s3 cp`` in parallel.
        ``1`` (default) is fully sequential.
    force_keys : iterable of str
        S3 keys to keep regardless of the filter result. Used by
        the caller to pin essentials (e.g. the subject brain mask
        when filtering by ``ses``).
    """
    n_jobs = _clamp_n_jobs(n_jobs)
    force_keys = set(force_keys)

    objects = list_prefix_objects(bucket, prefix)
    matching = [
        o for o in objects
        if o["Key"] in force_keys
        or _matches_filters(o["Key"], filters)
    ]

    if not matching:
        local_path = Path(data_dir) / prefix
        has_local = (
            local_path.is_dir() and any(local_path.rglob("*"))
        )
        if not has_local:
            hint = (
                " No AWS credentials were detected -- "
                "if the bucket is still private, call "
                "laion_fmri.config.set_aws_credentials(...) first."
                if not has_aws_credentials()
                else ""
            )
            warnings.warn(
                f"No objects matching the requested filters under "
                f"s3://{bucket}/{prefix}.{hint}",
                UserWarning,
                stacklevel=3,
            )
        return

    todo = [
        o for o in matching
        if not _local_matches(
            Path(data_dir) / o["Key"], o["Size"],
        )
    ]
    if not todo:
        return

    def _fetch(obj):
        download_key(bucket, obj["Key"], Path(data_dir) / obj["Key"])

    if n_jobs <= 1:
        for obj in todo:
            _fetch(obj)
    else:
        with ThreadPoolExecutor(max_workers=n_jobs) as pool:
            list(pool.map(_fetch, todo))


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
    include_stimuli=False,
    n_jobs=1,
):
    """Download data for one subject, optionally narrowed by entities.

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
    include_stimuli : bool
        Mirror the ``stimuli/`` prefix as well.
    n_jobs : int
        Number of parallel ``aws s3 cp`` workers. ``1`` (default) is
        sequential. Each worker is one subprocess that itself runs
        AWS-CLI's internal multipart concurrency, so doubling this
        number more than doubles the open S3 connections.
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

    # Root metadata files always go through, regardless of filters.
    for key in DATASET_LEVEL_KEYS:
        download_key(bucket, key, f"{data_dir}/{key}")

    # Brain mask is pinned when ``ses`` filters to specific
    # session(s) without "averages" -- it lives at the subject
    # level (no ses entity) so the strict ses filter would
    # otherwise drop it, and the loader needs it.
    glm_force = set()
    if _ses_filters_specific_sessions(ses):
        bm_local = brain_mask_path(data_dir, subject)
        glm_force.add(
            bm_local.relative_to(data_dir).as_posix()
        )

    _filtered_download(
        bucket, f"derivatives/glmsingle-tedana/{subject}/",
        data_dir, filters, n_jobs=n_jobs, force_keys=glm_force,
    )
    _filtered_download(
        bucket, f"derivatives/atlases/{subject}/",
        data_dir, filters, n_jobs=n_jobs,
    )

    if include_stimuli:
        _filtered_download(
            bucket, "stimuli/", data_dir, filters, n_jobs=n_jobs,
        )


def _ses_filters_specific_sessions(ses):
    """True if ``ses`` filters to specific sessions (not 'averages')."""
    if ses is None:
        return False
    values = [ses] if isinstance(ses, str) else list(ses)
    normalized = [_normalize("ses", v) for v in values]
    return any(v != "averages" for v in normalized)
