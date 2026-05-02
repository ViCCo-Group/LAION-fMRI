"""Integration tests that exercise the real LAION-fMRI S3 bucket.

These tests do NOT mock anything network-facing. They actually
invoke ``aws s3api`` / ``aws s3`` against ``s3://laion-fmri/`` and
verify the package's behavior end to end.

All tests in this module are marked with ``@pytest.mark.network``,
so they are deselected by default. Run them explicitly with::

    uv run pytest -m network -v

The bucket is public, so no AWS credentials are needed.
"""

import shutil
import tempfile
import warnings
from pathlib import Path

import pytest

from laion_fmri._s3_engine import (
    download_key,
    list_common_prefixes,
    list_prefix_keys,
    sync_prefix,
)
from laion_fmri._sources import LAION_FMRI_BUCKET
from laion_fmri.discovery import (
    describe,
    get_rois,
    get_subjects,
    inspect_bucket,
)

pytestmark = pytest.mark.network


# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def isolated_download_dir():
    """Provide a temp directory and wipe it after the test.

    Used by the download-flow integration test so that several
    hundred MB of fetched bucket data don't survive between test
    runs (pytest's ``tmp_path`` retains the last 3 by default).
    """
    path = Path(tempfile.mkdtemp(prefix="laion_fmri_test_"))
    yield path
    shutil.rmtree(path, ignore_errors=True)


# ── Pre-flight ──────────────────────────────────────────────────


def _quietly(func, *args, **kwargs):
    """Run ``func`` while ignoring our own UserWarnings."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return func(*args, **kwargs)


# ── Bucket reachability ─────────────────────────────────────────


def test_bucket_root_lists_derivatives():
    """The bucket root contains the ``derivatives/`` BIDS prefix."""
    top = list_common_prefixes(LAION_FMRI_BUCKET, "")
    assert "derivatives" in top, (
        f"Expected 'derivatives/' under s3://{LAION_FMRI_BUCKET}/ "
        f"but found: {top}"
    )


def test_inspect_bucket_real_run(capsys):
    """``inspect_bucket()`` prints the live bucket structure."""
    inspect_bucket()
    out = capsys.readouterr().out
    assert f"s3://{LAION_FMRI_BUCKET}" in out
    assert "Top-level prefixes" in out


# ── Discovery against real bucket ───────────────────────────────


def test_get_subjects_returns_list_from_real_bucket():
    """Subjects discovered from the real bucket match BIDS naming."""
    subjects = _quietly(get_subjects)
    assert isinstance(subjects, list)
    for sub_id in subjects:
        assert sub_id.startswith("sub-"), (
            f"Unexpected entry under derivatives/: {sub_id!r}"
        )


def test_describe_real_bucket(capsys):
    """``describe()`` shows the real bucket contents."""
    _quietly(describe)
    out = capsys.readouterr().out
    assert "LAION-fMRI Dataset" in out
    assert f"s3://{LAION_FMRI_BUCKET}" in out


def test_get_rois_for_first_subject():
    """ROI listing works for a real subject in the bucket."""
    subjects = _quietly(get_subjects)
    if not subjects:
        pytest.skip("No subjects in bucket yet -- nothing to test.")
    rois = _quietly(get_rois, subject=subjects[0])
    # Real bucket may or may not have ROIs at this dev stage --
    # we only require the listing to succeed and return a list.
    assert isinstance(rois, list)


# ── End-to-end download ─────────────────────────────────────────


def _list_subject_sessions(subject):
    """Sessions actually present for ``subject`` in the bucket."""
    names = list_common_prefixes(
        LAION_FMRI_BUCKET,
        f"derivatives/glmsingle-tedana/{subject}/",
    )
    return sorted(n for n in names if n.startswith("ses-"))


def test_download_one_session_and_load(
    isolated_download_dir, monkeypatch,
):
    """Targeted, low-bandwidth integration check.

    Downloads only the dataset-level metadata, the subject-level
    brain mask, and *one* session's ``func/`` directory -- then
    loads betas through the public ``Subject`` API to confirm the
    file format on S3 round-trips correctly through the package.

    Whole-subject downloads (30+ sessions, several GB) are too
    heavy for CI; this test stays under a few hundred MB. The
    ``isolated_download_dir`` fixture removes everything when the
    test finishes so nothing accumulates on disk.
    """
    subjects = _quietly(get_subjects)
    if not subjects:
        pytest.skip("No subjects in bucket yet -- nothing to test.")
    subject = subjects[0]

    sessions = _list_subject_sessions(subject)
    if not sessions:
        pytest.skip(
            f"No sessions found under "
            f"derivatives/glmsingle-tedana/{subject}/"
        )
    session = sessions[0]

    from laion_fmri._paths import brain_mask_path
    from laion_fmri.config import dataset_initialize
    from laion_fmri.subject import load_subject

    config_home = isolated_download_dir / "cfg"
    config_home.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    data_dir = isolated_download_dir / "data"
    data_dir.mkdir()
    dataset_initialize(str(data_dir))

    # Root-level metadata
    for key in (
        "dataset_description.json",
        "participants.tsv",
        "participants.json",
        "README",
    ):
        download_key(
            LAION_FMRI_BUCKET, key, data_dir / key,
        )

    # Subject-level brain mask -- skip the round-trip if the file
    # is not yet uploaded under the expected name.
    bm_local = brain_mask_path(data_dir, subject)
    bm_key = (
        f"derivatives/glmsingle-tedana/{subject}/"
        f"{bm_local.name}"
    )
    subject_keys = list_prefix_keys(
        LAION_FMRI_BUCKET,
        f"derivatives/glmsingle-tedana/{subject}/",
    )
    if bm_key not in subject_keys:
        pytest.skip(
            f"Brain mask not yet in bucket: s3://{LAION_FMRI_BUCKET}/{bm_key}"
        )
    download_key(LAION_FMRI_BUCKET, bm_key, bm_local)

    # One session's func dir only
    session_prefix = (
        f"derivatives/glmsingle-tedana/{subject}/{session}/"
    )
    sync_prefix(LAION_FMRI_BUCKET, session_prefix, data_dir)

    # Files actually landed
    assert (data_dir / "dataset_description.json").exists()
    assert bm_local.exists(), (
        f"Brain-mask file missing locally: {bm_local}"
    )
    func_dir = (
        data_dir / "derivatives" / "glmsingle-tedana"
        / subject / session / "func"
    )
    assert func_dir.is_dir(), (
        f"Expected session func dir at {func_dir}"
    )

    # Round-trip through the public API
    sub = load_subject(subject)
    assert session in sub.get_sessions()

    betas = sub.get_betas(session=session)
    assert betas.ndim == 2
    assert betas.shape[0] > 0
    assert betas.shape[1] > 0

    nc = sub.get_noise_ceiling(session=session)
    assert nc.shape == (betas.shape[1],)

    events = sub.get_trial_info(session=session)
    assert len(events) == betas.shape[0]


# ── CLI ─────────────────────────────────────────────────────────


def test_cli_info_against_real_bucket(monkeypatch, tmp_path, capsys):
    """``laion-fmri info`` end-to-end against the real bucket."""
    from laion_fmri._cli import main

    config_home = tmp_path / "cfg"
    config_home.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        main(["info"])

    out = capsys.readouterr().out
    assert "LAION-fMRI" in out
    assert f"s3://{LAION_FMRI_BUCKET}" in out
