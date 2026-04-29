"""Brain space mapping utilities."""

import nibabel as nib
import numpy as np

from laion_fmri.io import load_nifti_mask


def to_nifti(
    values, output_path, brain_mask_path, affine,
    roi_mask=None, custom_mask=None,
):
    """Map 1D voxel values back to a 3D NIfTI volume.

    Parameters
    ----------
    values : np.ndarray
        1D array of values to place in the volume.
    output_path : str or Path
        Output NIfTI file path.
    brain_mask_path : str or Path
        Path to the brain mask NIfTI.
    affine : np.ndarray
        4x4 affine matrix.
    roi_mask : np.ndarray[bool] or None
        Boolean mask within brain voxels.
    custom_mask : np.ndarray[bool] or None
        Custom boolean mask within brain voxels.

    Raises
    ------
    ValueError
        If values length does not match the expected voxel count.
    """
    brain_mask = load_nifti_mask(brain_mask_path)
    volume_shape = nib.load(str(brain_mask_path)).shape

    # Determine which voxels to fill
    if roi_mask is not None:
        expected_n = int(roi_mask.sum())
    elif custom_mask is not None:
        expected_n = int(custom_mask.sum())
    else:
        expected_n = int(brain_mask.sum())

    if len(values) != expected_n:
        raise ValueError(
            f"Values length mismatch: got {len(values)}, "
            f"expected {expected_n}"
        )

    # Build full-volume flat array
    volume_flat = np.zeros(brain_mask.shape[0], dtype=np.float32)

    brain_indices = np.where(brain_mask)[0]

    if roi_mask is not None:
        selected_brain_indices = brain_indices[roi_mask]
    elif custom_mask is not None:
        selected_brain_indices = brain_indices[custom_mask]
    else:
        selected_brain_indices = brain_indices

    volume_flat[selected_brain_indices] = values

    volume_3d = volume_flat.reshape(volume_shape)
    img = nib.Nifti1Image(volume_3d, affine)
    nib.save(img, str(output_path))


def get_voxel_coordinates(
    brain_mask_path, affine, roi_mask=None, custom_mask=None,
):
    """Compute MNI coordinates for brain voxels.

    Parameters
    ----------
    brain_mask_path : str or Path
        Path to the brain mask NIfTI.
    affine : np.ndarray
        4x4 affine matrix.
    roi_mask : np.ndarray[bool] or None
        Boolean mask within brain voxels.
    custom_mask : np.ndarray[bool] or None
        Custom boolean mask within brain voxels.

    Returns
    -------
    np.ndarray
        Shape (n_voxels, 3) array of coordinates.
    """
    brain_mask = load_nifti_mask(brain_mask_path)
    volume_shape = nib.load(str(brain_mask_path)).shape

    # Get 3D indices of brain voxels
    brain_3d = brain_mask.reshape(volume_shape)
    ijk = np.array(np.where(brain_3d)).T  # (n_brain, 3)

    if roi_mask is not None:
        ijk = ijk[roi_mask]
    elif custom_mask is not None:
        ijk = ijk[custom_mask]

    # Apply affine: coords = affine @ [i, j, k, 1]^T
    ones = np.ones((len(ijk), 1))
    ijk_h = np.hstack([ijk, ones])  # (n, 4)
    coords = (affine @ ijk_h.T).T[:, :3]

    return coords
