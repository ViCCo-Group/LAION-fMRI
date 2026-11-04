"""Paths to released retinotopy and localizer derivatives."""

from laion_fmri._paths import (
    LOCALIZER_SESSIONS,
    LOCALIZER_TASKS,
    PRF_BEST_PARAMS,
    PRF_DESCS,
    PRF_PARADIGMS,
    PRF_PARAMS,
    PRF_STAGES,
    PRF_WINNER_LEVELS,
    ROI_CONTRASTS,
    VOLUME_RESOLUTIONS,
    localizer_effect_path as _localizer_effect_path,
    localizer_fitted_mask_path as _localizer_fitted_mask_path,
    localizer_statmap_path as _localizer_statmap_path,
    prf_map_path as _prf_map_path,
)
from laion_fmri.config import get_data_dir


def prf_map_path(
    subject,
    param,
    paradigm="best",
    stage="dnhrf",
    space="T1w",
    hemi=None,
    res="1pt8",
    data_dir=None,
    desc=None,
):
    """Return the local path to one pRF parameter map.

    ``paradigm="best"`` (default) is the per-vertex best of the three
    paradigms; it exists for ``stage="dnhrf"`` and
    :data:`PRF_BEST_PARAMS` only. ``desc`` selects a variant of the
    full fit: ``"odd"`` / ``"even"`` (split-half fits), ``"half"``
    (measured split-half ``r2cv`` and ``nc``) or ``"filtered"``
    (reliable, stimulated ``dnhrf`` pRFs); ``paradigm="best"`` has
    ``"filtered"`` and, for ``r2cv``, ``"half"``. ``space="T1w"``
    (default) takes ``res``: ``"1pt8"`` (default, the beta grid) or
    ``"1pt5"`` (the fit grid). ``space="fsnative"`` takes ``hemi``.
    """
    root = get_data_dir() if data_dir is None else data_dir
    return _prf_map_path(
        root, subject, param,
        paradigm=paradigm, stage=stage, space=space, hemi=hemi, res=res,
        desc=desc,
    )


def localizer_statmap_path(
    subject,
    task,
    contrast,
    session,
    space="fsnative",
    hemi=None,
    res="1pt5",
    data_dir=None,
    acq=None,
):
    """Return the local path to one localizer contrast z-map.

    ``acq`` was removed (the motion hemifields are the tasks
    ``MotionLeft`` / ``MotionRight``); passing it raises.
    """
    root = get_data_dir() if data_dir is None else data_dir
    return _localizer_statmap_path(
        root, subject, task, contrast, session,
        space=space, hemi=hemi, res=res, acq=acq,
    )


def localizer_fitted_mask_path(subject, session, res="1pt5", data_dir=None):
    """Return the local path to one localizer session's fitted mask."""
    root = get_data_dir() if data_dir is None else data_dir
    return _localizer_fitted_mask_path(root, subject, session, res=res)


def localizer_effect_path(
    subject,
    task,
    condition,
    session,
    run,
    space="fsnative",
    hemi=None,
    res="1pt5",
    data_dir=None,
):
    """Return the local path to one per-run localizer condition estimate."""
    root = get_data_dir() if data_dir is None else data_dir
    return _localizer_effect_path(
        root, subject, task, condition, session, run,
        space=space, hemi=hemi, res=res,
    )


__all__ = [
    "LOCALIZER_SESSIONS",
    "LOCALIZER_TASKS",
    "PRF_BEST_PARAMS",
    "PRF_DESCS",
    "PRF_PARADIGMS",
    "PRF_PARAMS",
    "PRF_STAGES",
    "PRF_WINNER_LEVELS",
    "ROI_CONTRASTS",
    "VOLUME_RESOLUTIONS",
    "localizer_effect_path",
    "localizer_fitted_mask_path",
    "localizer_statmap_path",
    "prf_map_path",
]
