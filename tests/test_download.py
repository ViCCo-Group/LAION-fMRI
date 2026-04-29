from unittest.mock import patch, call

import pytest

from laion_fmri._constants import (
    LICENSE_AGREEMENT_TEXT,
    TERMS_OF_USE_TEXT,
)
from laion_fmri._errors import LicenseNotAcceptedError, SubjectNotFoundError
from laion_fmri.download import (
    _check_license_accepted,
    _check_tou_accepted,
    _write_license_marker,
    _write_tou_marker,
    accept_licenses,
    download,
)


@pytest.fixture
def configured_env(tmp_path, monkeypatch):
    """Set up a configured data dir for download tests.

    Pre-accepts the dataset license so tests not focused on
    the license flow are not blocked by the license prompt.
    """
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
    """Set up a configured data dir WITHOUT license acceptance."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / ".laion_fmri").mkdir()

    config_home = tmp_path / "config_home"
    config_home.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(data_dir))
    return data_dir


def test_download_rejects_non_string_subject(configured_env):
    """Integer indices are no longer accepted; BIDS-form strings only."""
    with pytest.raises(TypeError):
        download(subject=1)


def test_download_rejects_empty_subject(configured_env):
    with pytest.raises(SubjectNotFoundError):
        download(subject="")


DEFAULT_FETCH_KWARGS = dict(
    ses=None, task=None, space=None, desc=None, stat=None,
    suffix=None, extension=None, include_stimuli=False, n_jobs=1,
)


def test_download_dispatches_to_laion_fmri_for_string_subject(
    configured_env,
):
    with patch(
        "laion_fmri.download.fetch_laion_fmri"
    ) as mock_fetch:
        download(subject="sub-01")

    mock_fetch.assert_called_once_with(
        str(configured_env), subject="sub-01",
        **DEFAULT_FETCH_KWARGS,
    )


def test_download_dispatches_for_bare_value_subject(configured_env):
    """``subject="01"`` is normalized to ``"sub-01"``."""
    with patch(
        "laion_fmri.download.fetch_laion_fmri"
    ) as mock_fetch:
        download(subject="01")

    mock_fetch.assert_called_once_with(
        str(configured_env), subject="sub-01",
        **DEFAULT_FETCH_KWARGS,
    )


def test_download_dispatches_to_laion_fmri_for_all_subjects(
    configured_env,
):
    """``subject="all"`` expands via the S3-backed get_subjects."""
    with patch(
        "laion_fmri.download.fetch_laion_fmri"
    ) as mock_fetch, patch(
        "laion_fmri.download.get_subjects",
        return_value=["sub-01", "sub-03"],
    ):
        download(subject="all")

    expected_calls = [
        call(
            str(configured_env), subject=sub_id,
            **DEFAULT_FETCH_KWARGS,
        )
        for sub_id in ("sub-01", "sub-03")
    ]
    mock_fetch.assert_has_calls(expected_calls, any_order=False)
    assert mock_fetch.call_count == 2


def test_download_passes_include_stimuli_flag(configured_env):
    # Pre-accept ToU so prompt does not block
    (configured_env / ".laion_fmri" / "stimuli_terms_accepted").touch()
    with patch(
        "laion_fmri.download.fetch_laion_fmri"
    ) as mock_fetch:
        download(subject="sub-01", include_stimuli=True)

    expected = {**DEFAULT_FETCH_KWARGS, "include_stimuli": True}
    mock_fetch.assert_called_once_with(
        str(configured_env), subject="sub-01", **expected,
    )


def test_download_passes_bids_entity_filters(configured_env):
    """``ses``, ``desc``, etc. flow through to fetch_laion_fmri."""
    with patch(
        "laion_fmri.download.fetch_laion_fmri"
    ) as mock_fetch:
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


def test_check_tou_accepted_false_when_no_marker(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / ".laion_fmri").mkdir()
    assert _check_tou_accepted(str(data_dir)) is False


def test_check_tou_accepted_true_when_marker_exists(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    meta_dir = data_dir / ".laion_fmri"
    meta_dir.mkdir()
    (meta_dir / "stimuli_terms_accepted").touch()
    assert _check_tou_accepted(str(data_dir)) is True


def test_write_tou_marker_creates_file(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / ".laion_fmri").mkdir()
    _write_tou_marker(str(data_dir))
    assert (
        data_dir / ".laion_fmri" / "stimuli_terms_accepted"
    ).exists()


def test_tou_prompt_text_is_defined():
    assert isinstance(TERMS_OF_USE_TEXT, str)
    assert len(TERMS_OF_USE_TEXT) > 0


# --- License agreement tests ---


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


def test_download_prompts_license_on_first_download(
    configured_env_no_license,
):
    """First download without license marker prompts the user."""
    with patch(
        "laion_fmri.download._prompt_license", return_value=True
    ) as mock_prompt, patch(
        "laion_fmri.download.fetch_laion_fmri"
    ):
        download(subject="sub-01")

    mock_prompt.assert_called_once()
    assert (
        configured_env_no_license / ".laion_fmri" / "license_accepted"
    ).exists()


def test_download_raises_when_license_declined(
    configured_env_no_license,
):
    """Declining the license raises LicenseNotAcceptedError."""
    with patch(
        "laion_fmri.download._prompt_license", return_value=False
    ):
        with pytest.raises(
            LicenseNotAcceptedError,
            match="license must be accepted",
        ):
            download(subject="sub-01")


def test_download_skips_license_prompt_when_already_accepted(
    configured_env,
):
    """Second download with marker file skips the license prompt."""
    with patch(
        "laion_fmri.download._prompt_license"
    ) as mock_prompt, patch(
        "laion_fmri.download.fetch_laion_fmri"
    ):
        download(subject="sub-01")

    mock_prompt.assert_not_called()


def test_download_license_check_happens_before_tou(
    configured_env_no_license,
):
    """License check runs before stimulus ToU check."""
    with patch(
        "laion_fmri.download._prompt_license", return_value=False
    ):
        with pytest.raises(LicenseNotAcceptedError):
            download(subject="sub-01", include_stimuli=True)
    # ToU marker should NOT exist since we never got past license
    assert not (
        configured_env_no_license
        / ".laion_fmri"
        / "stimuli_terms_accepted"
    ).exists()


# ── accept_licenses (standalone helper) ─────────────────────────


def test_accept_licenses_prompts_dataset_only_by_default(
    configured_env_no_license,
):
    """Without ``include_stimuli`` only the dataset license is asked."""
    with patch(
        "laion_fmri.download._prompt_license", return_value=True
    ) as mock_lic, patch(
        "laion_fmri.download._prompt_tou"
    ) as mock_tou:
        accept_licenses()

    mock_lic.assert_called_once()
    mock_tou.assert_not_called()
    assert (
        configured_env_no_license / ".laion_fmri" / "license_accepted"
    ).exists()


def test_accept_licenses_with_stimuli_prompts_both(
    configured_env_no_license,
):
    with patch(
        "laion_fmri.download._prompt_license", return_value=True
    ) as mock_lic, patch(
        "laion_fmri.download._prompt_tou", return_value=True
    ) as mock_tou:
        accept_licenses(include_stimuli=True)

    mock_lic.assert_called_once()
    mock_tou.assert_called_once()
    meta = configured_env_no_license / ".laion_fmri"
    assert (meta / "license_accepted").exists()
    assert (meta / "stimuli_terms_accepted").exists()


def test_accept_licenses_skips_when_already_accepted(configured_env):
    """Markers already on disk -> no prompts."""
    (
        configured_env / ".laion_fmri" / "stimuli_terms_accepted"
    ).touch()
    with patch(
        "laion_fmri.download._prompt_license"
    ) as mock_lic, patch(
        "laion_fmri.download._prompt_tou"
    ) as mock_tou:
        accept_licenses(include_stimuli=True)

    mock_lic.assert_not_called()
    mock_tou.assert_not_called()


def test_accept_licenses_raises_when_dataset_declined(
    configured_env_no_license,
):
    with patch(
        "laion_fmri.download._prompt_license", return_value=False
    ):
        with pytest.raises(
            LicenseNotAcceptedError, match="license must be accepted",
        ):
            accept_licenses()


def test_accept_licenses_raises_when_stimuli_declined(
    configured_env_no_license,
):
    with patch(
        "laion_fmri.download._prompt_license", return_value=True
    ), patch(
        "laion_fmri.download._prompt_tou", return_value=False
    ):
        with pytest.raises(
            RuntimeError, match="Terms of use",
        ):
            accept_licenses(include_stimuli=True)
