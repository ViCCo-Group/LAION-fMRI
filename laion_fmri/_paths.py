"""Path resolution for the LAION-fMRI on-disk layout."""

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


# ── Per-session files (single-trial GLMsingle outputs) ─────────

def betas_path(data_dir, subject, session):
    """4D NIfTI of single-trial effect betas for one session."""
    fname = (
        f"{subject}_{session}_task-images_space-T1w_stat-effect_"
        f"desc-SingletrialBetas_statmap.nii.gz"
    )
    return session_func_dir(data_dir, subject, session) / fname


def session_noise_ceiling_path(data_dir, subject, session):
    """3D NIfTI of per-session noise ceiling."""
    fname = (
        f"{subject}_{session}_task-images_space-T1w_"
        f"desc-Noiseceiling_statmap.nii.gz"
    )
    return session_func_dir(data_dir, subject, session) / fname


def trialinfo_path(data_dir, subject, session):
    """Per-session single-trial event TSV."""
    fname = (
        f"{subject}_{session}_task-images_"
        f"desc-SingletrialBetas_trials.tsv"
    )
    return session_func_dir(data_dir, subject, session) / fname


# ── Subject-level aggregate files ───────────────────────────────

def r2mean_path(data_dir, subject):
    """Subject-level mean-R^2 map.

    The package derives the brain mask from this file
    (``data > 0``) rather than carrying a separate mask file --
    the bucket already ships R2mean and the GLMsingle output is
    zero outside the model's support, so the threshold is
    just "voxels with any model fit".
    """
    fname = (
        f"{subject}_task-images_space-T1w_"
        f"stat-rsquare_desc-R2mean_statmap.nii.gz"
    )
    return glmsingle_subject_dir(data_dir, subject) / fname


def subject_noise_ceiling_path(data_dir, subject, desc):
    """Subject-level noise ceiling NIfTI for a given ``desc`` label.

    The bucket holds several variants (e.g. ``Noiseceiling12rep``,
    ``Noiseceiling4rep``, ``NoiseceilingAllrep``) -- the caller
    picks one.
    """
    fname = (
        f"{subject}_task-images_space-T1w_"
        f"desc-{desc}_statmap.nii.gz"
    )
    return glmsingle_subject_dir(data_dir, subject) / fname


# ── ROI atlases ─────────────────────────────────────────────────

def rois_subject_dir(data_dir, subject):
    """Path to the ROI dir for a subject."""
    return Path(data_dir) / "derivatives" / "rois" / subject


def roi_mask_path(data_dir, subject, roi):
    """Resolve the volumetric ROI mask file for ``roi``.

    The bucket groups ROIs by category
    (``face/``, ``place/``, ...). The category is discovered by
    globbing the subject's rois dir for the matching
    ``label-{roi}_mask.nii.gz`` token.

    Parameters
    ----------
    data_dir : str or Path
    subject : str
        BIDS subject ID (``"sub-XX"``).
    roi : str
        BIDS-clean ROI label (e.g. ``"FFA1"``, ``"pSTSfaces"``).

    Raises
    ------
    FileNotFoundError
        If no matching volumetric mask exists under the
        subject's ROI tree.
    """
    pattern = (
        f"*/{subject}_space-T1w_res-1pt8_"
        f"label-{roi}_mask.nii.gz"
    )
    matches = list(rois_subject_dir(data_dir, subject).glob(pattern))
    if not matches:
        raise FileNotFoundError(
            f"ROI {roi!r} not found under "
            f"{rois_subject_dir(data_dir, subject)}. "
            "See Subject.get_available_rois() for valid names."
        )
    return matches[0]


def roi_surface_path(data_dir, subject, roi, hemi):
    """Resolve the per-hemisphere ``.func.gii`` surface mask file.

    Parameters
    ----------
    data_dir : str or Path
    subject : str
    roi : str
        BIDS-clean ROI label.
    hemi : ``"L"`` or ``"R"``

    Raises
    ------
    FileNotFoundError
    """
    pattern = (
        f"*/{subject}_hemi-{hemi}_space-fsnative_"
        f"label-{roi}_mask.func.gii"
    )
    matches = list(rois_subject_dir(data_dir, subject).glob(pattern))
    if not matches:
        raise FileNotFoundError(
            f"Surface ROI {roi!r} (hemi-{hemi}) not found under "
            f"{rois_subject_dir(data_dir, subject)}."
        )
    return matches[0]


def roi_freesurfer_label_path(data_dir, subject, roi, hemi):
    """Resolve the per-hemisphere FreeSurfer ``.label`` file.

    Parameters
    ----------
    data_dir : str or Path
    subject : str
    roi : str
        BIDS-clean ROI label.
    hemi : ``"L"`` or ``"R"``

    Raises
    ------
    FileNotFoundError
    """
    pattern = (
        f"*/{subject}_hemi-{hemi}_space-fsnative_"
        f"label-{roi}_mask.label"
    )
    matches = list(rois_subject_dir(data_dir, subject).glob(pattern))
    if not matches:
        raise FileNotFoundError(
            f"FreeSurfer label {roi!r} (hemi-{hemi}) not found under "
            f"{rois_subject_dir(data_dir, subject)}."
        )
    return matches[0]


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
