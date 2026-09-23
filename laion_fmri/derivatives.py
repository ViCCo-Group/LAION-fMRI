"""Paths to released localizer derivatives."""

from laion_fmri._paths import (
    LOCALIZER_TASKS,
    VOLUME_RESOLUTIONS,
    localizer_effect_path as _localizer_effect_path,
    localizer_statmap_path as _localizer_statmap_path,
)
from laion_fmri.config import get_data_dir


def localizer_statmap_path(
    subject,
    task,
    contrast,
    session,
    space="fsnative",
    hemi=None,
    res="1pt5",
    data_dir=None,
):
    """Return the local path to one localizer contrast z-map."""
    root = get_data_dir() if data_dir is None else data_dir
    return _localizer_statmap_path(
        root, subject, task, contrast, session,
        space=space, hemi=hemi, res=res,
    )


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
    "LOCALIZER_TASKS",
    "VOLUME_RESOLUTIONS",
    "localizer_effect_path",
    "localizer_statmap_path",
]
