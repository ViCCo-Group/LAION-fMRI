from unittest.mock import call, patch

import pytest

from laion_fmri._constants import LICENSE_AGREEMENT_TEXT
from laion_fmri._errors import LicenseNotAcceptedError, SubjectNotFoundError
from laion_fmri.download import (
    _check_license_accepted,
    _write_license_marker,
    accept_license,
    accept_licenses,
    download,
)


@pytest.fixture
def configured_env(tmp_path, monkeypatch):
    """A configured data dir with the CC0 license pre-accepted."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    meta_dir = data_dir / ".laion_fmri"
    meta_dir.mkdir()
    (meta_dir / "license_accepted").touch()

    config_home = tmp_path / "config_home"
    config_home.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(data_dir))
    return data_dir


@pytest.fixture
def configured_env_no_license(tmp_path, monkeypatch):
    """A configured data dir WITHOUT license acceptance."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / ".laion_fmri").mkdir()

    config_home = tmp_path / "config_home"
    config_home.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(data_dir))
    return data_dir


# ── subject argument handling ──────────────────────────────────


def test_download_rejects_non_string_subject(configured_env):
    with pytest.raises(TypeError):
        download(subject=1)


def test_download_rejects_empty_subject(configured_env):
    with pytest.raises(SubjectNotFoundError):
        download(subject="")


# fetch_laion_fmri no longer receives ``include_stimuli`` — stimuli are
# downloaded via the access service in a separate call.
DEFAULT_FETCH_KWARGS = dict(
    ses=None, task=None, space=None, desc=None, stat=None,
    suffix=None, extension=None, include_stimuli=False, n_jobs=1,
)


def test_download_dispatches_to_laion_fmri_for_string_subject(configured_env):
    with patch("laion_fmri.download.fetch_laion_fmri") as mock_fetch:
        download(subject="sub-01")
    mock_fetch.assert_called_once_with(
        str(configured_env), subject="sub-01", **DEFAULT_FETCH_KWARGS,
    )


def test_download_dispatches_for_bare_value_subject(configured_env):
    with patch("laion_fmri.download.fetch_laion_fmri") as mock_fetch:
        download(subject="01")
    mock_fetch.assert_called_once_with(
        str(configured_env), subject="sub-01", **DEFAULT_FETCH_KWARGS,
    )


def test_download_dispatches_for_all_subjects(configured_env):
    with patch("laion_fmri.download.fetch_laion_fmri") as mock_fetch, patch(
        "laion_fmri.download.get_subjects", return_value=["sub-01", "sub-03"],
    ):
        download(subject="all")
    mock_fetch.assert_has_calls(
        [
            call(str(configured_env), subject=sub_id, **DEFAULT_FETCH_KWARGS)
            for sub_id in ("sub-01", "sub-03")
        ],
        any_order=False,
    )
    assert mock_fetch.call_count == 2


def test_download_passes_bids_entity_filters(configured_env):
    with patch("laion_fmri.download.fetch_laion_fmri") as mock_fetch:
        download(
            subject="sub-01",
            ses="04",
            task="images",
            desc="singletrial",
            stat="effect",
            extension="nii.gz",
        )
    kwargs = mock_fetch.call_args.kwargs
    assert kwargs["ses"] == "04"
    assert kwargs["task"] == "images"
    assert kwargs["desc"] == "singletrial"
    assert kwargs["stat"] == "effect"
    assert kwargs["extension"] == "nii.gz"


# ── include_stimuli routes through the access service ─────────


def test_download_include_stimuli_calls_access_service(configured_env):
    """``include_stimuli=True`` triggers ``download_stimuli`` after the
    fMRI fetch, and does NOT pass ``include_stimuli`` to
    ``fetch_laion_fmri`` (which now ignores the flag)."""
    with patch("laion_fmri.download.fetch_laion_fmri") as mock_fetch, patch(
        "laion_fmri.download.download_stimuli"
    ) as mock_stim:
        download(subject="sub-01", include_stimuli=True)

    mock_fetch.assert_called_once()
    assert mock_fetch.call_args.kwargs["include_stimuli"] is False
    mock_stim.assert_called_once_with(data_dir=str(configured_env))


def test_download_without_stimuli_does_not_call_access_service(configured_env):
    with patch("laion_fmri.download.fetch_laion_fmri"), patch(
        "laion_fmri.download.download_stimuli"
    ) as mock_stim:
        download(subject="sub-01")
    mock_stim.assert_not_called()


# ── CC0 license prompt ────────────────────────────────────────


def test_license_agreement_text_is_defined():
    assert isinstance(LICENSE_AGREEMENT_TEXT, str)
    assert len(LICENSE_AGREEMENT_TEXT) > 0


def test_check_license_accepted_false_when_no_marker(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / ".laion_fmri").mkdir()
    assert _check_license_accepted(str(data_dir)) is False


def test_check_license_accepted_true_when_marker_exists(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    meta_dir = data_dir / ".laion_fmri"
    meta_dir.mkdir()
    (meta_dir / "license_accepted").touch()
    assert _check_license_accepted(str(data_dir)) is True


def test_write_license_marker_creates_file(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / ".laion_fmri").mkdir()
    _write_license_marker(str(data_dir))
    assert (data_dir / ".laion_fmri" / "license_accepted").exists()


def test_write_license_marker_creates_parent_dirs(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_license_marker(str(data_dir))
    assert (data_dir / ".laion_fmri" / "license_accepted").exists()


def test_download_prompts_license_on_first_download(configured_env_no_license):
    with patch(
        "laion_fmri.download._prompt_license", return_value=True
    ) as mock_prompt, patch("laion_fmri.download.fetch_laion_fmri"):
        download(subject="sub-01")
    mock_prompt.assert_called_once()
    assert (
        configured_env_no_license / ".laion_fmri" / "license_accepted"
    ).exists()


def test_download_raises_when_license_declined(configured_env_no_license):
    with patch("laion_fmri.download._prompt_license", return_value=False):
        with pytest.raises(LicenseNotAcceptedError, match="license"):
            download(subject="sub-01")


def test_download_skips_license_prompt_when_already_accepted(configured_env):
    with patch(
        "laion_fmri.download._prompt_license"
    ) as mock_prompt, patch("laion_fmri.download.fetch_laion_fmri"):
        download(subject="sub-01")
    mock_prompt.assert_not_called()


# ── accept_license / accept_licenses helpers ──────────────────


def test_accept_license_prompts_when_needed(configured_env_no_license):
    with patch(
        "laion_fmri.download._prompt_license", return_value=True
    ) as mock_lic:
        accept_license()
    mock_lic.assert_called_once()
    assert (
        configured_env_no_license / ".laion_fmri" / "license_accepted"
    ).exists()


def test_accept_license_skips_when_already_accepted(configured_env):
    with patch("laion_fmri.download._prompt_license") as mock_lic:
        accept_license()
    mock_lic.assert_not_called()


def test_accept_license_raises_when_declined(configured_env_no_license):
    with patch("laion_fmri.download._prompt_license", return_value=False):
        with pytest.raises(LicenseNotAcceptedError, match="license"):
            accept_license()


def test_accept_licenses_deprecated_alias_still_works(
    configured_env_no_license,
):
    """``accept_licenses`` is a back-compat wrapper around
    ``accept_license``; it should still prompt for the CC0 license."""
    with patch(
        "laion_fmri.download._prompt_license", return_value=True
    ) as mock_lic:
        accept_licenses()
    mock_lic.assert_called_once()


def test_accept_licenses_with_include_stimuli_is_no_op_for_stimuli(
    configured_env_no_license, capsys,
):
    """The ``include_stimuli=True`` flag on the deprecated alias just
    prints a hint pointing the user at the access service. It does NOT
    write any stimulus marker (those are gone)."""
    with patch("laion_fmri.download._prompt_license", return_value=True):
        accept_licenses(include_stimuli=True)
    captured = capsys.readouterr()
    assert "access service" in captured.err
    assert not (
        configured_env_no_license / ".laion_fmri" / "stimuli_terms_accepted"
    ).exists()
