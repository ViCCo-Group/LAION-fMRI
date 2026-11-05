"""Tests for the S3-backed discovery API."""

from unittest.mock import patch

import pytest

from laion_fmri.discovery import describe, get_rois, get_subjects


# ── get_subjects ────────────────────────────────────────────────


def test_get_subjects_default_is_the_main_experiment():
    """Uploading the mapping-only subjects must not change the default."""
    assert get_subjects() == [
        "sub-01", "sub-03", "sub-05", "sub-06", "sub-07",
    ]
    assert get_subjects("main") == get_subjects()


def test_get_subjects_mapping_adds_sub04_sub08():
    assert get_subjects("mapping") == [
        "sub-01", "sub-03", "sub-04", "sub-05", "sub-06", "sub-07",
        "sub-08",
    ]


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_does_not_query_the_bucket(mock_lcp):
    get_subjects()
    get_subjects("mapping")
    mock_lcp.assert_not_called()


def test_get_subjects_rejects_unknown_dataset():
    with pytest.raises(ValueError):
        get_subjects("all+mapping")


@patch("laion_fmri.discovery.list_common_prefixes")
def test_inspect_bucket_mentions_raw_prefix(mock_lcp, capsys):
    """``inspect_bucket`` reports the raw BIDS root among probed prefixes."""
    from laion_fmri.discovery import inspect_bucket

    mock_lcp.return_value = []
    inspect_bucket()
    out = capsys.readouterr().out
    assert "sub-" in out


# ── get_rois ────────────────────────────────────────────────────


@patch("laion_fmri.discovery.list_prefix_keys")
def test_get_rois_lists_bidsified_names_from_bucket(mock_lpk):
    """Hyphenated label values are normalized to BIDS-clean form."""
    mock_lpk.return_value = [
        "derivatives/rois/sub-01/face/"
        "sub-01_space-T1w_res-1pt8_label-FFA-1_mask.nii.gz",
        "derivatives/rois/sub-01/face/"
        "sub-01_space-T1w_res-1pt8_label-OFA_mask.nii.gz",
    ]
    assert get_rois(subject="sub-01") == ["FFA1", "OFA"]


@patch("laion_fmri.discovery.list_prefix_keys")
def test_get_rois_uses_volume_files_only(mock_lpk):
    """Volume nii.gz is the source of truth; surface files are ignored."""
    mock_lpk.return_value = [
        "derivatives/rois/sub-01/face/"
        "sub-01_space-T1w_res-1pt8_label-OFA_mask.nii.gz",
        "derivatives/rois/sub-01/face/"
        "sub-01_hemi-L_space-fsnative_label-OFA_mask.func.gii",
        "derivatives/rois/sub-01/face/"
        "sub-01_hemi-L_space-fsnative_label-OFA_mask.label",
    ]
    assert get_rois(subject="sub-01") == ["OFA"]


@patch("laion_fmri.discovery.list_prefix_keys")
def test_get_rois_category_filter(mock_lpk):
    mock_lpk.return_value = [
        "derivatives/rois/sub-01/face/"
        "sub-01_space-T1w_res-1pt8_label-FFA1_mask.nii.gz",
        "derivatives/rois/sub-01/face/"
        "sub-01_space-T1w_res-1pt8_label-OFA_mask.nii.gz",
        "derivatives/rois/sub-01/place/"
        "sub-01_space-T1w_res-1pt8_label-PPA_mask.nii.gz",
    ]
    assert get_rois(subject="sub-01", category="face") == [
        "FFA1", "OFA",
    ]
    assert get_rois(subject="sub-01", category="place") == ["PPA"]


@patch("laion_fmri.discovery.list_prefix_keys")
@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_rois_default_subject_uses_first_in_bucket(
    mock_lcp, mock_lpk,
):
    # get_subjects scans glmsingle-tedana, rois, freesurfer, anatomical,
    # raw root
    mock_lcp.side_effect = [["sub-01"], [], [], [], [], []]
    mock_lpk.return_value = [
        "derivatives/rois/sub-01/face/"
        "sub-01_space-T1w_res-1pt8_label-OFA_mask.nii.gz",
    ]
    assert get_rois() == ["OFA"]


@patch("laion_fmri.discovery.list_prefix_keys")
@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_rois_empty_when_bucket_empty(mock_lcp, mock_lpk):
    mock_lcp.side_effect = [[], [], [], [], [], []]
    mock_lpk.return_value = []
    with pytest.warns(UserWarning):
        assert get_rois() == []


@patch("laion_fmri.discovery.list_prefix_keys")
def test_get_rois_warns_for_explicit_subject_without_rois(mock_lpk):
    mock_lpk.return_value = []
    with pytest.warns(UserWarning, match="No ROIs"):
        assert get_rois(subject="sub-99") == []


# ── describe ────────────────────────────────────────────────────


@patch("laion_fmri.discovery.list_prefix_keys")
@patch("laion_fmri.discovery.list_common_prefixes")
def test_describe_prints_bucket_summary(
    mock_lcp, mock_lpk, capsys,
):
    mock_lcp.side_effect = [["sub-01", "sub-03"], [], [], [], [], []]
    mock_lpk.return_value = [
        "derivatives/rois/sub-01/face/"
        "sub-01_space-T1w_res-1pt8_label-OFA_mask.nii.gz",
    ]

    describe()
    out = capsys.readouterr().out
    assert "LAION-fMRI" in out
    assert "s3://laion-fmri" in out
    assert "sub-01" in out
    assert "sub-03" in out
    assert "OFA" in out
