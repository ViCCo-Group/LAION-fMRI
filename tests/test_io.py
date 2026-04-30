import numpy as np
import pandas as pd
import pytest

from laion_fmri.io import (
    load_nifti_4d,
    load_nifti_data,
    load_nifti_mask,
    load_nifti_with_affine,
    load_tsv,
)
from tests.conftest import (
    N_BRAIN_VOXELS,
    N_TRIALS_PER_SESSION,
)


def _brain_mask_file(synthetic_data_dir, sub):
    return (
        synthetic_data_dir / "derivatives" / "glmsingle-tedana"
        / sub
        / f"{sub}_task-images_space-T1w_"
        f"desc-meanR2gt15mask_mask.nii.gz"
    )


def _trial_betas_file(synthetic_data_dir, sub, ses):
    return (
        synthetic_data_dir / "derivatives" / "glmsingle-tedana"
        / sub / ses / "func"
        / f"{sub}_{ses}_task-images_space-T1w_stat-effect_"
        f"desc-SingletrialBetas_statmap.nii.gz"
    )


def _session_nc_file(synthetic_data_dir, sub, ses):
    return (
        synthetic_data_dir / "derivatives" / "glmsingle-tedana"
        / sub / ses / "func"
        / f"{sub}_{ses}_task-images_space-T1w_"
        f"desc-Noiseceiling_statmap.nii.gz"
    )


def _events_file(synthetic_data_dir, sub, ses):
    return (
        synthetic_data_dir / "derivatives" / "glmsingle-tedana"
        / sub / ses / "func"
        / f"{sub}_{ses}_task-images_"
        f"desc-SingletrialBetas_trials.tsv"
    )


# ── load_nifti_mask ────────────────────────────────────────────


def test_load_nifti_mask_returns_bool(synthetic_data_dir):
    mask_path = _brain_mask_file(synthetic_data_dir, "sub-01")
    mask = load_nifti_mask(mask_path)
    assert isinstance(mask, np.ndarray)
    assert mask.dtype == bool
    assert mask.ndim == 1
    assert mask.sum() == N_BRAIN_VOXELS


# ── load_nifti_data (3-D within mask) ───────────────────────────


def test_load_nifti_data_returns_brain_voxels(synthetic_data_dir):
    nc_path = _session_nc_file(
        synthetic_data_dir, "sub-01", "ses-01",
    )
    mask_path = _brain_mask_file(synthetic_data_dir, "sub-01")
    data = load_nifti_data(nc_path, mask_path)
    assert isinstance(data, np.ndarray)
    assert np.issubdtype(data.dtype, np.floating)
    assert data.shape == (N_BRAIN_VOXELS,)


# ── load_nifti_4d (single-trial betas) ──────────────────────────


def test_load_nifti_4d_shape(synthetic_data_dir):
    betas_path = _trial_betas_file(
        synthetic_data_dir, "sub-01", "ses-01",
    )
    mask_path = _brain_mask_file(synthetic_data_dir, "sub-01")
    betas = load_nifti_4d(betas_path, mask_path)
    assert betas.shape == (N_TRIALS_PER_SESSION, N_BRAIN_VOXELS)
    assert betas.dtype == np.float32


def test_load_nifti_4d_rejects_3d(synthetic_data_dir):
    """Loading a 3-D NIfTI through the 4-D loader is an error."""
    nc_path = _session_nc_file(
        synthetic_data_dir, "sub-01", "ses-01",
    )
    mask_path = _brain_mask_file(synthetic_data_dir, "sub-01")
    with pytest.raises(ValueError, match="4-D"):
        load_nifti_4d(nc_path, mask_path)


# ── load_nifti_with_affine ──────────────────────────────────────


def test_load_nifti_with_affine(synthetic_data_dir):
    mask_path = _brain_mask_file(synthetic_data_dir, "sub-01")
    data, affine = load_nifti_with_affine(mask_path)
    assert isinstance(data, np.ndarray)
    assert isinstance(affine, np.ndarray)
    assert affine.shape == (4, 4)


# ── load_tsv ────────────────────────────────────────────────────


def test_load_tsv_events(synthetic_data_dir):
    tsv = _events_file(synthetic_data_dir, "sub-01", "ses-01")
    df = load_tsv(tsv)
    assert isinstance(df, pd.DataFrame)
    assert "stimulus_id" in df.columns
    assert "session" in df.columns
    assert len(df) == N_TRIALS_PER_SESSION


def test_load_tsv_participants(synthetic_data_dir):
    tsv = synthetic_data_dir / "participants.tsv"
    df = load_tsv(tsv)
    assert "participant_id" in df.columns
    assert len(df) == 2
