"""Tests for the S3-backed discovery API."""

from unittest.mock import patch

import pytest

from laion_fmri.discovery import describe, get_rois, get_subjects


# ── get_subjects ────────────────────────────────────────────────


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_lists_from_bucket(mock_lcp):
    # First call: glmsingle-tedana, second call: atlases
    mock_lcp.side_effect = [
        ["sub-01", "sub-03"],
        ["sub-01", "sub-03", "sub-05"],
    ]
    assert get_subjects() == ["sub-01", "sub-03", "sub-05"]


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_union_across_derivatives(mock_lcp):
    """Subject present only in atlases is still returned."""
    mock_lcp.side_effect = [[], ["sub-01"]]
    assert get_subjects() == ["sub-01"]


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_probes_glmsingle_tedana_first(mock_lcp):
    """glmsingle-tedana is the primary derivative tree."""
    mock_lcp.side_effect = [[], []]
    import pytest as _pytest
    with _pytest.warns(UserWarning):
        get_subjects()
    prefixes = [call.args[1] for call in mock_lcp.call_args_list]
    assert prefixes[0] == "derivatives/glmsingle-tedana/"
    assert "derivatives/atlases/" in prefixes


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_warns_when_empty(mock_lcp):
    mock_lcp.side_effect = [[], []]
    with pytest.warns(UserWarning, match="No subjects found"):
        result = get_subjects()
    assert result == []


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_filters_non_subject_names(mock_lcp):
    mock_lcp.side_effect = [["sub-01", "_tmp"], []]
    assert get_subjects() == ["sub-01"]


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_queries_both_derivative_prefixes(mock_lcp):
    mock_lcp.side_effect = [[], []]
    with pytest.warns(UserWarning):
        get_subjects()
    prefixes = [call.args[1] for call in mock_lcp.call_args_list]
    assert "derivatives/glmsingle-tedana/" in prefixes
    assert "derivatives/atlases/" in prefixes


# ── get_rois ────────────────────────────────────────────────────


@patch("laion_fmri.discovery.list_prefix_keys")
def test_get_rois_lists_from_bucket(mock_lpk):
    mock_lpk.return_value = [
        "derivatives/atlases/sub-01/rois/visual.nii.gz",
        "derivatives/atlases/sub-01/rois/face_area.nii.gz",
    ]
    assert get_rois(subject="sub-01") == ["face_area", "visual"]


@patch("laion_fmri.discovery.list_prefix_keys")
def test_get_rois_ignores_non_roi_files(mock_lpk):
    mock_lpk.return_value = [
        "derivatives/atlases/sub-01/rois/visual.nii.gz",
        "derivatives/atlases/sub-01/rois/notes.txt",
    ]
    assert get_rois(subject="sub-01") == ["visual"]


@patch("laion_fmri.discovery.list_prefix_keys")
@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_rois_default_subject_uses_first_in_bucket(
    mock_lcp, mock_lpk,
):
    mock_lcp.side_effect = [["sub-01"], []]  # get_subjects listings
    mock_lpk.return_value = [
        "derivatives/atlases/sub-01/rois/visual.nii.gz",
    ]
    assert get_rois() == ["visual"]


@patch("laion_fmri.discovery.list_prefix_keys")
@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_rois_empty_when_bucket_empty(mock_lcp, mock_lpk):
    mock_lcp.side_effect = [[], []]
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
    mock_lcp.side_effect = [["sub-01", "sub-03"], []]
    mock_lpk.return_value = [
        "derivatives/atlases/sub-01/rois/visual.nii.gz",
    ]

    describe()
    out = capsys.readouterr().out
    assert "LAION-fMRI" in out
    assert "s3://laion-fmri" in out
    assert "sub-01" in out
    assert "sub-03" in out
    assert "visual" in out
