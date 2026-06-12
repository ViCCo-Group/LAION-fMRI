import tracemalloc

import nibabel as nib
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
    """Path to the file the loader uses to derive the brain mask."""
    return (
        synthetic_data_dir / "derivatives" / "glmsingle-tedana"
        / sub
        / f"{sub}_task-images_space-T1w_"
        f"stat-rsquare_desc-R2mean_statmap.nii.gz"
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


def test_load_nifti_mask_excludes_nan(tmp_path):
    """A NaN-bearing source NIfTI (e.g. an R2mean file with
    failed GLMsingle voxels) must not leak NaN voxels into the
    boolean brain mask. ``bool(np.nan)`` is ``True``, so a naive
    ``.astype(bool)`` would incorrectly mark them as in-brain.
    """
    import nibabel as nib

    arr = np.zeros((4, 4, 4), dtype=np.float32)
    arr[1, 1, 1] = 0.5     # in-brain (non-zero R2)
    arr[2, 2, 2] = np.nan  # GLMsingle failed here -- not in brain
    img = nib.Nifti1Image(arr, np.eye(4))
    p = tmp_path / "nan_mask.nii.gz"
    nib.save(img, str(p))

    mask = load_nifti_mask(p)
    flat = arr.ravel()
    nan_idx = np.where(np.isnan(flat))[0][0]
    finite_idx = np.where(flat == 0.5)[0][0]
    assert mask[finite_idx] is np.True_ or mask[finite_idx]
    assert not mask[nan_idx]
    assert mask.sum() == 1


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
    brain_mask = load_nifti_mask(mask_path)
    betas = load_nifti_4d(betas_path, brain_mask)
    assert betas.shape == (N_TRIALS_PER_SESSION, N_BRAIN_VOXELS)
    assert betas.dtype == np.float32


def test_load_nifti_4d_rejects_3d(synthetic_data_dir):
    """Loading a 3-D NIfTI through the 4-D loader is an error."""
    nc_path = _session_nc_file(
        synthetic_data_dir, "sub-01", "ses-01",
    )
    mask_path = _brain_mask_file(synthetic_data_dir, "sub-01")
    brain_mask = load_nifti_mask(mask_path)
    with pytest.raises(ValueError, match="4-D"):
        load_nifti_4d(nc_path, brain_mask)


def test_load_nifti_4d_bulk_matches_streaming(synthetic_data_dir):
    """Bulk and streaming modes return identical arrays."""
    betas_path = _trial_betas_file(
        synthetic_data_dir, "sub-01", "ses-01",
    )
    mask_path = _brain_mask_file(synthetic_data_dir, "sub-01")
    brain_mask = load_nifti_mask(mask_path)
    streamed = load_nifti_4d(betas_path, brain_mask, streaming=True)
    bulk = load_nifti_4d(betas_path, brain_mask, streaming=False)
    np.testing.assert_array_equal(streamed, bulk)


def test_load_nifti_4d_default_is_streaming(synthetic_data_dir):
    """Calling without ``streaming=`` matches ``streaming=True``."""
    betas_path = _trial_betas_file(
        synthetic_data_dir, "sub-01", "ses-01",
    )
    mask_path = _brain_mask_file(synthetic_data_dir, "sub-01")
    brain_mask = load_nifti_mask(mask_path)
    default = load_nifti_4d(betas_path, brain_mask)
    streamed = load_nifti_4d(betas_path, brain_mask, streaming=True)
    np.testing.assert_array_equal(default, streamed)


def _strict_subset_mask(brain_mask, fraction=0.5):
    """Return a bool mask that keeps the first ``fraction`` of brain voxels."""
    n_keep = int(brain_mask.sum() * fraction)
    out = np.zeros_like(brain_mask)
    out[np.flatnonzero(brain_mask)[:n_keep]] = True
    return out


def test_load_nifti_4d_bulk_accepts_voxel_mask_array(
    synthetic_data_dir,
):
    """Bulk-load path must accept a precomputed bool voxel mask so
    callers can combine brain + ROI + NC inline, avoiding the
    brain-only intermediate.
    """
    betas_path = _trial_betas_file(
        synthetic_data_dir, "sub-01", "ses-01",
    )
    mask_path = _brain_mask_file(synthetic_data_dir, "sub-01")
    brain_mask = load_nifti_mask(mask_path)
    voxel_mask = _strict_subset_mask(brain_mask, fraction=0.5)

    out = load_nifti_4d(betas_path, voxel_mask, streaming=False)
    assert out.shape == (
        N_TRIALS_PER_SESSION, int(voxel_mask.sum()),
    )
    assert out.dtype == np.float32


def test_load_nifti_4d_streaming_accepts_voxel_mask_array(
    synthetic_data_dir,
):
    """Same as above, but for the chunked-gzip streaming path."""
    betas_path = _trial_betas_file(
        synthetic_data_dir, "sub-01", "ses-01",
    )
    mask_path = _brain_mask_file(synthetic_data_dir, "sub-01")
    brain_mask = load_nifti_mask(mask_path)
    voxel_mask = _strict_subset_mask(brain_mask, fraction=0.5)

    out = load_nifti_4d(betas_path, voxel_mask, streaming=True)
    assert out.shape == (
        N_TRIALS_PER_SESSION, int(voxel_mask.sum()),
    )
    assert out.dtype == np.float32


def test_load_nifti_4d_streaming_matches_bulk_with_voxel_mask(
    synthetic_data_dir,
):
    """The chunked-gzip path must produce the same array as the
    bulk-load path, bit-for-bit, when both are given the same
    combined mask.
    """
    betas_path = _trial_betas_file(
        synthetic_data_dir, "sub-01", "ses-01",
    )
    mask_path = _brain_mask_file(synthetic_data_dir, "sub-01")
    brain_mask = load_nifti_mask(mask_path)
    voxel_mask = _strict_subset_mask(brain_mask, fraction=0.3)

    streamed = load_nifti_4d(betas_path, voxel_mask, streaming=True)
    bulk = load_nifti_4d(betas_path, voxel_mask, streaming=False)
    np.testing.assert_array_equal(streamed, bulk)


def test_load_nifti_4d_streaming_peak_memory_bounded(tmp_path):
    """The chunked-gzip path's peak memory must be a small
    fraction of the bulk-load peak. Without this guarantee the
    streaming flag would just be cosmetic on ``.nii.gz``.

    The shared synthetic fixture (5x5x5x60) is too small to make
    the difference visible -- both paths would fit in a few KB
    of overhead -- so this test builds its own ~22 MB ``.nii.gz``
    in ``tmp_path`` for a meaningful comparison.
    """
    n_x, n_y, n_z = 30, 30, 30
    n_t = 200
    rng = np.random.default_rng(0)
    data = rng.standard_normal(
        (n_x, n_y, n_z, n_t),
    ).astype(np.float32)
    brain = (
        rng.uniform(size=(n_x, n_y, n_z)) > 0.5
    ).astype(np.float32)

    betas_path = tmp_path / "betas.nii.gz"
    nib.save(nib.Nifti1Image(data, np.eye(4)), str(betas_path))
    voxel_mask = brain.ravel().astype(bool)

    tracemalloc.start()
    bulk = load_nifti_4d(betas_path, voxel_mask, streaming=False)
    _, bulk_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    streamed = load_nifti_4d(betas_path, voxel_mask, streaming=True)
    _, stream_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    np.testing.assert_array_equal(bulk, streamed)
    # Bulk peak includes the full 4-D (~22 MB) + the masked
    # output. Streaming peak is one volume (~108 KB) + the
    # same masked output. If a future change accidentally
    # materializes the full 4-D in the streaming path, this
    # assertion catches it.
    assert stream_peak * 2 < bulk_peak, (
        f"streaming peak {stream_peak} bytes is not meaningfully "
        f"smaller than bulk peak {bulk_peak} bytes"
    )


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
