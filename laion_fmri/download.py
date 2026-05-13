"""Download logic for the LAION-fMRI dataset."""

import sys
from concurrent.futures import ThreadPoolExecutor

from laion_fmri._constants import (
    ACCESS_SERVICE_URL,
    LICENSE_AGREEMENT_TEXT,
    resolve_subject_id,
)
from laion_fmri._errors import LicenseNotAcceptedError, NoMatchingDataError
from laion_fmri._laion_fmri_fetch import _clamp_n_jobs, fetch_laion_fmri
from laion_fmri._paths import (
    captions_path,
    embeddings_h5_path,
    license_marker_path,
    segmentations_h5_path,
    segmentations_metadata_path,
    stimuli_h5_path,
    stimuli_metadata_path,
)
from laion_fmri._s3_engine import download_key, list_prefix_objects
from laion_fmri._sources import LAION_FMRI_BUCKET
from laion_fmri._stimulus_access import (
    AccessNotFoundError,
    AccessServiceError,
    TermsOutdatedError,
    current_terms_version,
    download_file,
    fetch_manifest,
    load_request_id,
    refresh_urls,
    save_request_id,
    submit_access_request,
)
from laion_fmri.config import get_data_dir
from laion_fmri.discovery import get_subjects
from laion_fmri.embeddings import AVAILABLE_MODELS


def _check_license_accepted(data_dir):
    """Check whether the CC0 dataset license has been accepted locally."""
    return license_marker_path(data_dir).exists()


def _write_license_marker(data_dir):
    """Write the CC0 dataset-license acceptance marker."""
    marker = license_marker_path(data_dir)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()


def _prompt_license():
    """Show the CC0 dataset license and prompt for acceptance."""
    sys.stdout.write(LICENSE_AGREEMENT_TEXT)
    sys.stdout.flush()
    response = input().strip()
    return response == "I AGREE"


def accept_license():
    """Walk through the CC0 dataset-license acceptance without downloading.

    Stimulus terms are no longer accepted locally — they're handled by the
    access service. Use ``request_stimulus_access()`` (or
    ``laion-fmri request-access``) when you need stimulus images.
    """
    data_dir = get_data_dir()
    if _check_license_accepted(data_dir):
        return
    if not _prompt_license():
        raise LicenseNotAcceptedError(
            "Dataset license must be accepted before downloading."
        )
    _write_license_marker(data_dir)


# Backwards-compat alias — old callers that imported the previous
# ``accept_licenses(include_stimuli=...)`` keep working with the
# ``include_stimuli`` flag now ignored (stimuli are gated via the access
# service rather than a local marker).
def accept_licenses(include_stimuli=False):
    """Deprecated. Use :func:`accept_license` or
    :func:`request_stimulus_access` instead.
    """
    accept_license()
    if include_stimuli:
        sys.stderr.write(
            "[laion-fmri] Note: stimulus access is now obtained via the "
            "access service. Run `laion-fmri request-access` (or pass "
            "include_stimuli=True to download() for an interactive prompt).\n"
        )


# ── Stimulus access via the access service ──────────────────────


def _prompt_stimulus_form(server_url=ACCESS_SERVICE_URL):
    """Interactive CLI form for /api/v1/access/request."""
    terms_version = current_terms_version(server_url)

    print("=" * 64)
    print("LAION-fMRI stimulus access request")
    print("=" * 64)
    print(
        "\nThe stimulus images are gated by a Data Use Agreement.\n"
        f"Read the full terms:  {server_url}/terms\n"
        f"Privacy notice:       {server_url}/privacy\n"
        f"Takedown contact:     {server_url}/takedown\n"
    )

    name = input("Full name: ").strip()
    email = input("Institutional email: ").strip()
    institution = input("Institution / affiliation: ").strip()
    pi = input("PI / supervisor (optional, Enter to skip): ").strip()
    print(
        "\nResearch purpose — briefly describe how you plan to use the\n"
        "stimulus images. Do NOT include patient names or special-category\n"
        "data about third parties. (minimum 20 characters)"
    )
    purpose = input("> ").strip()
    print()
    answer = input(
        f"I have read and accept the LAION-fMRI Terms of Use "
        f"(v{terms_version}) and I have read the Privacy notice. "
        "Type 'yes' to submit: "
    ).strip().lower()
    if answer != "yes":
        raise AccessServiceError("Access request cancelled by user.")

    return {
        "name": name,
        "email": email,
        "institution": institution,
        "pi_or_supervisor": pi or None,
        "research_purpose": purpose,
        "accepted_terms": True,
        "acknowledged_privacy": True,
        "terms_version": terms_version,
        "source": "cli",
    }, email


def request_stimulus_access(server_url=ACCESS_SERVICE_URL):
    """Walk the user through the form and persist the returned request_id.

    Returns the response dict (request_id, expires_at, files).
    """
    payload, email = _prompt_stimulus_form(server_url)
    response = submit_access_request(payload, server_url=server_url)
    saved_path = save_request_id(
        response["request_id"], email=email, server_url=server_url,
    )
    print(
        f"\n✓ Access granted. request_id saved to {saved_path}\n"
        f"  You can now run `laion-fmri download --include-stimuli`.\n"
    )
    return response


def _resolve_stimulus_access(server_url=ACCESS_SERVICE_URL):
    """Return a fresh download payload, prompting for the form if needed.

    Side-effect: if no cached request_id is present, walks the user
    through the form and persists the new id.
    """
    request_id = load_request_id()
    if request_id is None:
        response = request_stimulus_access(server_url=server_url)
        # request_stimulus_access already created the row + URLs.
        return response

    try:
        return refresh_urls(request_id, server_url=server_url)
    except AccessNotFoundError:
        sys.stderr.write(
            "[laion-fmri] Your cached request_id is unknown to the server "
            "(maybe revoked, anonymised after inactivity, or you switched "
            "servers). Running the access form now.\n"
        )
        return request_stimulus_access(server_url=server_url)


def download_stimuli(data_dir=None, server_url=ACCESS_SERVICE_URL):
    """Download the stimuli (HDF5 + metadata CSV).

    The stimuli is a single HDF5 covering all subjects — it is
    dataset-wide, not per-subject — so this function takes no subject
    argument.

    Network behaviour:

    * Always starts with the **public** manifest endpoint to find out
      what the current files are and their sha256s. No authentication
      involved.
    * If the local files already match the manifest, the function
      returns immediately. **No access-service call, no auth state
      needed.** This is why a cluster job can just rsync the data dir
      from your laptop and call ``download_stimuli()`` without ever
      copying ``auth.json`` — the package sees the files are correct
      and short-circuits.
    * Only when at least one file is missing or has the wrong sha256
      does the function reach for the access service: if no cached
      ``request_id`` is present, it walks the user through the Data
      Use Agreement form; otherwise it re-mints URLs via
      ``/api/v1/refresh`` and downloads what's missing.

    Parameters
    ----------
    data_dir : str or Path, optional
        Override the configured data directory.
    server_url : str
        Override the access service URL (default: production).

    Returns
    -------
    dict
        Mapping of file name to local :class:`pathlib.Path` for the
        downloaded files.

    Raises
    ------
    AccessServiceError
        If the access service rejects the request or a download fails.
    TermsOutdatedError
        If the cached request_id needs to re-accept an updated ToU.
    """
    if data_dir is None:
        data_dir = get_data_dir()

    manifest = fetch_manifest(server_url=server_url)
    file_specs = {f["name"]: f for f in manifest["files"]}
    expected = {
        "task-images_stimuli.h5": stimuli_h5_path(data_dir),
        "task-images_metadata.csv": stimuli_metadata_path(data_dir),
    }

    # What's missing or stale?
    needs_download = []
    for name, dest in expected.items():
        spec = file_specs.get(name)
        if spec is None:
            raise AccessServiceError(
                f"Public manifest is missing {name!r}; aborting."
            )
        if dest.exists() and dest.stat().st_size == spec["size"]:
            from laion_fmri._stimulus_access import _sha256_of
            if _sha256_of(dest) == spec["sha256"]:
                continue
        needs_download.append((name, dest, spec))

    if not needs_download:
        print("[laion-fmri] stimuli already up to date.")
        return expected

    # Something to fetch → now we need auth + signed URLs.
    payload = _resolve_stimulus_access(server_url=server_url)
    by_name = {f["name"]: f for f in payload["files"]}
    print(
        f"\n[laion-fmri] Downloading {len(needs_download)} stimulus file(s) "
        f"(links valid until {payload['expires_at']}):"
    )
    for name, dest, spec in needs_download:
        info = by_name.get(name)
        if info is None:
            raise AccessServiceError(
                f"Server didn't return expected file {name!r}."
            )
        download_file(
            info["url"], dest,
            expected_size=info["size"],
            expected_sha256=info["sha256"],
        )
    return expected


# ── Stimulus embeddings (public S3, CC0) ────────────────────────


def _resolve_embedding_models(models):
    """Normalise the ``models`` argument to a list of valid labels."""
    if isinstance(models, str):
        selected = (
            list(AVAILABLE_MODELS) if models == "all" else [models]
        )
    else:
        selected = list(models)
    unknown = [m for m in selected if m not in AVAILABLE_MODELS]
    if unknown:
        raise ValueError(
            f"Unknown embedding model(s) {unknown}. "
            f"Available: {list(AVAILABLE_MODELS)}."
        )
    return selected


def download_embeddings(models="all", data_dir=None, n_jobs=1):
    """Download stimulus embedding HDF5 files from the public S3 bucket.

    The embeddings are dataset-wide derivatives (one set of files for
    all subjects), shipped under the same CC0 license as the rest of
    the fMRI data — no Data Use Agreement, no signed URLs.

    The download is **idempotent**: files whose local size matches the
    S3 size are skipped, so re-running an interrupted transfer only
    fetches what's missing.

    Parameters
    ----------
    models : str or list[str]
        One of:

        * ``"all"`` (default) — download every model in
          :data:`laion_fmri.embeddings.AVAILABLE_MODELS`.
        * a single label, e.g. ``"CLIP"``.
        * a list of labels, e.g. ``["CLIP", "DINOv2"]``.
    data_dir : str or Path, optional
        Override the configured data directory.
    n_jobs : int
        Number of parallel AWS CLI copy workers. ``1`` (default) is
        sequential.

    Returns
    -------
    dict[str, pathlib.Path]
        Mapping of model label to local file path for each requested
        model.
    """
    if data_dir is None:
        data_dir = get_data_dir()

    selected = _resolve_embedding_models(models)
    accept_license()
    n_jobs = _clamp_n_jobs(n_jobs)

    bucket_objects = list_prefix_objects(LAION_FMRI_BUCKET, "stimuli/")
    sizes = {o["Key"]: o["Size"] for o in bucket_objects}

    todo = []
    paths = {}
    for m in selected:
        key = f"stimuli/task-images_desc-{m}_embeddings.h5"
        local = embeddings_h5_path(data_dir, m)
        paths[m] = local
        expected_size = sizes.get(key)
        if expected_size is None:
            raise RuntimeError(
                f"Embedding file {key!r} not found on "
                f"s3://{LAION_FMRI_BUCKET}/. Has it been uploaded yet?"
            )
        if local.exists() and local.stat().st_size == expected_size:
            continue
        todo.append((key, local))

    if not todo:
        print("[laion-fmri] embeddings already up to date.")
        return paths

    print(f"[laion-fmri] Downloading {len(todo)} embedding file(s):")

    def _fetch(item):
        key, local = item
        download_key(LAION_FMRI_BUCKET, key, local)

    if n_jobs <= 1:
        for it in todo:
            _fetch(it)
    else:
        with ThreadPoolExecutor(max_workers=n_jobs) as pool:
            list(pool.map(_fetch, todo))

    return paths


def download_segmentations(data_dir=None):
    """Download the per-stimulus segmentation masks from the public S3 bucket.

    Pulls two sibling files into ``<data_dir>/stimuli/``:

    * ``task-images_desc-segmentations.h5`` — stacked ``(N, H, W)`` uint8 masks
    * ``task-images_desc-segmentations_metadata.csv`` — one row per mask

    These are dataset-wide derivatives (one set of files for all
    subjects), shipped under the same CC0 license as the rest of the
    fMRI data — no Data Use Agreement, no signed URLs.

    The download is **idempotent**: files whose local size matches the
    S3 size are skipped, so re-running an interrupted transfer only
    fetches what's missing.

    Parameters
    ----------
    data_dir : str or Path, optional
        Override the configured data directory.

    Returns
    -------
    dict[str, pathlib.Path]
        Mapping of ``{"h5": ..., "metadata": ...}`` to local file paths.
    """
    if data_dir is None:
        data_dir = get_data_dir()

    accept_license()

    bucket_objects = list_prefix_objects(LAION_FMRI_BUCKET, "stimuli/")
    sizes = {o["Key"]: o["Size"] for o in bucket_objects}

    targets = {
        "h5": (
            "stimuli/task-images_desc-segmentations.h5",
            segmentations_h5_path(data_dir),
        ),
        "metadata": (
            "stimuli/task-images_desc-segmentations_metadata.csv",
            segmentations_metadata_path(data_dir),
        ),
    }
    paths = {label: local for label, (_, local) in targets.items()}

    todo = []
    for label, (key, local) in targets.items():
        expected_size = sizes.get(key)
        if expected_size is None:
            raise RuntimeError(
                f"Segmentation file {key!r} not found on "
                f"s3://{LAION_FMRI_BUCKET}/. Has it been uploaded yet?"
            )
        if local.exists() and local.stat().st_size == expected_size:
            continue
        todo.append((key, local))

    if not todo:
        print("[laion-fmri] segmentations already up to date.")
        return paths

    print(f"[laion-fmri] Downloading {len(todo)} segmentation file(s):")
    for key, local in todo:
        download_key(LAION_FMRI_BUCKET, key, local)

    return paths


def download_captions(data_dir=None):
    """Download the per-stimulus captions CSV from the public S3 bucket.

    Pulls ``task-images_desc-captions.csv`` into ``<data_dir>/stimuli/``.
    The file is a dataset-wide stimulus metadata derivative: shared
    images have five human captions, shared non-OOD images have one AI
    caption, and unique images have three human captions and no AI
    caption.

    The download is **idempotent**: a file whose local size matches the
    S3 size is skipped, so re-running an interrupted transfer only
    fetches what's missing.

    Parameters
    ----------
    data_dir : str or Path, optional
        Override the configured data directory.

    Returns
    -------
    pathlib.Path
        Local path to ``task-images_desc-captions.csv``.
    """
    if data_dir is None:
        data_dir = get_data_dir()

    accept_license()

    key = "stimuli/task-images_desc-captions.csv"
    local = captions_path(data_dir)
    bucket_objects = list_prefix_objects(LAION_FMRI_BUCKET, "stimuli/")
    sizes = {o["Key"]: o["Size"] for o in bucket_objects}
    expected_size = sizes.get(key)
    if expected_size is None:
        raise RuntimeError(
            f"Captions file {key!r} not found on "
            f"s3://{LAION_FMRI_BUCKET}/. Has it been uploaded yet?"
        )
    if local.exists() and local.stat().st_size == expected_size:
        print("[laion-fmri] captions already up to date.")
        return local

    print("[laion-fmri] Downloading captions file:")
    download_key(LAION_FMRI_BUCKET, key, local)
    return local


# ── Public entry point ──────────────────────────────────────────


def download(
    subject,
    ses=None,
    task=None,
    space=None,
    desc=None,
    stat=None,
    suffix=None,
    extension=None,
    include_stimuli=False,
    include_embeddings=False,
    n_jobs=1,
):
    """Download fMRI dataset files for a subject, narrowed by BIDS entities.

    The download is **idempotent**: a file whose local size already
    matches the S3 size is skipped, so re-running after an interrupted
    transfer only fetches what's missing.

    The stimuli is dataset-wide (one HDF5 for all subjects), so
    it is not subject-keyed. For stimulus-only downloads use the
    standalone :func:`download_stimuli` function. The
    ``include_stimuli=True`` flag here is a convenience that calls
    :func:`download_stimuli` after the fMRI fetch completes.

    Parameters
    ----------
    subject : str or "all"
        Subject identifier (BIDS ID, e.g. ``"sub-01"`` / ``"01"``,
        or ``"all"`` to iterate every subject).
    ses, task, space, desc, stat : str or list[str], optional
        BIDS-entity filters. Each accepts a bare value
        (``ses="04"``) or the full BIDS token (``ses="ses-04"``).
        A list narrows to multiple values. Files that don't carry
        an entity are not excluded by a filter on it (so
        subject-level summaries survive a ``ses=`` filter).
    suffix : str or list[str], optional
        BIDS suffix filter (``"statmap"``, ``"events"``, ...).
    extension : str or list[str], optional
        File extension filter (``"nii.gz"``, ``"tsv"``, ...).
    include_stimuli : bool
        After the fMRI fetch, also call :func:`download_stimuli` to
        pull the dataset-wide stimuli. Useful when you want
        both in a single call. Use :func:`download_stimuli` directly
        if you only need the stimuli.
    include_embeddings : bool or str or list[str]
        After the fMRI fetch, also call :func:`download_embeddings`.
        Pass ``True`` for all four models, or a model label / list of
        labels to narrow. ``False`` (default) skips the embeddings.
    n_jobs : int
        Number of parallel download workers for fMRI data
        (AWS CLI copy subprocesses). ``1`` (default) is sequential.
        Does not affect stimulus downloads.

    Raises
    ------
    SubjectNotFoundError
        If the subject identifier is invalid.
    LicenseNotAcceptedError
        If the CC0 dataset license is declined.
    AccessServiceError
        If ``include_stimuli=True`` and the stimulus access service
        rejects the request or a download fails.
    TermsOutdatedError
        If ``include_stimuli=True`` and the server's current Terms of
        Use version differs from the version on the cached
        ``request_id``.
    """
    data_dir = get_data_dir()

    if subject != "all":
        resolve_subject_id(subject)

    accept_license()

    if subject == "all":
        subjects = get_subjects()
        if not subjects:
            raise NoMatchingDataError(
                "No LAION-fMRI subjects were found in the public S3 "
                "bucket. Check network access and the bucket layout."
            )
    else:
        subjects = [resolve_subject_id(subject)]

    for sub_id in subjects:
        fetch_laion_fmri(
            data_dir,
            subject=sub_id,
            ses=ses,
            task=task,
            space=space,
            desc=desc,
            stat=stat,
            suffix=suffix,
            extension=extension,
            n_jobs=n_jobs,
        )

    if include_stimuli:
        download_stimuli(data_dir=data_dir)

    if include_embeddings:
        models = (
            "all" if include_embeddings is True else include_embeddings
        )
        download_embeddings(
            models=models, data_dir=data_dir, n_jobs=n_jobs,
        )
