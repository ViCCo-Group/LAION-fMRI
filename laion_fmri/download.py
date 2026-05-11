"""Download logic for the LAION-fMRI dataset."""

import sys

from laion_fmri._constants import (
    ACCESS_SERVICE_URL,
    LICENSE_AGREEMENT_TEXT,
    resolve_subject_id,
)
from laion_fmri._errors import LicenseNotAcceptedError
from laion_fmri._laion_fmri_fetch import fetch_laion_fmri
from laion_fmri._paths import (
    license_marker_path,
    stimuli_h5_path,
    stimuli_metadata_path,
)
from laion_fmri._stimulus_access import (
    AccessNotFoundError,
    AccessServiceError,
    TermsOutdatedError,
    current_terms_version,
    download_file,
    load_request_id,
    refresh_urls,
    save_request_id,
    submit_access_request,
)
from laion_fmri.config import get_data_dir
from laion_fmri.discovery import get_subjects


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
        f"I accept the LAION-fMRI Terms of Use (v{terms_version}). "
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
    """Download the gated stimulus archive (HDF5 + metadata CSV).

    The stimulus archive is a single HDF5 covering all subjects — it is
    dataset-wide, not per-subject — so this function takes no subject
    argument. If no cached ``request_id`` is present, walks the user
    through the Data Use Agreement form interactively. Otherwise
    re-mints URLs via ``/api/v1/refresh`` and downloads silently.

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

    payload = _resolve_stimulus_access(server_url=server_url)
    expected = {
        "task-images_stimuli.h5": stimuli_h5_path(data_dir),
        "task-images_metadata.csv": stimuli_metadata_path(data_dir),
    }
    by_name = {f["name"]: f for f in payload["files"]}
    missing = set(expected) - set(by_name)
    if missing:
        raise AccessServiceError(
            f"Server didn't return expected files: {sorted(missing)}."
        )
    print(
        f"\n[laion-fmri] Downloading stimuli "
        f"(links valid until {payload['expires_at']}):"
    )
    for name, dest in expected.items():
        info = by_name[name]
        download_file(
            info["url"], dest,
            expected_size=info["size"],
            expected_sha256=info["sha256"],
        )
    return expected


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
    n_jobs=1,
):
    """Download fMRI dataset files for a subject, narrowed by BIDS entities.

    The download is **idempotent**: a file whose local size already
    matches the S3 size is skipped, so re-running after an interrupted
    transfer only fetches what's missing.

    The stimulus archive is dataset-wide (one HDF5 for all subjects), so
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
        pull the dataset-wide stimulus archive. Useful when you want
        both in a single call. Use :func:`download_stimuli` directly
        if you only need the stimuli.
    n_jobs : int
        Number of parallel download workers for fMRI data
        (``aws s3 cp`` subprocesses). ``1`` (default) is sequential.
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
