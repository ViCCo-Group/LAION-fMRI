from unittest.mock import call, patch

import pytest

from laion_fmri._constants import LICENSE_AGREEMENT_TEXT
from laion_fmri._errors import LicenseNotAcceptedError, SubjectNotFoundError
from laion_fmri.download import (
    _check_license_accepted,
    _prompt_stimulus_form,
    _write_license_marker,
    accept_license,
    accept_licenses,
    download,
    download_captions,
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


# fetch_laion_fmri no longer accepts an ``include_stimuli`` flag —
# stimuli are downloaded via the access service in a separate call.
DEFAULT_FETCH_KWARGS = dict(
    ses=None, task=None, space=None, desc=None, stat=None,
    suffix=None, extension=None, n_jobs=1,
    include_freesurfer=False, include_anatomical=False,
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
    fMRI fetch. ``fetch_laion_fmri`` itself no longer knows about
    ``include_stimuli``."""
    with patch("laion_fmri.download.fetch_laion_fmri") as mock_fetch, patch(
        "laion_fmri.download.download_stimuli"
    ) as mock_stim:
        download(subject="sub-01", include_stimuli=True)

    mock_fetch.assert_called_once()
    assert "include_stimuli" not in mock_fetch.call_args.kwargs
    mock_stim.assert_called_once_with(data_dir=str(configured_env))


def test_download_without_stimuli_does_not_call_access_service(configured_env):
    with patch("laion_fmri.download.fetch_laion_fmri"), patch(
        "laion_fmri.download.download_stimuli"
    ) as mock_stim:
        download(subject="sub-01")
    mock_stim.assert_not_called()


# ── include_freesurfer forwards to fetch_laion_fmri ────────────


def test_download_passes_include_freesurfer_to_fetch(configured_env):
    """``include_freesurfer=True`` flows through to the per-subject
    fetch call so the recon prefix gets pulled.
    """
    with patch("laion_fmri.download.fetch_laion_fmri") as mock_fetch:
        download(subject="sub-01", include_freesurfer=True)
    kwargs = mock_fetch.call_args.kwargs
    assert kwargs["include_freesurfer"] is True


def test_download_include_freesurfer_default_false(configured_env):
    """Default is to skip the recon -- it's hundreds of MB per subject."""
    with patch("laion_fmri.download.fetch_laion_fmri") as mock_fetch:
        download(subject="sub-01")
    kwargs = mock_fetch.call_args.kwargs
    assert kwargs.get("include_freesurfer", False) is False


# ── include_anatomical forwards to fetch_laion_fmri ────────────


def test_download_passes_include_anatomical_to_fetch(configured_env):
    """``include_anatomical=True`` flows through to the per-subject
    fetch call so the anat prefix gets pulled.
    """
    with patch("laion_fmri.download.fetch_laion_fmri") as mock_fetch:
        download(subject="sub-01", include_anatomical=True)
    kwargs = mock_fetch.call_args.kwargs
    assert kwargs["include_anatomical"] is True


def test_download_include_anatomical_default_false(configured_env):
    """Default skips the anat tree -- it's tens of MB per subject."""
    with patch("laion_fmri.download.fetch_laion_fmri") as mock_fetch:
        download(subject="sub-01")
    kwargs = mock_fetch.call_args.kwargs
    assert kwargs.get("include_anatomical", False) is False


def test_download_captions_fetches_public_csv(configured_env):
    with patch("laion_fmri.download.accept_license") as mock_accept, patch(
        "laion_fmri.download.list_prefix_objects",
        return_value=[
            {
                "Key": "stimuli/task-images_desc-captions.csv",
                "Size": 123,
            }
        ],
    ), patch("laion_fmri.download.download_key") as mock_download:
        path = download_captions(data_dir=str(configured_env))

    mock_accept.assert_called_once()
    mock_download.assert_called_once_with(
        "laion-fmri",
        "stimuli/task-images_desc-captions.csv",
        path,
    )


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


def test_prompt_stimulus_form_acknowledges_terms_and_privacy(capsys):
    responses = iter([
        "Ada Lovelace",
        "ada@example.edu",
        "Analytical Engine Institute",
        "",
        "Benchmarking visual encoding models on LAION-fMRI stimuli.",
        "yes",
    ])

    with patch(
        "laion_fmri.download.current_terms_version",
        return_value="2026-05-12",
    ), patch(
        "builtins.input",
        side_effect=lambda prompt="": next(responses),
    ) as mock_input:
        payload, email = _prompt_stimulus_form("https://example.test")

    captured = capsys.readouterr()
    assert "https://example.test/terms" in captured.out
    assert "https://example.test/privacy" in captured.out
    assert "Terms of Use" in mock_input.call_args_list[-1].args[0]
    assert "Privacy notice" in mock_input.call_args_list[-1].args[0]
    assert payload["accepted_terms"] is True
    assert payload["acknowledged_privacy"] is True
    assert payload["terms_version"] == "2026-05-12"
    assert payload["source"] == "cli"
    assert email == "ada@example.edu"


def test_download_stimuli_skips_auth_when_local_files_match(configured_env):
    """If local stimuli match the public manifest, the loader must NOT
    contact the access service. This is what lets a cluster job just
    rsync the data dir and call ``download_stimuli()`` without copying
    any auth state."""
    import hashlib
    from laion_fmri.download import download_stimuli

    stim_dir = configured_env / "stimuli"
    stim_dir.mkdir(exist_ok=True)
    h5_bytes = b"FAKEH5"
    csv_bytes = b"image_name\nx\n"
    (stim_dir / "task-images_stimuli.h5").write_bytes(h5_bytes)
    (stim_dir / "task-images_metadata.csv").write_bytes(csv_bytes)

    fake_manifest = {
        "dataset": "laion-fmri",
        "current_terms_version": "2026-05-11",
        "versions": ["v1"],
        "files": [
            {"name": "task-images_stimuli.h5",
             "size": len(h5_bytes),
             "sha256": hashlib.sha256(h5_bytes).hexdigest()},
            {"name": "task-images_metadata.csv",
             "size": len(csv_bytes),
             "sha256": hashlib.sha256(csv_bytes).hexdigest()},
        ],
    }

    with patch(
        "laion_fmri.download.fetch_manifest", return_value=fake_manifest,
    ) as mock_manifest, patch(
        "laion_fmri.download._resolve_stimulus_access"
    ) as mock_resolve, patch(
        "laion_fmri.download.download_file"
    ) as mock_download:
        download_stimuli()

    mock_manifest.assert_called_once()
    mock_resolve.assert_not_called()
    mock_download.assert_not_called()
