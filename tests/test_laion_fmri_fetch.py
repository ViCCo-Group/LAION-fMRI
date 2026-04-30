"""Tests for laion_fmri S3 fetch with BIDS-entity filters."""

import warnings
from unittest.mock import patch

import pytest

from laion_fmri._laion_fmri_fetch import (
    _clamp_n_jobs,
    _matches_filters,
    fetch_laion_fmri,
)


# ── _clamp_n_jobs ───────────────────────────────────────────────


def test_clamp_n_jobs_passes_valid():
    assert _clamp_n_jobs(4) == 4


def test_clamp_n_jobs_default_one():
    assert _clamp_n_jobs(1) == 1


def test_clamp_n_jobs_zero_falls_back_with_warning():
    with pytest.warns(UserWarning, match="positive int"):
        assert _clamp_n_jobs(0) == 1


def test_clamp_n_jobs_negative_falls_back_with_warning():
    with pytest.warns(UserWarning, match="positive int"):
        assert _clamp_n_jobs(-1) == 1


def test_clamp_n_jobs_non_int_falls_back_with_warning():
    with pytest.warns(UserWarning, match="positive int"):
        assert _clamp_n_jobs("four") == 1


def test_clamp_n_jobs_huge_value_clamped_with_warning():
    with pytest.warns(UserWarning, match="higher than"):
        result = _clamp_n_jobs(10000)
    assert result < 10000
    assert result >= 1


# ── _matches_filters ────────────────────────────────────────────


SES_KEY = (
    "derivatives/glmsingle-tedana/sub-03/ses-04/func/"
    "sub-03_ses-04_task-images_space-T1w_stat-effect_"
    "desc-SingletrialBetas_statmap.nii.gz"
)
SUBJECT_LEVEL_KEY = (
    "derivatives/glmsingle-tedana/sub-03/"
    "sub-03_task-images_space-T1w_"
    "desc-meanR2gt15mask_mask.nii.gz"
)


def test_matches_filters_no_filters():
    assert _matches_filters(SES_KEY, {}) is True


def test_matches_filters_ses_value():
    assert _matches_filters(SES_KEY, {"ses": "04"}) is True
    assert _matches_filters(SES_KEY, {"ses": "05"}) is False


def test_matches_filters_ses_full_token():
    """User can pass either the bare value or the full BIDS token."""
    assert _matches_filters(SES_KEY, {"ses": "ses-04"}) is True
    assert _matches_filters(SES_KEY, {"ses": "ses-05"}) is False


def test_matches_filters_ses_list():
    assert _matches_filters(SES_KEY, {"ses": ["04", "05"]}) is True
    assert (
        _matches_filters(SES_KEY, {"ses": ["02", "03"]}) is False
    )


def test_matches_filters_ses_strict_excludes_subject_level():
    """A specific ses filter excludes files without a ses entity.

    This is the strict ses semantic: subject-level summaries are
    NOT pulled along when the caller asks for one or more sessions.
    """
    assert (
        _matches_filters(SUBJECT_LEVEL_KEY, {"ses": "04"}) is False
    )


def test_matches_filters_ses_averages_keeps_subject_level():
    """The literal "averages" matches files without a ses entity."""
    assert (
        _matches_filters(
            SUBJECT_LEVEL_KEY, {"ses": "averages"},
        ) is True
    )


def test_matches_filters_ses_averages_excludes_session_files():
    """``ses="averages"`` matches only subject-level files."""
    assert (
        _matches_filters(SES_KEY, {"ses": "averages"}) is False
    )


def test_matches_filters_ses_list_with_averages_keeps_both():
    """List combining session IDs and 'averages' yields both."""
    assert (
        _matches_filters(
            SES_KEY, {"ses": ["04", "averages"]},
        ) is True
    )
    assert (
        _matches_filters(
            SUBJECT_LEVEL_KEY, {"ses": ["04", "averages"]},
        ) is True
    )


def test_matches_filters_other_entities_remain_permissive():
    """Strict logic only applies to ``ses``; other entities still
    let through files that don't carry the entity at all."""
    no_task_key = (
        "derivatives/glmsingle-tedana/sub-03/"
        "sub-03_space-T1w_desc-prfR2paradigmStandardOls_"
        "statmap.nii.gz"
    )
    assert (
        _matches_filters(no_task_key, {"task": "images"}) is True
    )


def test_matches_filters_task():
    assert (
        _matches_filters(SES_KEY, {"task": "images"}) is True
    )
    assert (
        _matches_filters(SES_KEY, {"task": "other"}) is False
    )


def test_matches_filters_space():
    assert (
        _matches_filters(
            SUBJECT_LEVEL_KEY, {"space": "T1w"},
        )
        is True
    )
    assert (
        _matches_filters(
            SUBJECT_LEVEL_KEY, {"space": "fsnative"},
        )
        is False
    )


def test_matches_filters_desc():
    assert (
        _matches_filters(SES_KEY, {"desc": "SingletrialBetas"})
        is True
    )
    assert (
        _matches_filters(SES_KEY, {"desc": "Noiseceiling"}) is False
    )


def test_matches_filters_stat():
    assert _matches_filters(SES_KEY, {"stat": "effect"}) is True
    assert (
        _matches_filters(SES_KEY, {"stat": "noiseceiling"}) is False
    )


def test_matches_filters_suffix():
    assert (
        _matches_filters(SES_KEY, {"suffix": "statmap"}) is True
    )
    assert (
        _matches_filters(SES_KEY, {"suffix": "events"}) is False
    )


def test_matches_filters_extension():
    assert (
        _matches_filters(SES_KEY, {"extension": "nii.gz"}) is True
    )
    assert (
        _matches_filters(SES_KEY, {"extension": "tsv"}) is False
    )


def test_matches_filters_combined():
    """All active filters must match (AND semantics)."""
    assert _matches_filters(
        SES_KEY,
        {"ses": "04", "stat": "effect", "extension": "nii.gz"},
    ) is True
    assert _matches_filters(
        SES_KEY,
        {"ses": "04", "stat": "noiseceiling"},
    ) is False


# ── fetch_laion_fmri ────────────────────────────────────────────


@patch("laion_fmri._laion_fmri_fetch.list_prefix_objects")
@patch("laion_fmri._laion_fmri_fetch.download_key")
def test_fetch_downloads_root_metadata(
    mock_download_key, mock_list_objects, tmp_path,
):
    """All four root-level metadata files are fetched."""
    mock_list_objects.return_value = []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        fetch_laion_fmri(str(tmp_path), subject="sub-03")

    keys = [c.args[1] for c in mock_download_key.call_args_list]
    for expected in (
        "dataset_description.json",
        "participants.tsv",
        "participants.json",
        "README",
    ):
        assert expected in keys


@patch("laion_fmri._laion_fmri_fetch.list_prefix_objects")
@patch("laion_fmri._laion_fmri_fetch.download_key")
def test_fetch_lists_glmsingle_and_atlases_prefixes(
    mock_download_key, mock_list_objects, tmp_path,
):
    mock_list_objects.return_value = []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        fetch_laion_fmri(str(tmp_path), subject="sub-03")

    listed = [c.args[1] for c in mock_list_objects.call_args_list]
    assert "derivatives/glmsingle-tedana/sub-03/" in listed
    assert "derivatives/atlases/sub-03/" in listed


@patch("laion_fmri._laion_fmri_fetch.list_prefix_objects")
@patch("laion_fmri._laion_fmri_fetch.download_key")
def test_fetch_skips_stimuli_by_default(
    mock_download_key, mock_list_objects, tmp_path,
):
    mock_list_objects.return_value = []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        fetch_laion_fmri(str(tmp_path), subject="sub-03")

    listed = [c.args[1] for c in mock_list_objects.call_args_list]
    assert "stimuli/" not in listed


@patch("laion_fmri._laion_fmri_fetch.list_prefix_objects")
@patch("laion_fmri._laion_fmri_fetch.download_key")
def test_fetch_lists_stimuli_when_requested(
    mock_download_key, mock_list_objects, tmp_path,
):
    mock_list_objects.return_value = []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        fetch_laion_fmri(
            str(tmp_path), subject="sub-03", include_stimuli=True,
        )

    listed = [c.args[1] for c in mock_list_objects.call_args_list]
    assert "stimuli/" in listed


@patch("laion_fmri._laion_fmri_fetch.list_prefix_objects")
@patch("laion_fmri._laion_fmri_fetch.download_key")
def test_fetch_ses_filter_narrows_downloads(
    mock_download_key, mock_list_objects, tmp_path,
):
    """``ses="04"`` keeps the requested session and the brain mask;
    other sessions and other subject-level summaries are excluded."""
    ses04 = (
        "derivatives/glmsingle-tedana/sub-03/ses-04/func/"
        "sub-03_ses-04_task-images_space-T1w_stat-effect_"
        "desc-SingletrialBetas_statmap.nii.gz"
    )
    ses05 = (
        "derivatives/glmsingle-tedana/sub-03/ses-05/func/"
        "sub-03_ses-05_task-images_space-T1w_stat-effect_"
        "desc-SingletrialBetas_statmap.nii.gz"
    )
    brain_mask = (
        "derivatives/glmsingle-tedana/sub-03/"
        "sub-03_task-images_space-T1w_"
        "desc-meanR2gt15mask_mask.nii.gz"
    )
    other_summary = (
        "derivatives/glmsingle-tedana/sub-03/"
        "sub-03_task-images_space-T1w_"
        "desc-Noiseceiling12rep_statmap.nii.gz"
    )

    def listing(_bucket, prefix):
        if prefix.endswith("glmsingle-tedana/sub-03/"):
            return [
                {"Key": ses04, "Size": 100},
                {"Key": ses05, "Size": 100},
                {"Key": brain_mask, "Size": 100},
                {"Key": other_summary, "Size": 100},
            ]
        return []

    mock_list_objects.side_effect = listing

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        fetch_laion_fmri(
            str(tmp_path), subject="sub-03", ses="04",
        )

    downloaded = [
        c.args[1] for c in mock_download_key.call_args_list
    ]
    assert ses04 in downloaded
    assert ses05 not in downloaded
    assert brain_mask in downloaded  # pinned by force_keys
    assert other_summary not in downloaded  # strict ses excludes


@patch("laion_fmri._laion_fmri_fetch.list_prefix_objects")
@patch("laion_fmri._laion_fmri_fetch.download_key")
def test_fetch_ses_averages_keeps_all_subject_level(
    mock_download_key, mock_list_objects, tmp_path,
):
    """``ses="averages"`` keeps every subject-level file."""
    brain_mask = (
        "derivatives/glmsingle-tedana/sub-03/"
        "sub-03_task-images_space-T1w_"
        "desc-meanR2gt15mask_mask.nii.gz"
    )
    other_summary = (
        "derivatives/glmsingle-tedana/sub-03/"
        "sub-03_task-images_space-T1w_"
        "desc-Noiseceiling12rep_statmap.nii.gz"
    )
    ses04 = (
        "derivatives/glmsingle-tedana/sub-03/ses-04/func/"
        "sub-03_ses-04_task-images_space-T1w_stat-effect_"
        "desc-SingletrialBetas_statmap.nii.gz"
    )

    def listing(_bucket, prefix):
        if prefix.endswith("glmsingle-tedana/sub-03/"):
            return [
                {"Key": ses04, "Size": 100},
                {"Key": brain_mask, "Size": 100},
                {"Key": other_summary, "Size": 100},
            ]
        return []

    mock_list_objects.side_effect = listing

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        fetch_laion_fmri(
            str(tmp_path), subject="sub-03", ses="averages",
        )

    downloaded = [
        c.args[1] for c in mock_download_key.call_args_list
    ]
    assert brain_mask in downloaded
    assert other_summary in downloaded
    assert ses04 not in downloaded  # session files excluded


@patch("laion_fmri._laion_fmri_fetch.list_prefix_objects")
@patch("laion_fmri._laion_fmri_fetch.download_key")
def test_fetch_warns_when_no_match(
    mock_download_key, mock_list_objects, tmp_path,
):
    """Empty match + no local copy emits the missing-data warning."""
    mock_list_objects.return_value = []

    with pytest.warns(UserWarning, match="No objects matching"):
        fetch_laion_fmri(str(tmp_path), subject="sub-03")


@patch("laion_fmri._laion_fmri_fetch.list_prefix_objects")
@patch("laion_fmri._laion_fmri_fetch.download_key")
def test_fetch_does_not_warn_when_local_dir_has_data(
    mock_download_key, mock_list_objects, tmp_path,
):
    mock_list_objects.return_value = []

    for prefix in (
        "derivatives/atlases/sub-03",
        "derivatives/glmsingle-tedana/sub-03",
    ):
        d = tmp_path / prefix
        d.mkdir(parents=True)
        (d / "existing.txt").write_text("hi")

    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        fetch_laion_fmri(str(tmp_path), subject="sub-03")
    relevant = [
        w for w in record
        if issubclass(w.category, UserWarning)
        and "No objects matching" in str(w.message)
    ]
    assert relevant == []


# ── size-aware skip (resume support) ────────────────────────────


@patch("laion_fmri._laion_fmri_fetch.list_prefix_objects")
@patch("laion_fmri._laion_fmri_fetch.download_key")
def test_fetch_skips_already_complete_file(
    mock_download_key, mock_list_objects, tmp_path,
):
    """A local file matching the S3 size is not re-downloaded."""
    key = (
        "derivatives/glmsingle-tedana/sub-03/"
        "sub-03_task-images_space-T1w_"
        "desc-meanR2gt15mask_mask.nii.gz"
    )
    local = tmp_path / key
    local.parent.mkdir(parents=True)
    local.write_bytes(b"x" * 42)

    def listing(_bucket, prefix):
        if prefix.endswith("glmsingle-tedana/sub-03/"):
            return [{"Key": key, "Size": 42}]
        return []

    mock_list_objects.side_effect = listing

    fetch_laion_fmri(str(tmp_path), subject="sub-03")

    keys_called = [
        c.args[1] for c in mock_download_key.call_args_list
    ]
    assert key not in keys_called  # skipped


@patch("laion_fmri._laion_fmri_fetch.list_prefix_objects")
@patch("laion_fmri._laion_fmri_fetch.download_key")
def test_fetch_redownloads_when_size_mismatch(
    mock_download_key, mock_list_objects, tmp_path,
):
    """A local file with wrong size is re-downloaded."""
    key = (
        "derivatives/glmsingle-tedana/sub-03/"
        "sub-03_task-images_space-T1w_"
        "desc-meanR2gt15mask_mask.nii.gz"
    )
    local = tmp_path / key
    local.parent.mkdir(parents=True)
    local.write_bytes(b"x" * 10)  # too short

    def listing(_bucket, prefix):
        if prefix.endswith("glmsingle-tedana/sub-03/"):
            return [{"Key": key, "Size": 100}]
        return []

    mock_list_objects.side_effect = listing

    fetch_laion_fmri(str(tmp_path), subject="sub-03")

    keys_called = [
        c.args[1] for c in mock_download_key.call_args_list
    ]
    assert key in keys_called  # re-downloaded


# ── n_jobs (parallel downloads) ─────────────────────────────────


@patch("laion_fmri._laion_fmri_fetch.list_prefix_objects")
@patch("laion_fmri._laion_fmri_fetch.download_key")
def test_fetch_n_jobs_downloads_all_keys(
    mock_download_key, mock_list_objects, tmp_path,
):
    """With n_jobs > 1, every matching key is still downloaded."""
    keys = [
        f"derivatives/glmsingle-tedana/sub-03/file-{i}.bin"
        for i in range(8)
    ]

    def listing(_bucket, prefix):
        if prefix.endswith("glmsingle-tedana/sub-03/"):
            return [{"Key": k, "Size": 1} for k in keys]
        return []

    mock_list_objects.side_effect = listing

    fetch_laion_fmri(str(tmp_path), subject="sub-03", n_jobs=4)

    called = {
        c.args[1] for c in mock_download_key.call_args_list
    }
    for k in keys:
        assert k in called
