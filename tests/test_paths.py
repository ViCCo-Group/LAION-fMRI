from pathlib import Path

from laion_fmri._paths import (
    atlases_subject_dir,
    betas_path,
    brain_mask_path,
    glmsingle_subject_dir,
    license_marker_path,
    participants_tsv_path,
    roi_mask_path,
    rois_dir,
    session_func_dir,
    session_noise_ceiling_path,
    stimuli_dir_path,
    stimuli_metadata_path,
    subject_noise_ceiling_path,
    tou_marker_path,
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


def test_brain_mask_path_subject_level():
    result = brain_mask_path("/data", "sub-03")
    assert result == Path(
        "/data/derivatives/glmsingle-tedana/sub-03/"
        "sub-03_task-images_space-T1w_"
        "desc-meanR2gt15mask_mask.nii.gz"
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


def test_roi_mask_path():
    result = roi_mask_path("/data", "sub-03", "visual")
    assert result == Path(
        "/data/derivatives/atlases/sub-03/rois/visual.nii.gz"
    )


def test_atlases_subject_dir():
    assert atlases_subject_dir("/d", "sub-03") == Path(
        "/d/derivatives/atlases/sub-03"
    )


def test_rois_dir():
    assert rois_dir("/d", "sub-03") == Path(
        "/d/derivatives/atlases/sub-03/rois"
    )


def test_stimuli_dir_path():
    assert stimuli_dir_path("/data") == Path("/data/stimuli/images")


def test_stimuli_metadata_path():
    assert stimuli_metadata_path("/data") == Path(
        "/data/stimuli/stimuli.tsv"
    )


def test_participants_tsv_path():
    assert participants_tsv_path("/data") == Path(
        "/data/participants.tsv"
    )


def test_license_marker_path():
    assert license_marker_path("/data") == Path(
        "/data/.laion_fmri/license_accepted"
    )


def test_tou_marker_path():
    assert tou_marker_path("/data") == Path(
        "/data/.laion_fmri/stimuli_terms_accepted"
    )


def test_all_paths_return_path_objects():
    assert isinstance(betas_path("/d", "s", "ses"), Path)
    assert isinstance(
        session_noise_ceiling_path("/d", "s", "ses"), Path,
    )
    assert isinstance(trialinfo_path("/d", "s", "ses"), Path)
    assert isinstance(brain_mask_path("/d", "s"), Path)
    assert isinstance(
        subject_noise_ceiling_path("/d", "s", "x"), Path,
    )
    assert isinstance(roi_mask_path("/d", "s", "r"), Path)
    assert isinstance(stimuli_dir_path("/d"), Path)
    assert isinstance(stimuli_metadata_path("/d"), Path)
    assert isinstance(participants_tsv_path("/d"), Path)
    assert isinstance(glmsingle_subject_dir("/d", "s"), Path)
    assert isinstance(session_func_dir("/d", "s", "ses"), Path)
