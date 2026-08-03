"""Tests for the S3-backed discovery API."""

from unittest.mock import patch

import pytest

from laion_fmri.discovery import describe, get_rois, get_subjects


# ── get_subjects ────────────────────────────────────────────────


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_lists_from_bucket(mock_lcp):
    # glmsingle-tedana, rois, freesurfer, anatomical, raw root
    mock_lcp.side_effect = [
        ["sub-01", "sub-03"],
        ["sub-01", "sub-03", "sub-05"],
        [],
        [],
        [],
    ]
    assert get_subjects() == ["sub-01", "sub-03", "sub-05"]


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_union_across_derivatives(mock_lcp):
    """Subject present only in rois is still returned."""
    mock_lcp.side_effect = [[], ["sub-01"], [], [], []]
    assert get_subjects() == ["sub-01"]


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_probes_glmsingle_tedana_first(mock_lcp):
    """glmsingle-tedana is the primary derivative tree."""
    mock_lcp.side_effect = [[], [], [], [], []]
    with pytest.warns(UserWarning):
        get_subjects()
    prefixes = [call.args[1] for call in mock_lcp.call_args_list]
    assert prefixes[0] == "derivatives/glmsingle-tedana/"
    assert "derivatives/rois/" in prefixes


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_warns_when_empty(mock_lcp):
    mock_lcp.side_effect = [[], [], [], [], []]
    with pytest.warns(UserWarning, match="No subjects found"):
        result = get_subjects()
    assert result == []


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_filters_non_subject_names(mock_lcp):
    mock_lcp.side_effect = [["sub-01", "_tmp"], [], [], [], []]
    assert get_subjects() == ["sub-01"]


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_queries_all_derivative_prefixes(mock_lcp):
    mock_lcp.side_effect = [[], [], [], [], []]
    with pytest.warns(UserWarning):
        get_subjects()
    prefixes = [call.args[1] for call in mock_lcp.call_args_list]
    assert "derivatives/glmsingle-tedana/" in prefixes
    assert "derivatives/rois/" in prefixes
    assert "derivatives/freesurfer/" in prefixes


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_finds_freesurfer_only_subjects(mock_lcp):
    """Subject with only a FreeSurfer recon (no glmsingle, no rois)
    is still returned -- some subjects may have an anatomical
    pipeline run before the functional one lands.
    """
    # glmsingle-tedana, rois, freesurfer, anatomical, raw root
    mock_lcp.side_effect = [[], [], ["sub-07"], [], []]
    assert get_subjects() == ["sub-07"]


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_includes_anatomical_prefix(mock_lcp):
    """``derivatives/anatomical/`` is one of the subject-prefix probes."""
    mock_lcp.side_effect = [[], [], [], [], []]
    with pytest.warns(UserWarning):
        get_subjects()
    prefixes = [call.args[1] for call in mock_lcp.call_args_list]
    assert "derivatives/anatomical/" in prefixes


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_finds_anatomical_only_subjects(mock_lcp):
    """Subject present only in anatomical derivatives still surfaces."""
    # glmsingle-tedana, rois, freesurfer, anatomical, raw root
    mock_lcp.side_effect = [[], [], [], ["sub-09"], []]
    assert get_subjects() == ["sub-09"]


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_finds_raw_only_subjects(mock_lcp):
    """Subject present only under ``sub-XX/`` (raw BIDS root) surfaces.

    A subject who has raw multi-echo BOLD uploaded but no derivatives
    yet must still be reachable via ``get_subjects()`` so that
    ``download_raw(subject="all")`` can iterate over them.
    """
    # glmsingle-tedana, rois, freesurfer, anatomical, raw root
    mock_lcp.side_effect = [[], [], [], [], ["sub-11"]]
    assert get_subjects() == ["sub-11"]


@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_subjects_probes_raw_bids_root_prefix(mock_lcp):
    """``""`` (bucket root) is probed so ``sub-*`` under raw root surfaces."""
    mock_lcp.side_effect = [[], [], [], [], []]
    with pytest.warns(UserWarning):
        get_subjects()
    prefixes = [call.args[1] for call in mock_lcp.call_args_list]
    assert "" in prefixes


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
    mock_lcp.side_effect = [["sub-01"], [], [], [], []]
    mock_lpk.return_value = [
        "derivatives/rois/sub-01/face/"
        "sub-01_space-T1w_res-1pt8_label-OFA_mask.nii.gz",
    ]
    assert get_rois() == ["OFA"]


@patch("laion_fmri.discovery.list_prefix_keys")
@patch("laion_fmri.discovery.list_common_prefixes")
def test_get_rois_empty_when_bucket_empty(mock_lcp, mock_lpk):
    mock_lcp.side_effect = [[], [], [], [], []]
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
    mock_lcp.side_effect = [["sub-01", "sub-03"], [], [], [], []]
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
