"""Low-level file loaders for laion_fmri."""

import nibabel as nib
import numpy as np
import pandas as pd


def load_nifti_mask(path):
    """Load a NIfTI mask as a flat 1-D boolean array.

    Parameters
    ----------
    path : str or Path

    Returns
    -------
    np.ndarray
        Shape ``(n_total_voxels,)``, dtype bool.
    """
    img = nib.load(str(path))
    data = np.asarray(img.dataobj)
    return data.ravel().astype(bool)


def load_nifti_data(path, mask_path):
    """Load a 3-D NIfTI's values within a brain mask.

    Parameters
    ----------
    path : str or Path
    mask_path : str or Path

    Returns
    -------
    np.ndarray
        Shape ``(n_brain_voxels,)``, dtype float32.
    """
    img = nib.load(str(path))
    data = np.asarray(img.dataobj, dtype=np.float32).ravel()
    mask = load_nifti_mask(mask_path)
    return data[mask]


def load_nifti_4d(path, mask_path):
    """Load a 4-D NIfTI's values within a brain mask.

    Returns each volume as a row of voxel values.

    Streams the data one volume at a time so the masking step
    runs against a Fortran-contiguous 3-D slab rather than against
    a strided 4-D reshape. NIfTI files are F-contiguous on disk;
    a single ``flat[mask]`` over the full 4-D would force ~50k
    cache-cold gathers across several GB of memory and is orders
    of magnitude slower than the per-volume loop.

    Parameters
    ----------
    path : str or Path
    mask_path : str or Path

    Returns
    -------
    np.ndarray
        Shape ``(n_volumes, n_brain_voxels)``, dtype float32,
        C-contiguous so row indexing is cheap.
    """
    img = nib.load(str(path))
    data = np.asarray(img.dataobj)
    if data.ndim != 4:
        raise ValueError(
            f"Expected 4-D NIfTI at {path}, got shape {data.shape}"
        )

    n_volumes = data.shape[3]
    mask = load_nifti_mask(mask_path)
    n_voxels = int(mask.sum())

    out = np.empty((n_volumes, n_voxels), dtype=np.float32)
    for t in range(n_volumes):
        out[t] = data[..., t].ravel()[mask]
    return out


def load_nifti_with_affine(path):
    """Load a NIfTI's data and 4×4 affine.

    Parameters
    ----------
    path : str or Path

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
    """
    img = nib.load(str(path))
    data = np.asarray(img.dataobj)
    affine = np.array(img.affine)
    return data, affine


def load_tsv(path):
    """Load a TSV file as a pandas DataFrame.

    Parameters
    ----------
    path : str or Path

    Returns
    -------
    pd.DataFrame
    """
    return pd.read_csv(str(path), sep="\t")
