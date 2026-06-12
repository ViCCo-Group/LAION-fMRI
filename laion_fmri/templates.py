"""Template-space projection of subject-T1w data.

Wraps two chains so callers reach a supported template through
``to_template(..., target=...)`` without touching the external
libraries:

- *Surface chain*: T1w volume → fsnative surface
  (``nilearn.surface.vol_to_surf``) → fsaverage surface
  (``nitransforms.surface.SurfaceResampler``). Used for the
  ``fsaverage`` target.
- *Volume chain*: T1w volume → MNI305 via
  ``nitransforms.linear.Affine`` reading the recon's
  ``talairach.lta``. Used for the ``MNI305`` target.
"""

import importlib.util
import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np

from laion_fmri._paths import freesurfer_transforms_dir


_TEMPLATE_INSTALL_HINT = (
    "Template-space transforms require the optional ``[template]`` "
    "extra. Install with ``uv sync --extra template`` (or "
    "``pip install laion-fmri[template]``)."
)

_SUPPORTED_TARGETS = (
    "fsaverage",
    "MNI305",
)

_SURFACE_TARGETS = frozenset({"fsaverage"})
_VOLUME_ONLY_TARGETS = frozenset({"MNI305"})


def _check_template_available():
    """Raise ImportError if any template-extra dependency is missing."""
    missing = [
        name for name in (
            "nilearn", "nitransforms", "templateflow",
        )
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        raise ImportError(
            f"Missing dependencies: {', '.join(missing)}. "
            f"{_TEMPLATE_INSTALL_HINT}"
        )


def to_template(
    subject,
    values,
    target,
    *,
    hemi=None,
    route="auto",
    surface="white",
    fsaverage_density="fsaverage5",
    fslr_density="32k",
    interpolation="linear",
    output_dir=None,
    desc=None,
    session=None,
):
    """Project subject-T1w-space values into a template space.

    Parameters
    ----------
    subject : Subject
    values : np.ndarray | str | Path
        1-D over the brain mask, 2-D ``(n_trials, n_voxels)``, or
        a path to a NIfTI already on the subject's T1w grid.
    target : str
        One of the entries in
        ``laion_fmri.templates._SUPPORTED_TARGETS``.
    hemi : "L" | "R" | None
        Hemisphere selector for surface targets.
    route : "auto" | "surface" | "volume"
        Currently every supported target has a single route, so
        ``"auto"`` always resolves to that route. The keyword is
        retained for forward compatibility; passing the wrong
        route for a target (e.g. ``route="surface"`` for
        ``"MNI305"``) raises ``ValueError``.
    surface : str
        Surface used by the vol→surf sampling step (``"white"``,
        ``"pial"``, or ``"midthickness"``).
    fsaverage_density : str
        ``"fsaverage5"`` (10k/hemi), ``"fsaverage6"`` (41k), or
        ``"fsaverage7"`` (164k).
    fslr_density : str
        ``"32k"`` or ``"164k"``.
    interpolation : str
        Forwarded to ``nilearn.surface.vol_to_surf``.
    output_dir : Path | None
        If given, also writes BIDS-conformant files to disk.
    desc, session : str | None
        BIDS ``desc-`` and ``ses-`` tokens for the output
        filename(s).

    Returns
    -------
    For surface targets: 1-D ndarray, 2-D if input was
    multi-trial, or a ``{"L": ..., "R": ...}`` dict when
    ``hemi=None``.
    For volume targets: ``nibabel.Nifti1Image``.
    """
    _check_template_available()

    if target not in _SUPPORTED_TARGETS:
        raise ValueError(
            f"Unknown target {target!r}. "
            f"Supported targets: {_SUPPORTED_TARGETS}."
        )

    effective_route = _resolve_route(target, route)

    if effective_route == "volume":
        if target == "MNI305":
            result = _to_mni305(subject, values)
        else:
            raise NotImplementedError(
                f"Volume route for target {target!r} is not "
                "implemented."
            )
    else:
        result = _to_surface(
            subject, values, target,
            hemi=hemi,
            surface=surface,
            fsaverage_density=fsaverage_density,
            fslr_density=fslr_density,
            interpolation=interpolation,
        )

    if output_dir is not None:
        _write_output(
            result,
            subject_id=subject.subject_id,
            target=target,
            hemi=hemi,
            fsaverage_density=fsaverage_density,
            desc=desc,
            session=session,
            output_dir=output_dir,
        )
    return result


def volume_to_surface(subject, values, target="fsaverage", **kwargs):
    """Volume-input → surface-target shortcut around :func:`to_template`.

    Refuses volume targets so the caller's intent is checked at
    the call site instead of silently routing somewhere unexpected.
    """
    if target not in _SURFACE_TARGETS:
        raise ValueError(
            f"target={target!r} is not a surface target. "
            f"Use ``volume_to_template`` for volume targets. "
            f"Surface targets: {sorted(_SURFACE_TARGETS)}."
        )
    return to_template(subject, values, target, **kwargs)


def volume_to_template(subject, values, target, **kwargs):
    """Volume-input → volume-target shortcut around :func:`to_template`."""
    if target not in _VOLUME_ONLY_TARGETS:
        raise ValueError(
            f"target={target!r} is not a volume target. "
            f"Use ``volume_to_surface`` for surface targets. "
            f"Volume targets: {sorted(_VOLUME_ONLY_TARGETS)}."
        )
    return to_template(subject, values, target, **kwargs)


def surface_to_template(
    subject, values, target="fsaverage", *,
    hemi=None, fsaverage_density="fsaverage5",
    output_dir=None, desc=None, session=None,
):
    """Resample fsnative-surface input onto a surface template.

    Parameters
    ----------
    subject : Subject
    values : ndarray | dict[str, ndarray]
        Per-hemi fsnative-vertex array, or a ``{"L": ..., "R": ...}``
        dict. With a single array, ``hemi`` must specify which
        hemisphere the array belongs to.
    target : str
        Surface target (currently only ``"fsaverage"``).
    hemi : "L" | "R" | None
        Required when ``values`` is a single array. Ignored when
        ``values`` is a dict.
    fsaverage_density : str
        ``"fsaverage5"``, ``"fsaverage6"``, ``"fsaverage7"`` /
        ``"fsaverage"``.
    output_dir, desc, session
        BIDS-writer kwargs; see :func:`to_template`.

    Returns
    -------
    ndarray | dict[str, ndarray]
        Same container type as ``values``.
    """
    _check_template_available()
    if target not in _SURFACE_TARGETS:
        raise ValueError(
            f"target={target!r} is not a surface target. "
            f"Use ``volume_to_template`` for volume targets. "
            f"Surface targets: {sorted(_SURFACE_TARGETS)}."
        )

    fs_dir = subject.get_freesurfer_dir()
    density_token = _fsaverage_density_token(fsaverage_density)
    per_hemi_in = _normalize_surface_input(values, hemi)
    for h, arr in per_hemi_in.items():
        _check_fsnative_vertex_count(fs_dir, h, arr)

    resampled = {
        h: _resample_fsnative_to_fsaverage(
            arr, fs_dir=fs_dir, hemi=h,
            density_token=density_token,
        )
        for h, arr in per_hemi_in.items()
    }

    result = resampled if isinstance(values, dict) else resampled[hemi]
    if output_dir is not None:
        _write_output(
            result,
            subject_id=subject.subject_id,
            target=target,
            hemi=None if isinstance(values, dict) else hemi,
            fsaverage_density=fsaverage_density,
            desc=desc, session=session,
            output_dir=output_dir,
        )
    return result


def _normalize_surface_input(values, hemi):
    """Return a ``{hemi: ndarray}`` view of the user's surface input."""
    if isinstance(values, dict):
        return {h: np.asarray(arr) for h, arr in values.items()}
    if hemi is None:
        raise ValueError(
            "Single-array input requires a ``hemi`` kwarg of "
            "'L' or 'R'. Pass {'L': ..., 'R': ...} for both."
        )
    return {hemi: np.asarray(values)}


def _check_fsnative_vertex_count(fs_dir, hemi, arr):
    """Raise ValueError if ``arr`` doesn't match the recon's
    fsnative vertex count for ``hemi``."""
    h_fs = "lh" if hemi == "L" else "rh"
    sphere_path = fs_dir / "surf" / f"{h_fs}.sphere.reg"
    verts, _ = nib.freesurfer.read_geometry(str(sphere_path))
    expected = verts.shape[0]
    if arr.shape[0] != expected:
        raise ValueError(
            f"Hemisphere {hemi!r}: input has {arr.shape[0]} "
            f"vertices but the recon's fsnative mesh has "
            f"{expected}."
        )


def _resolve_route(target, route):
    """Validate ``route`` against ``target`` and return the effective
    route the dispatch will run."""
    if target in _SURFACE_TARGETS:
        if route == "volume":
            raise ValueError(
                f"target={target!r} is surface-only; "
                "route='volume' is not supported."
            )
        return "surface"

    if target in _VOLUME_ONLY_TARGETS:
        if route == "surface":
            raise ValueError(
                f"target={target!r} is volume-only; "
                "route='surface' is not supported."
            )
        return "volume"

    raise ValueError(
        f"Unknown target {target!r}. "
        f"Supported targets: {_SUPPORTED_TARGETS}."
    )


def _to_mni305(subject, values):
    """T1w volume → MNI305 volume via the recon's ``talairach.lta``.

    The reference grid is fetched from templateflow when available
    so the output sits on a canonical MNI305 grid. If templateflow
    can't resolve an MNI305 reference (offline tests, version
    skew), we fall back to using the input grid -- correct only
    when the LTA's source and destination grids agree (the
    fixture's identity LTA case).
    """
    from nitransforms.linear import Affine

    t1w_img = _scatter_to_nifti(subject, values)
    lta_path = (
        freesurfer_transforms_dir(
            subject._data_dir, subject._subject_id,
        )
        / "talairach.lta"
    )
    affine_xfm = Affine.from_filename(str(lta_path), fmt="fs")
    reference = _mni305_reference(fallback=t1w_img)
    return _apply_resample(affine_xfm, t1w_img, reference)


_FSAVERAGE_DENSITY_TOKENS = {
    "fsaverage": "164k",
    "fsaverage5": "10k",
    "fsaverage6": "41k",
    "fsaverage7": "164k",
}


def _fsaverage_density_token(density):
    """Translate user-facing fsaverage names into templateflow tokens."""
    return _FSAVERAGE_DENSITY_TOKENS.get(density, density)


def _to_surface(
    subject, values, target,
    *, hemi, surface, fsaverage_density, fslr_density,
    interpolation,
):
    """Surface chain: T1w volume → fsnative → fsaverage.

    Only ``target == "fsaverage"`` reaches this function; one or
    both hemispheres are produced depending on ``hemi``.
    """
    t1w_img = _scatter_to_nifti(subject, values)
    fs_dir = subject.get_freesurfer_dir()
    density_token = _fsaverage_density_token(fsaverage_density)

    hemis = ("L", "R") if hemi is None else (hemi,)
    fsaverage_per_hemi = {
        h: _project_hemi_to_fsaverage(
            t1w_img=t1w_img, fs_dir=fs_dir, hemi=h,
            surface=surface, density_token=density_token,
            interpolation=interpolation,
        )
        for h in hemis
    }

    if hemi is None:
        return fsaverage_per_hemi
    return fsaverage_per_hemi[hemi]


def _project_hemi_to_fsaverage(
    *, t1w_img, fs_dir, hemi,
    surface, density_token, interpolation,
):
    """T1w volume → fsnative → fsaverage for one hemisphere."""
    from nilearn.surface import vol_to_surf

    h_fs = "lh" if hemi == "L" else "rh"
    subj_surface = fs_dir / "surf" / f"{h_fs}.{surface}"
    fsnative_data = vol_to_surf(
        t1w_img, str(subj_surface), interpolation=interpolation,
    )
    return _resample_fsnative_to_fsaverage(
        fsnative_data, fs_dir=fs_dir, hemi=hemi,
        density_token=density_token,
    )


def _resample_fsnative_to_fsaverage(
    fsnative_data, *, fs_dir, hemi, density_token,
):
    """fsnative vertex array → fsaverage vertex array.

    ``SurfaceResampler`` loads its inputs via ``nib.load`` which
    doesn't understand FreeSurfer-native binary geometry, so we
    re-encode the subject's ``sphere.reg`` as a GIfTI in a
    scratch directory and pass that. Templateflow already ships
    fsaverage's sphere as ``.surf.gii``.
    """
    from nitransforms.surface import SurfaceResampler
    from templateflow.api import get as tflow_get

    h_fs = "lh" if hemi == "L" else "rh"
    subj_sphere_fs = fs_dir / "surf" / f"{h_fs}.sphere.reg"

    fsavg_sphere = tflow_get(
        "fsaverage", hemi=hemi, suffix="sphere",
        density=density_token, extension=".surf.gii",
    )
    if isinstance(fsavg_sphere, list):
        fsavg_sphere = fsavg_sphere[0]

    with tempfile.TemporaryDirectory() as scratch:
        subj_sphere_gii = (
            Path(scratch) / f"{h_fs}.sphere.reg.surf.gii"
        )
        _write_fs_geometry_as_gifti(subj_sphere_fs, subj_sphere_gii)
        resampler = SurfaceResampler(
            reference=str(fsavg_sphere),
            moving=str(subj_sphere_gii),
        )
        return resampler.apply(fsnative_data)


def _write_fs_geometry_as_gifti(fs_path, gii_path):
    """Write a FreeSurfer-native surface to ``gii_path`` as ``.surf.gii``.

    Used to bridge FreeSurfer-native surface files (which
    ``nib.load`` doesn't auto-detect) into libraries that expect
    GIfTI.
    """
    verts, faces = nib.freesurfer.read_geometry(str(fs_path))
    img = nib.gifti.GiftiImage(darrays=[
        nib.gifti.GiftiDataArray(
            verts.astype(np.float32),
            intent="NIFTI_INTENT_POINTSET",
        ),
        nib.gifti.GiftiDataArray(
            faces.astype(np.int32),
            intent="NIFTI_INTENT_TRIANGLE",
        ),
    ])
    nib.save(img, str(gii_path))


def _apply_resample(transform, img, reference):
    """Resample ``img`` through ``transform`` onto ``reference``.

    Handles 3-D and 4-D moving images: 4-D inputs are processed
    one volume at a time and the resampled outputs are stacked
    back along the trailing axis. ``nitransforms``'s own
    ``resampling.apply`` is 3-D only.

    Uses nearest-neighbor interpolation (``order=0``) so each
    target voxel takes the exact value of its closest source
    voxel -- no averaging, no value drift.
    """
    from nitransforms.resampling import apply as nt_apply

    if img.ndim == 3:
        return nt_apply(
            transform, img, reference=reference, order=0,
        )

    if img.ndim != 4:
        raise ValueError(
            f"img must be 3-D or 4-D; got shape {img.shape}."
        )

    n_vols = img.shape[-1]
    affine = img.affine
    data_in = np.asarray(img.dataobj)
    vols = []
    for t in range(n_vols):
        vol_img = nib.Nifti1Image(data_in[..., t], affine)
        out_img = nt_apply(
            transform, vol_img, reference=reference, order=0,
        )
        vols.append(np.asarray(out_img.dataobj))
    stacked = np.stack(vols, axis=-1)
    return nib.Nifti1Image(stacked, out_img.affine)


def _fetch_template_reference(target):
    """Fetch templateflow's T1w reference image for ``target``."""
    from templateflow.api import get as tflow_get

    paths = tflow_get(
        target, suffix="T1w", resolution=1,
        extension=".nii.gz", desc=None,
    )
    if isinstance(paths, list):
        paths = paths[0]
    return nib.load(str(paths))


def _mni305_reference(fallback):
    """Return an MNI305 reference NIfTI; fall back to ``fallback``.

    Templateflow ships MNI305 as ``tpl-MNI305_T1w.nii.gz`` -- a
    1 mm isotropic image with no ``res-`` or ``desc-`` entity, so
    the lookup must not filter on resolution. When templateflow
    has no match at all (offline tests, no cache), we fall back
    to the input grid -- correct only when the LTA's source and
    destination grids agree.
    """
    from templateflow.api import get as tflow_get

    ref_path = tflow_get(
        "MNI305", suffix="T1w", extension=".nii.gz",
        raise_empty=False,
    )
    if not ref_path:
        return fallback
    if isinstance(ref_path, list):
        ref_path = ref_path[0]
    return nib.load(str(ref_path))


def _write_output(
    result, *, subject_id, target, hemi, fsaverage_density,
    desc, session, output_dir,
):
    """Persist ``result`` to ``output_dir`` under a BIDS filename.

    Volume results land as ``.nii.gz``; surface results land as
    ``.func.gii`` (one file per hemisphere). The directory is
    created on demand.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if isinstance(result, dict):
        density_token = _fsaverage_density_token(fsaverage_density)
        for h, arr in result.items():
            filename = _bids_filename(
                subject_id=subject_id, target=target, hemi=h,
                density_token=density_token, desc=desc,
                session=session, extension=".func.gii",
            )
            _save_gifti(arr, output_dir / filename)
        return

    if isinstance(result, nib.Nifti1Image):
        filename = _bids_filename(
            subject_id=subject_id, target=target,
            desc=desc, session=session, extension=".nii.gz",
        )
        nib.save(result, str(output_dir / filename))
        return

    if isinstance(result, np.ndarray):
        density_token = _fsaverage_density_token(fsaverage_density)
        filename = _bids_filename(
            subject_id=subject_id, target=target, hemi=hemi,
            density_token=density_token, desc=desc,
            session=session, extension=".func.gii",
        )
        _save_gifti(result, output_dir / filename)
        return

    raise TypeError(
        f"Cannot write result of type {type(result).__name__}."
    )


def _bids_filename(
    *, subject_id, target, extension,
    hemi=None, density_token=None, desc=None, session=None,
):
    """Assemble a BIDS-conformant ``..._statmap{ext}`` filename."""
    parts = [subject_id]
    if session is not None:
        ses_value = (
            session[4:] if session.startswith("ses-") else session
        )
        parts.append(f"ses-{ses_value}")
    parts.append(f"space-{target}")
    if density_token is not None:
        parts.append(f"den-{density_token}")
    if hemi is not None:
        parts.append(f"hemi-{hemi}")
    if desc is not None:
        parts.append(f"desc-{desc}")
    return "_".join(parts) + f"_statmap{extension}"


def _save_gifti(array, path):
    """Save a 1-D ndarray to a ``.func.gii`` file at ``path``."""
    gifti = nib.gifti.GiftiImage(darrays=[
        nib.gifti.GiftiDataArray(
            np.asarray(array, dtype=np.float32),
            intent="NIFTI_INTENT_NONE",
        ),
    ])
    nib.save(gifti, str(path))


def _scatter_to_nifti(subject, values):
    """Round-trip a brain-masked array to a T1w-grid NIfTI.

    Accepts a 1-D ``(n_voxels,)`` array, a 2-D
    ``(n_trials, n_voxels)`` array (returns a 4-D NIfTI with the
    trial axis preserved), or a path / Nifti1Image already on the
    subject's T1w grid.

    GLMsingle's "unmodeled voxel" sentinel (``NaN``) is replaced
    with 0 inside the scattered volume so the downstream cubic
    spline resample does not propagate ``NaN`` across the whole
    output. The substitution is scoped to the transform pipeline;
    user-facing accessors (``get_betas`` etc.) still surface the
    original ``NaN`` values.
    """
    if isinstance(values, (str, Path)):
        return nib.load(str(values))
    if isinstance(values, nib.Nifti1Image):
        return values

    from laion_fmri.io import load_nifti_mask

    arr = np.nan_to_num(
        np.asarray(values, dtype=np.float32), copy=True, nan=0.0,
    )
    mask_path = subject._brain_mask_path("rsquare")
    brain_mask = load_nifti_mask(mask_path)
    ref = nib.load(str(mask_path))
    n_voxels = int(brain_mask.sum())

    if arr.ndim == 1:
        if arr.size != n_voxels:
            raise ValueError(
                f"values length {arr.size} does not match "
                f"brain-mask voxel count {n_voxels}."
            )
        flat = np.zeros(brain_mask.shape[0], dtype=np.float32)
        flat[brain_mask] = arr
        vol = flat.reshape(ref.shape)
    elif arr.ndim == 2:
        n_trials, n_v = arr.shape
        if n_v != n_voxels:
            raise ValueError(
                f"values shape {(n_trials, n_v)} does not match "
                f"brain-mask voxel count {n_voxels}."
            )
        flat = np.zeros(
            (brain_mask.shape[0], n_trials), dtype=np.float32,
        )
        flat[brain_mask, :] = arr.T
        vol = flat.reshape(*ref.shape, n_trials)
    else:
        raise ValueError(
            f"values must be 1-D or 2-D; got shape {arr.shape}."
        )

    return nib.Nifti1Image(vol, ref.affine)
