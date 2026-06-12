"""Low-level file loaders for laion_fmri."""

import gzip

import nibabel as nib
import numpy as np
import pandas as pd


def load_nifti_mask(path):
    """Load a NIfTI mask as a flat 1-D boolean array.

    Voxels with ``NaN`` are treated as out-of-mask. This matters
    when the source NIfTI is a stat map (e.g. the R^2 file the
    rsquare-derived brain mask is built from): GLMsingle writes
    ``NaN`` at voxels where the model couldn't fit, and
    ``np.nan.astype(bool)`` is ``True`` -- without this guard,
    those failed-fit voxels would leak into every downstream
    voxel-axis accessor.

    Parameters
    ----------
    path : str or Path

    Returns
    -------
    np.ndarray
        Shape ``(n_total_voxels,)``, dtype bool.
    """
    img = nib.load(str(path))
    data = np.asarray(img.dataobj).ravel()
    return np.where(np.isnan(data), False, data).astype(bool)


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


def load_nifti_4d(path, voxel_mask, streaming=False):
    """Load a 4-D NIfTI's values within a voxel mask.

    Returns each volume as a row of voxel values.

    Parameters
    ----------
    path : str or Path
    voxel_mask : np.ndarray
        1-D bool array of length ``X*Y*Z``. Build with
        ``load_nifti_mask`` for a brain-only mask, or combine
        brain + ROI + NC once on the caller side so the streaming
        path can apply the combination inline.
    streaming : bool
        If False (default), materialize the full 4-D array up
        front, then mask per volume. Decompresses any ``.nii.gz``
        once; peak memory is the full 4-D file (~12 GB for a real
        session) plus the masked output. If True, stream the file
        volume-by-volume: for ``.nii.gz`` a custom gzip pipe is
        used so each volume is read sequentially without
        re-decompression, keeping peak memory at one volume plus
        the masked output. For raw ``.nii`` nibabel's per-volume
        slicing is used (cheap, no streaming needed).

    Returns
    -------
    np.ndarray
        Shape ``(n_volumes, n_mask_voxels)``, dtype float32,
        C-contiguous so row indexing is cheap.
    """
    img = nib.load(str(path))
    shape = img.shape
    if len(shape) != 4:
        raise ValueError(
            f"Expected 4-D NIfTI at {path}, got shape {shape}"
        )

    voxel_mask = voxel_mask.astype(bool, copy=False)
    n_volumes = shape[3]
    n_voxels = int(voxel_mask.sum())
    out = np.empty((n_volumes, n_voxels), dtype=np.float32)

    if streaming and str(path).endswith(".gz"):
        _stream_chunked_gz_4d(path, voxel_mask, shape, out)
        return out

    if streaming:
        for t in range(n_volumes):
            vol = np.asarray(img.dataobj[..., t])
            out[t] = vol.ravel()[voxel_mask]
        return out

    data = np.asarray(img.dataobj)
    for t in range(n_volumes):
        out[t] = data[..., t].ravel()[voxel_mask]
    return out


def _stream_chunked_gz_4d(path, voxel_mask, shape, out):
    """Read a gzipped 4-D NIfTI volume-by-volume and mask inline.

    Opens the file with a single ``gzip.open`` stream and reads
    sequentially: the NIfTI-1 header, any extensions/padding up
    to ``vox_offset``, then one volume's worth of bytes per
    iteration. Writes into the preallocated ``out`` array.
    Peak in-flight memory is one volume plus ``out`` itself.
    """
    n_x, n_y, n_z, n_t = shape
    with gzip.open(str(path), "rb") as stream:
        header = nib.Nifti1Header.from_fileobj(stream)
        dtype = header.get_data_dtype()
        vox_offset = int(header["vox_offset"])
        # ``from_fileobj`` may or may not consume the extension
        # flag bytes depending on the nibabel version. Use the
        # actual stream position to skip exactly the remaining
        # padding up to where the data block begins.
        pos = stream.tell()
        if pos < vox_offset:
            stream.read(vox_offset - pos)
        bytes_per_vol = n_x * n_y * n_z * dtype.itemsize
        for t in range(n_t):
            raw = stream.read(bytes_per_vol)
            # NIfTI stores X fastest -- reshape with order='F'
            # to recover the (X, Y, Z) array nibabel would
            # return, then ravel C-order to align with the
            # mask layout used elsewhere in laion_fmri.
            vol = np.frombuffer(raw, dtype=dtype).reshape(
                (n_x, n_y, n_z), order="F",
            )
            out[t] = vol.ravel()[voxel_mask].astype(np.float32)


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
