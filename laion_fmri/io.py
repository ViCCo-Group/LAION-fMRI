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


def load_nifti_4d(path, mask_path, streaming=False):
    """Load a 4-D NIfTI's values within a brain mask.

    Returns each volume as a row of voxel values.

    Parameters
    ----------
    path : str or Path
    mask_path : str or Path
    streaming : bool
        If False (default), materialize the full 4-D array up
        front, then mask per volume. Decompresses any ``.nii.gz``
        once and is the right choice for the bucket's compressed
        files; peak memory is the full 4-D file plus the masked
        output, so a real session is ~12 GB. If True, read one
        volume at a time -- peak memory stays at one volume plus
        the masked output. **Streaming is only fast on raw
        uncompressed ``.nii``** (or with the file already in OS
        cache); on ``.nii.gz`` nibabel re-decompresses up to the
        offset on every slice, so streaming becomes effectively
        quadratic in the number of volumes.

    Returns
    -------
    np.ndarray
        Shape ``(n_volumes, n_brain_voxels)``, dtype float32,
        C-contiguous so row indexing is cheap.
    """
    img = nib.load(str(path))
    shape = img.shape
    if len(shape) != 4:
        raise ValueError(
            f"Expected 4-D NIfTI at {path}, got shape {shape}"
        )

    n_volumes = shape[3]
    mask = load_nifti_mask(mask_path)
    n_voxels = int(mask.sum())

    out = np.empty((n_volumes, n_voxels), dtype=np.float32)
    if streaming:
        for t in range(n_volumes):
            vol = np.asarray(img.dataobj[..., t])
            out[t] = vol.ravel()[mask]
    else:
        data = np.asarray(img.dataobj)
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


def load_gifti_mask(path):
    """Load a ``.func.gii`` surface mask as a 1-D boolean array.

    Parameters
    ----------
    path : str or Path

    Returns
    -------
    np.ndarray
        Shape ``(n_vertices,)``, dtype bool.
    """
    img = nib.load(str(path))
    return np.asarray(img.darrays[0].data).astype(bool)


def load_freesurfer_label(path):
    """Load a FreeSurfer ``.label`` file's vertex indices.

    Parameters
    ----------
    path : str or Path

    Returns
    -------
    np.ndarray
        Shape ``(n_label_vertices,)``, dtype int.
    """
    indices = nib.freesurfer.io.read_label(str(path))
    return np.asarray(indices, dtype=int)
