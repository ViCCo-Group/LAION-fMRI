"""On-disk path resolution for laion_fmri.

All file-layout assumptions are centralized here. If the bucket
structure changes, only this module needs updating.
"""

from pathlib import Path


# ── Subject-level directories ───────────────────────────────────

def glmsingle_subject_dir(data_dir, subject):
    """Path to the GLMsingle-tedana derivatives dir for a subject."""
    return (
        Path(data_dir) / "derivatives" / "glmsingle-tedana" / subject
    )


def session_func_dir(data_dir, subject, session):
    """Path to the per-session ``func/`` dir."""
    return (
        glmsingle_subject_dir(data_dir, subject) / session / "func"
    )


def atlases_subject_dir(data_dir, subject):
    """Path to the atlases dir for a subject."""
    return Path(data_dir) / "derivatives" / "atlases" / subject


def rois_dir(data_dir, subject):
    """Path to the ROI dir for a subject."""
    return atlases_subject_dir(data_dir, subject) / "rois"


# ── Per-session files (single-trial GLMsingle outputs) ─────────

def betas_path(data_dir, subject, session):
    """4D NIfTI of single-trial effect betas for one session."""
    fname = (
        f"{subject}_{session}_task-images_desc-singletrial_"
        f"stat-effect_statmap.nii.gz"
    )
    return session_func_dir(data_dir, subject, session) / fname


def session_noise_ceiling_path(data_dir, subject, session):
    """3D NIfTI of per-session noise ceiling."""
    fname = (
        f"{subject}_{session}_task-images_desc-singletrial_"
        f"stat-noiseceiling_statmap.nii.gz"
    )
    return session_func_dir(data_dir, subject, session) / fname


def trialinfo_path(data_dir, subject, session):
    """Per-session GLMsingle events TSV."""
    fname = (
        f"{subject}_{session}_task-images_desc-GLMsingle_events.tsv"
    )
    return session_func_dir(data_dir, subject, session) / fname


# ── Subject-level aggregate files ───────────────────────────────

def brain_mask_path(data_dir, subject):
    """Subject-level brain mask (R^2 > 15%)."""
    fname = (
        f"{subject}_task-images_space-T1w_"
        f"desc-meanR2gt15mask_mask.nii.gz"
    )
    return glmsingle_subject_dir(data_dir, subject) / fname


def subject_noise_ceiling_path(data_dir, subject, desc):
    """Subject-level noise ceiling NIfTI for a given ``desc`` label.

    The bucket holds several variants (e.g. ``noiseceiling33ses``,
    ``noiseceiling30ses4rep``, ...) -- the caller picks one.
    """
    fname = (
        f"{subject}_task-images_space-T1w_"
        f"desc-{desc}_statmap.nii.gz"
    )
    return glmsingle_subject_dir(data_dir, subject) / fname


# ── ROI atlases ─────────────────────────────────────────────────

def roi_mask_path(data_dir, subject, roi):
    """Path to an ROI mask NIfTI for a subject."""
    return rois_dir(data_dir, subject) / f"{roi}.nii.gz"


# ── Stimuli (forward-compat) ────────────────────────────────────

def stimuli_dir_path(data_dir):
    """Path to the stimulus images directory."""
    return Path(data_dir) / "stimuli" / "images"


def stimuli_metadata_path(data_dir):
    """Path to the stimulus metadata TSV."""
    return Path(data_dir) / "stimuli" / "stimuli.tsv"


# ── Dataset-level files ─────────────────────────────────────────

def participants_tsv_path(data_dir):
    """Path to the participants TSV file."""
    return Path(data_dir) / "participants.tsv"


# ── Markers ─────────────────────────────────────────────────────

def license_marker_path(data_dir):
    """Marker for accepted dataset license."""
    return Path(data_dir) / ".laion_fmri" / "license_accepted"


def tou_marker_path(data_dir):
    """Marker for accepted stimuli terms-of-use."""
    return Path(data_dir) / ".laion_fmri" / "stimuli_terms_accepted"
