import nibabel as nib
import numpy as np
import pytest

from laion_fmri._paths import brain_mask_path, roi_mask_path
from laion_fmri.brain import get_voxel_coordinates, to_nifti
from laion_fmri.io import load_nifti_mask
from tests.conftest import (
    BRAIN_SHAPE,
    N_BRAIN_VOXELS,
    N_HLVIS_VOXELS,
)


def _mask_path(synthetic_data_dir):
    return str(brain_mask_path(synthetic_data_dir, "sub-01"))


def _roi_within_brain(synthetic_data_dir, roi_name):
    brain = load_nifti_mask(_mask_path(synthetic_data_dir))
    full = load_nifti_mask(
        str(roi_mask_path(synthetic_data_dir, "sub-01", roi_name))
    )
    return full[brain]


def test_to_nifti_creates_file(synthetic_data_dir, tmp_path):
    affine = np.eye(4)
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)

    out_path = tmp_path / "output.nii.gz"
    to_nifti(
        values, str(out_path),
        _mask_path(synthetic_data_dir), affine,
    )
    assert out_path.exists()


def test_to_nifti_shape(synthetic_data_dir, tmp_path):
    affine = np.eye(4)
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)

    out_path = tmp_path / "output.nii.gz"
    to_nifti(
        values, str(out_path),
        _mask_path(synthetic_data_dir), affine,
    )

    img = nib.load(str(out_path))
    assert img.shape == BRAIN_SHAPE


def test_to_nifti_with_roi_mask(synthetic_data_dir, tmp_path):
    roi_mask = _roi_within_brain(synthetic_data_dir, "hlvis")
    affine = np.eye(4)
    values = np.ones(N_HLVIS_VOXELS, dtype=np.float32) * 5.0

    out_path = tmp_path / "roi_output.nii.gz"
    to_nifti(
        values, str(out_path),
        _mask_path(synthetic_data_dir), affine, roi_mask=roi_mask,
    )

    img = nib.load(str(out_path))
    data = np.asarray(img.dataobj)
    assert data.shape == BRAIN_SHAPE
    assert np.any(data == 5.0)


def test_to_nifti_wrong_size_raises(synthetic_data_dir, tmp_path):
    affine = np.eye(4)
    values = np.ones(10, dtype=np.float32)  # wrong size

    out_path = tmp_path / "bad.nii.gz"
    with pytest.raises(ValueError, match="mismatch"):
        to_nifti(
            values, str(out_path),
            _mask_path(synthetic_data_dir), affine,
        )


def test_get_voxel_coordinates_shape(synthetic_data_dir):
    coords = get_voxel_coordinates(
        _mask_path(synthetic_data_dir), np.eye(4),
    )
    assert coords.shape == (N_BRAIN_VOXELS, 3)


def test_get_voxel_coordinates_with_roi(synthetic_data_dir):
    roi_mask = _roi_within_brain(synthetic_data_dir, "hlvis")
    coords = get_voxel_coordinates(
        _mask_path(synthetic_data_dir),
        np.eye(4),
        roi_mask=roi_mask,
    )
    assert coords.shape == (N_HLVIS_VOXELS, 3)
