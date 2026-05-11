from pathlib import Path

import pytest

from laion_fmri._paths import (
    betas_path,
    glmsingle_subject_dir,
    license_marker_path,
    participants_tsv_path,
    r2mean_path,
    roi_freesurfer_label_path,
    roi_mask_path,
    roi_surface_path,
    rois_subject_dir,
    session_func_dir,
    session_noise_ceiling_path,
    stimuli_dir_path,
    stimuli_h5_path,
    stimuli_metadata_csv_path,
    stimuli_metadata_path,
    subject_noise_ceiling_path,
    trialinfo_path,
)


def test_glmsingle_subject_dir():
    result = glmsingle_subject_dir("/data", "sub-03")
    assert result == Path(
        "/data/derivatives/glmsingle-tedana/sub-03"
    )


def test_session_func_dir():
    result = session_func_dir("/data", "sub-03", "ses-01")
    assert result == Path(
        "/data/derivatives/glmsingle-tedana/sub-03/ses-01/func"
    )


def test_betas_path_per_session():
    result = betas_path("/data", "sub-03", "ses-04")
    assert result == Path(
        "/data/derivatives/glmsingle-tedana/sub-03/ses-04/func/"
        "sub-03_ses-04_task-images_space-T1w_stat-effect_"
        "desc-SingletrialBetas_statmap.nii.gz"
    )


def test_session_noise_ceiling_path():
    result = session_noise_ceiling_path(
        "/data", "sub-03", "ses-04",
    )
    assert result == Path(
        "/data/derivatives/glmsingle-tedana/sub-03/ses-04/func/"
        "sub-03_ses-04_task-images_space-T1w_"
        "desc-Noiseceiling_statmap.nii.gz"
    )


def test_trialinfo_path():
    result = trialinfo_path("/data", "sub-03", "ses-04")
    assert result == Path(
        "/data/derivatives/glmsingle-tedana/sub-03/ses-04/func/"
        "sub-03_ses-04_task-images_desc-SingletrialBetas_trials.tsv"
    )


def test_r2mean_path():
    result = r2mean_path("/data", "sub-03")
    assert result == Path(
        "/data/derivatives/glmsingle-tedana/sub-03/"
        "sub-03_task-images_space-T1w_"
        "stat-rsquare_desc-R2mean_statmap.nii.gz"
    )


def test_subject_noise_ceiling_path():
    result = subject_noise_ceiling_path(
        "/data", "sub-03", "Noiseceiling12rep",
    )
    assert result == Path(
        "/data/derivatives/glmsingle-tedana/sub-03/"
        "sub-03_task-images_space-T1w_"
        "desc-Noiseceiling12rep_statmap.nii.gz"
    )


# ── ROI path resolvers ─────────────────────────────────────────


def test_rois_subject_dir():
    assert rois_subject_dir("/d", "sub-03") == Path(
        "/d/derivatives/rois/sub-03"
    )


def test_roi_mask_path_finds_volume(tmp_path):
    """Volume mask file is glob-resolved by ROI label."""
    face_dir = tmp_path / "derivatives/rois/sub-03/face"
    face_dir.mkdir(parents=True)
    expected = (
        face_dir
        / "sub-03_space-T1w_res-1pt8_label-FFA1_mask.nii.gz"
    )
    expected.touch()

    assert roi_mask_path(tmp_path, "sub-03", "FFA1") == expected


def test_roi_mask_path_unknown_raises(tmp_path):
    rois_dir = tmp_path / "derivatives/rois/sub-03/face"
    rois_dir.mkdir(parents=True)

    with pytest.raises(FileNotFoundError, match="FFA99"):
        roi_mask_path(tmp_path, "sub-03", "FFA99")


def test_roi_surface_path_finds_func_gii_per_hemi(tmp_path):
    place_dir = tmp_path / "derivatives/rois/sub-03/place"
    place_dir.mkdir(parents=True)
    expected_l = (
        place_dir
        / "sub-03_hemi-L_space-fsnative_label-PPA_mask.func.gii"
    )
    expected_r = (
        place_dir
        / "sub-03_hemi-R_space-fsnative_label-PPA_mask.func.gii"
    )
    expected_l.touch()
    expected_r.touch()

    assert roi_surface_path(
        tmp_path, "sub-03", "PPA", "L",
    ) == expected_l
    assert roi_surface_path(
        tmp_path, "sub-03", "PPA", "R",
    ) == expected_r


def test_roi_surface_path_unknown_raises(tmp_path):
    rois_dir = tmp_path / "derivatives/rois/sub-03/face"
    rois_dir.mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        roi_surface_path(tmp_path, "sub-03", "PPA", "L")


def test_roi_freesurfer_label_path_finds_per_hemi(tmp_path):
    place_dir = tmp_path / "derivatives/rois/sub-03/place"
    place_dir.mkdir(parents=True)
    expected = (
        place_dir
        / "sub-03_hemi-L_space-fsnative_label-PPA_mask.label"
    )
    expected.touch()

    assert roi_freesurfer_label_path(
        tmp_path, "sub-03", "PPA", "L",
    ) == expected


def test_roi_freesurfer_label_path_unknown_raises(tmp_path):
    rois_dir = tmp_path / "derivatives/rois/sub-03/face"
    rois_dir.mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        roi_freesurfer_label_path(tmp_path, "sub-03", "PPA", "L")


# ── Stimuli / metadata / markers ───────────────────────────────


def test_stimuli_dir_path():
    """Legacy per-PNG layout."""
    assert stimuli_dir_path("/data") == Path("/data/stimuli/images")


def test_stimuli_metadata_path():
    """Legacy TSV metadata path (used by Subject)."""
    assert stimuli_metadata_path("/data") == Path(
        "/data/stimuli/stimuli.tsv"
    )


def test_stimuli_h5_path():
    """New schema: single HDF5 archive."""
    assert stimuli_h5_path("/data") == Path(
        "/data/stimuli/task-images_stimuli.h5"
    )


def test_stimuli_metadata_csv_path():
    """New schema: CSV metadata paired with the HDF5."""
    assert stimuli_metadata_csv_path("/data") == Path(
        "/data/stimuli/task-images_metadata.csv"
    )


def test_participants_tsv_path():
    assert participants_tsv_path("/data") == Path(
        "/data/participants.tsv"
    )


def test_license_marker_path():
    assert license_marker_path("/data") == Path(
        "/data/.laion_fmri/license_accepted"
    )
