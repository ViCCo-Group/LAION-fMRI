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


#: Volumetric grids: ``"1pt8"`` is the GLMsingle beta grid, ``"1pt5"``
#: the grid of the volumetric pRF and localizer maps. ROI masks ship on
#: both.
VOLUME_RESOLUTIONS = ("1pt8", "1pt5")
DEFAULT_VOLUME_RES = "1pt8"


def _check_res(res):
    if res not in VOLUME_RESOLUTIONS:
        raise ValueError(
            f"res must be one of {VOLUME_RESOLUTIONS}; got {res!r}.")
    return res


def parse_roi_label(filename, subject, res=DEFAULT_VOLUME_RES):
    """Extract the ROI name from a volumetric ROI mask filename.

    Returns the ROI label (e.g. ``"FFA1"``) when ``filename``
    matches ``{subject}_space-T1w_res-{res}_label-{ROI}_mask.nii.gz``,
    otherwise returns ``None``.
    """
    head = f"{subject}_space-T1w_res-{_check_res(res)}_label-"
    tail = "_mask.nii.gz"
    if filename.startswith(head) and filename.endswith(tail):
        return filename[len(head):-len(tail)]
    return None


def roi_mask_path(data_dir, subject, roi, res=DEFAULT_VOLUME_RES):
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
    res : ``"1pt8"`` (default) | ``"1pt5"``
        Volumetric grid, see :data:`VOLUME_RESOLUTIONS`.

    Raises
    ------
    FileNotFoundError
        If no matching volumetric mask exists under the
        subject's ROI tree.
    """
    _check_res(res)
    pattern = (
        f"*/{subject}_space-T1w_res-{res}_"
        f"label-{roi}_mask.nii.gz"
    )
    matches = list(rois_subject_dir(data_dir, subject).glob(pattern))
    if not matches:
        raise FileNotFoundError(
            f"ROI {roi!r} not found at res-{res} under "
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


# ── pRF parameter maps and localizer statmaps ───────────────────
#
# Filenames follow the release spec (scripts/release/spec.py in the
# prf-pipelines repository). Entity values must stay alphanumeric:
# `_entity_in_key` matches `entity-[A-Za-z0-9]+`.

#: pRF fitting paradigms (the ``paradigm`` entity).
PRF_PARADIGMS = ("standard", "foveal", "corners", "best")

#: Released fit stages (the ``model`` entity).
PRF_STAGES = ("ols", "gauss", "dn", "dnhrf")

#: pRF parameters (the ``param`` entity). ``r2`` is in-sample; ``r2cv``
#: is cross-validated between the split halves and ``nc`` is the noise
#: ceiling of the data.
PRF_PARAMS = (
    "angle", "ecc", "x", "y", "sd", "r2", "r2cv", "nc",
    "amplitude", "baseline",
    "boldbaseline", "neuralbaseline", "surroundbaseline",
    "rfamplitude", "srfamplitude", "srfsize",
    "hrfdelay", "hrfdispersion",
)

#: Labels of the ``paradigm-best`` ``seg-winner`` segmentation (also the
#: dataset-root ``seg-winner_dseg.tsv``).
PRF_WINNER_LEVELS = {0: "none", 1: "standard", 2: "foveal", 3: "corners"}

#: Parameters of the ``paradigm-best`` maps. ``best`` combines the
#: ``dnhrf`` fits of the three paradigms per vertex or voxel, so it has
#: no stage choice, no split-half fits and no noise ceiling (there is
#: no single dataset behind it); its ``r2cv`` also exists as
#: ``desc-half``.
PRF_BEST_PARAMS = ("x", "y", "ecc", "angle", "sd", "r2", "r2cv")

#: Parameters of the data rather than of a fit: no ``model`` entity.
PRF_STAGE_FREE = ("nc",)

#: Released ``desc`` variants of the full fit's maps. ``odd`` / ``even``
#: are the split-half fits, ``half`` the measured split-half quality
#: maps (``r2cv``, ``nc``), ``filtered`` the ``dnhrf`` maps restricted to
#: reliable, stimulated pRFs. No ``desc`` is the full fit itself.
PRF_DESCS = ("odd", "even", "half", "filtered")

#: Released localizer tasks. ``MotionLeft`` / ``MotionRight`` are the
#: two acquired hemifield tasks; ``MotionLoc`` is the pooled map.
LOCALIZER_TASKS = ("floc", "oloc", "MotionLeft", "MotionRight", "MotionLoc")

#: The session each localizer task was acquired in (the same for every
#: released subject).
LOCALIZER_SESSIONS = {
    "floc": "4BarScreenfLoc",
    "oloc": "31",
    "MotionLeft": "MotionLocBarsSML",
    "MotionRight": "MotionLocBarsSML",
    "MotionLoc": "MotionLocBarsSML",
}

#: ROI category -> (task, contrast) of the localizer contrast its ROIs
#: were delineated on. MT/MST were separated with the ipsilateral
#: hemifield maps, but both are motion-selective on the pooled map.
ROI_CONTRASTS = {
    "face": ("floc", "faceVsOthers"),
    "body": ("floc", "bodyVsOthers"),
    "place": ("floc", "placeVsOthers"),
    "character": ("floc", "characterVsOthers"),
    "object": ("oloc", "objectVsScrambled"),
    "motion": ("MotionLoc", "movingVsStatic"),
}


def retinotopy_subject_dir(data_dir, subject):
    return Path(data_dir) / "derivatives" / "retinotopy" / subject / "func"


def localizers_subject_dir(data_dir, subject, session):
    return (Path(data_dir) / "derivatives" / "localizers" / subject
            / f"ses-{session}" / "func")


def prf_map_path(data_dir, subject, param, paradigm="best",
                 stage="dnhrf", space="T1w", hemi=None,
                 res="1pt8", desc=None):
    """Resolve one pRF parameter map.

    Parameters
    ----------
    param : one of :data:`PRF_PARAMS`
    paradigm : one of :data:`PRF_PARADIGMS`
        ``"best"`` (default), the per-vertex best of the three
        paradigms, exists for ``stage="dnhrf"``, the parameters in
        :data:`PRF_BEST_PARAMS` and ``desc`` None or ``"filtered"``
        (plus ``"half"`` for ``r2cv``); other combinations raise.
        ``"standard"``, ``"foveal"`` and ``"corners"`` exist for every
        ``param``, ``stage`` and ``desc``.
    stage : one of :data:`PRF_STAGES`
    space : ``"T1w"`` (default) | ``"fsnative"``
        ``T1w`` is the volumetric product (cortical ribbon and
        subcortex) and takes ``res``: ``1pt8`` (the default, a
        nearest-neighbour resampling onto the beta grid) or ``1pt5``,
        the grid the fit was computed on. ``fsnative`` requires
        ``hemi``; ``T1w`` refuses it.
    desc : ``None`` (default, the full fit) or one of :data:`PRF_DESCS`
        ``nc`` exists only as ``desc="half"`` and takes no ``stage``.

    Parameters from different ``stage`` or ``paradigm`` values come from
    different fits and should not be combined.
    """
    if param not in PRF_PARAMS:
        raise ValueError(
            f"param must be one of {PRF_PARAMS}; got {param!r}.")
    if paradigm not in PRF_PARADIGMS:
        raise ValueError(
            f"paradigm must be one of {PRF_PARADIGMS}; got {paradigm!r}.")
    if param in PRF_STAGE_FREE:
        stage = None
    elif stage not in PRF_STAGES:
        raise ValueError(
            f"stage must be one of {PRF_STAGES}; got {stage!r}.")
    if desc is not None and desc not in PRF_DESCS:
        raise ValueError(
            f"desc must be None or one of {PRF_DESCS}; got {desc!r}.")
    if paradigm == "best" and not _is_best_map(param, stage, desc):
        raise ValueError(
            "paradigm='best' exists for stage='dnhrf', param in "
            f"{PRF_BEST_PARAMS} and desc None or 'filtered' ('half' for "
            f"r2cv); got param={param!r}, stage={stage!r}, desc={desc!r}. "
            "Pass paradigm='standard', 'foveal' or 'corners'.")
    tail = ((f"_model-{stage}" if stage else "")
            + (f"_desc-{desc}" if desc else "") + "_statmap")

    if space == "fsnative":
        if hemi not in ("L", "R"):
            raise ValueError(
                "space='fsnative' is per-hemisphere; pass hemi='L' or 'R'.")
        name = (f"{subject}_paradigm-{paradigm}_hemi-{hemi}_space-fsnative_"
                f"param-{param}{tail}.func.gii")
    elif space == "T1w":
        _check_volume_hemi(hemi)
        _check_res(res)
        name = (f"{subject}_paradigm-{paradigm}_space-T1w_res-{res}_"
                f"param-{param}{tail}.nii.gz")
    else:
        raise ValueError(
            f"space must be 'fsnative' or 'T1w'; got {space!r}.")

    path = retinotopy_subject_dir(data_dir, subject) / name
    if not path.exists():
        raise FileNotFoundError(f"pRF map not found: {path}")
    return path


def _check_volume_hemi(hemi):
    """A volume has no hemisphere; ``hemi`` would be silently ignored."""
    if hemi is not None:
        raise ValueError(
            "hemi applies to space='fsnative' only; the T1w volume "
            "(the default space) covers both hemispheres.")


def _is_best_map(param, stage, desc):
    """Whether a ``paradigm-best`` map exists for this combination."""
    if stage != "dnhrf" or param not in PRF_BEST_PARAMS:
        return False
    return desc in (None, "filtered") or (desc, param) == ("half", "r2cv")


def prf_winner_path(data_dir, subject, stage="dnhrf", space="T1w",
                    hemi=None, res="1pt8", desc=None):
    """Resolve the ``paradigm-best`` selection (``seg-winner`` dseg).

    Which paradigm's fit each vertex or voxel of the best-of maps comes
    from, coded :data:`PRF_WINNER_LEVELS`. ``desc`` is ``None`` or
    ``"filtered"``; ``space``/``hemi``/``res`` as in :func:`prf_map_path`.
    """
    if stage not in PRF_STAGES:
        raise ValueError(
            f"stage must be one of {PRF_STAGES}; got {stage!r}.")
    if desc not in (None, "filtered"):
        raise ValueError(f"desc must be None or 'filtered'; got {desc!r}.")
    tail = (f"_model-{stage}_seg-winner"
            + (f"_desc-{desc}" if desc else "") + "_dseg")
    if space == "fsnative":
        if hemi not in ("L", "R"):
            raise ValueError(
                "space='fsnative' is per-hemisphere; pass hemi='L' or 'R'.")
        name = (f"{subject}_paradigm-best_hemi-{hemi}_space-fsnative"
                f"{tail}.label.gii")
    elif space == "T1w":
        _check_volume_hemi(hemi)
        _check_res(res)
        name = f"{subject}_paradigm-best_space-T1w_res-{res}{tail}.nii.gz"
    else:
        raise ValueError(
            f"space must be 'fsnative' or 'T1w'; got {space!r}.")
    path = retinotopy_subject_dir(data_dir, subject) / name
    if not path.exists():
        raise FileNotFoundError(f"pRF winner segmentation not found: {path}")
    return path


def _localizer_map_path(data_dir, subject, task, session, run, contrast,
                        stat, space, hemi, res):
    if task not in LOCALIZER_TASKS:
        raise ValueError(
            f"task must be one of {LOCALIZER_TASKS}; got {task!r}.")
    parts = [subject, f"ses-{session}", f"task-{task}"]
    if run is not None:
        parts.append(f"run-{int(run):02d}")
    if space == "fsnative":
        if hemi not in ("L", "R"):
            raise ValueError(
                "space='fsnative' is per-hemisphere; pass hemi='L' or 'R'.")
        parts += [f"hemi-{hemi}", "space-fsnative"]
        ext = ".func.gii"
    elif space == "T1w":
        _check_res(res)
        parts += ["space-T1w", f"res-{res}"]
        ext = ".nii.gz"
    else:
        raise ValueError(
            f"space must be 'fsnative' or 'T1w'; got {space!r}.")
    parts += [f"contrast-{contrast}", f"stat-{stat}", "statmap"]
    path = (localizers_subject_dir(data_dir, subject, session)
            / ("_".join(parts) + ext))
    if not path.exists():
        raise FileNotFoundError(f"Localizer map not found: {path}")
    return path


def localizer_statmap_path(data_dir, subject, task, contrast, session,
                           space="fsnative", hemi=None, res="1pt5",
                           acq=None):
    """Resolve one localizer contrast z-map.

    Parameters
    ----------
    task : one of :data:`LOCALIZER_TASKS`
    contrast : str
        camelCase contrast name as released, e.g. ``"faceVsOthers"``.
    space : ``"fsnative"`` (default) | ``"T1w"``
        ``fsnative`` requires ``hemi``. ``T1w`` is a separate volumetric
        GLM fit (not a projection of the surface fit) and takes ``res``.
    acq : removed
        The motion hemifields are their own tasks now; ignoring ``acq``
        would silently return the pooled map, so passing it raises.
    """
    if acq is not None:
        raise ValueError(
            "acq= was removed: use task='MotionLeft' or 'MotionRight' "
            "for a hemifield, task='MotionLoc' for the pooled map.")
    return _localizer_map_path(
        data_dir, subject, task, session, None, contrast, "z",
        space, hemi, res,
    )


def localizer_fitted_mask_path(data_dir, subject, session, res="1pt5"):
    """Resolve one localizer session's fitted mask.

    The voxels the session's volumetric GLM was fitted on; values outside
    it in the session's maps are not estimates. One per session and grid.
    """
    name = (f"{subject}_ses-{session}_space-T1w_res-{_check_res(res)}_"
            "desc-fitted_mask.nii.gz")
    path = localizers_subject_dir(data_dir, subject, session) / name
    if not path.exists():
        raise FileNotFoundError(f"Localizer fitted mask not found: {path}")
    return path


def localizer_effect_path(data_dir, subject, task, condition, session, run,
                          space="fsnative", hemi=None, res="1pt5"):
    """Resolve one per-run localizer condition estimate (``stat-effect``).

    Parameters
    ----------
    task : one of :data:`LOCALIZER_TASKS` except ``"MotionLoc"``
        The pooled motion map has no per-run effect maps.
    condition : str
        Design-matrix regressor as released, e.g. ``"face"`` or
        ``"scrambled"`` (a condition, not a contrast).
    run : int
    space, hemi, res
        As for :func:`localizer_statmap_path`.
    """
    if task == "MotionLoc":
        raise ValueError(
            "task='MotionLoc' is the pooled map and has no per-run effect "
            "maps; pass task='MotionLeft' or 'MotionRight'.")
    return _localizer_map_path(
        data_dir, subject, task, session, run, condition, "effect",
        space, hemi, res,
    )


# ── FreeSurfer recon ────────────────────────────────────────────

_HEMI_TO_FS = {"L": "lh", "R": "rh"}


def freesurfer_subject_dir(data_dir, subject):
    """Path to the FreeSurfer recon dir for a subject."""
    return (
        Path(data_dir) / "derivatives" / "freesurfer" / subject
    )


def freesurfer_mri_path(data_dir, subject, filename):
    """Path to a file under the recon's ``mri/`` directory.

    ``filename`` is any FreeSurfer MGZ/MGH name -- e.g.
    ``"brain.mgz"``, ``"aparc+aseg.mgz"``, ``"T1.mgz"``.
    """
    return (
        freesurfer_subject_dir(data_dir, subject) / "mri" / filename
    )


def freesurfer_surf_path(data_dir, subject, hemi, name):
    """Path to a per-hemisphere surface file under ``surf/``.

    Parameters
    ----------
    hemi : ``"L"`` or ``"R"``
    name : str
        FreeSurfer surface name (``"white"``, ``"pial"``,
        ``"sphere"``, ``"sphere.reg"``, ``"inflated"``, ...).
    """
    if hemi not in _HEMI_TO_FS:
        raise ValueError(
            f"hemi must be 'L' or 'R'; got {hemi!r}"
        )
    return (
        freesurfer_subject_dir(data_dir, subject)
        / "surf"
        / f"{_HEMI_TO_FS[hemi]}.{name}"
    )


def freesurfer_transforms_dir(data_dir, subject):
    """Path to the recon's ``mri/transforms/`` directory.

    Holds ``talairach.lta`` (the linear T1w -> MNI305 affine
    despite its historical name) and its older ``.xfm`` sibling.
    """
    return (
        freesurfer_subject_dir(data_dir, subject)
        / "mri"
        / "transforms"
    )


# ── Anatomical derivatives ──────────────────────────────────────

# The anatomical-derivatives pipeline groups all per-subject T1w /
# T2w / brain-mask / tissue-mask outputs under a single session
# named ``ses-PrismaAnat``. See:
# ``derivatives/anatomical/sub-XX/ses-PrismaAnat/anat/``.
ANATOMICAL_SESSION = "ses-PrismaAnat"

#: Subjects whose anatomy is in another session: sub-04 has no
#: ``ses-PrismaAnat``; its anatomy comes from a Connectom scanner and
#: groups five visits under one label.
ANATOMICAL_SESSION_BY_SUBJECT = {"sub-04": "ses-ConnectomAnat"}
_ANATOMICAL_SUFFIXES = ("T1w", "T2w", "mask")

#: Anatomical grids: full resolution (``None``) plus the two
#: volumetric grids in :data:`VOLUME_RESOLUTIONS`.
ANATOMICAL_RESOLUTIONS = (None,) + VOLUME_RESOLUTIONS

#: ``label-`` values of the tissue masks (BIDS common labels): cortical
#: grey matter, subcortical grey matter, brainstem, cerebellar cortex,
#: white matter and ventricular CSF. The six do not overlap.
TISSUE_LABELS = ("CGM", "SGM", "BS", "CBM", "WM", "CSF")


def anatomical_subject_dir(data_dir, subject):
    """Path to the anatomical-derivatives dir for a subject.

    Holds the ``ses-PrismaAnat/anat/`` directory (``ses-ConnectomAnat``
    for sub-04) with T1w / T2w /
    brain-mask / tissue-mask files at full resolution, ``res-1pt8``
    and ``res-1pt5``.
    """
    return (
        Path(data_dir) / "derivatives" / "anatomical" / subject
    )


def anatomical_session(subject):
    """The session label of a subject's anatomical derivatives."""
    return ANATOMICAL_SESSION_BY_SUBJECT.get(subject, ANATOMICAL_SESSION)


def anatomical_session_dir(data_dir, subject):
    """Path to the per-subject anatomical session directory."""
    return (
        anatomical_subject_dir(data_dir, subject)
        / anatomical_session(subject)
        / "anat"
    )


def anatomical_file_path(
    data_dir, subject, *, suffix, res=None, desc=None, label=None,
):
    """Assemble the path to one anatomical derivative file.

    Parameters
    ----------
    suffix : ``"T1w"`` | ``"T2w"`` | ``"mask"``
    res : ``None`` | ``"1pt8"`` | ``"1pt5"``
        ``None`` is full resolution; ``"1pt8"`` matches the
        GLMsingle beta grid and ``"1pt5"`` the grid of the
        volumetric pRF and localizer maps.
    desc : ``None`` | ``"brain"``
        BIDS ``desc-`` token of the brain mask.
    label : ``None`` | one of :data:`TISSUE_LABELS`
        BIDS ``label-`` token of a tissue mask. A mask takes
        exactly one of ``desc="brain"`` and ``label``.
    """
    if suffix not in _ANATOMICAL_SUFFIXES:
        raise ValueError(
            f"suffix must be one of {list(_ANATOMICAL_SUFFIXES)}; "
            f"got {suffix!r}."
        )
    if res not in ANATOMICAL_RESOLUTIONS:
        raise ValueError(
            f"res must be one of {list(ANATOMICAL_RESOLUTIONS)}; "
            f"got {res!r}."
        )
    if label is not None and label not in TISSUE_LABELS:
        raise ValueError(
            f"label must be one of {list(TISSUE_LABELS)}; "
            f"got {label!r}."
        )
    if suffix == "mask" and (desc == "brain") == (label is not None):
        raise ValueError(
            "a mask takes exactly one of desc='brain' and label; "
            f"got desc={desc!r}, label={label!r}."
        )
    if suffix != "mask" and label is not None:
        raise ValueError(f"label applies to masks only; got {suffix!r}.")
    parts = [subject, anatomical_session(subject), "space-T1w"]
    if res is not None:
        parts.append(f"res-{res}")
    if label is not None:
        parts.append(f"label-{label}")
    if desc is not None:
        parts.append(f"desc-{desc}")
    filename = "_".join(parts) + f"_{suffix}.nii.gz"
    return anatomical_session_dir(data_dir, subject) / filename


# ── Raw BIDS ────────────────────────────────────────────────────

RAW_TASK = "images"


def raw_subject_dir(data_dir, subject):
    """Path to the raw-BIDS dir for a subject."""
    return Path(data_dir) / subject


def raw_session_dir(data_dir, subject, session):
    """Path to a raw-BIDS session dir."""
    return raw_subject_dir(data_dir, subject) / session


def raw_func_dir(data_dir, subject, session):
    """Path to the raw ``func/`` dir."""
    return raw_session_dir(data_dir, subject, session) / "func"


def raw_fmap_dir(data_dir, subject, session):
    """Path to the raw ``fmap/`` dir."""
    return raw_session_dir(data_dir, subject, session) / "fmap"


def raw_anat_dir(data_dir, subject, session):
    """Path to the raw ``anat/`` dir (per-session MEGRE)."""
    return raw_session_dir(data_dir, subject, session) / "anat"


def _normalize_run_token(run):
    """Return the zero-padded two-digit run string for a bare int/str."""
    if isinstance(run, int):
        return f"{run:02d}"
    return str(run).zfill(2)


def raw_bold_path(data_dir, subject, session, run, echo, part="mag"):
    """Multi-echo raw BOLD NIfTI (``_bold.nii.gz``).

    Parameters
    ----------
    data_dir, subject, session : str or Path
    run : int or str
        Run index. Bare integers are zero-padded to two digits.
    echo : int or str
        Echo index (1..3 for the release protocol).
    part : ``"mag"`` (default) | ``"phase"``
        BIDS ``part-`` entity. Magnitude is the standard input for
        analysis pipelines; phase is the companion file needed for
        phase-based denoising (NORDIC input).
    """
    run_tok = _normalize_run_token(run)
    fname = (
        f"{subject}_{session}_task-{RAW_TASK}_run-{run_tok}"
        f"_echo-{echo}_part-{part}_bold.nii.gz"
    )
    return raw_func_dir(data_dir, subject, session) / fname


def raw_sbref_path(data_dir, subject, session, run, echo, part="mag"):
    """Per-echo single-band reference NIfTI (``_sbref.nii.gz``)."""
    run_tok = _normalize_run_token(run)
    fname = (
        f"{subject}_{session}_task-{RAW_TASK}_run-{run_tok}"
        f"_echo-{echo}_part-{part}_sbref.nii.gz"
    )
    return raw_func_dir(data_dir, subject, session) / fname


def raw_events_path(data_dir, subject, session, run):
    """Per-run raw BIDS events TSV (``_events.tsv``)."""
    run_tok = _normalize_run_token(run)
    fname = (
        f"{subject}_{session}_task-{RAW_TASK}_run-{run_tok}"
        f"_events.tsv"
    )
    return raw_func_dir(data_dir, subject, session) / fname


# ── Stimuli ─────────────────────────────────────────────────────


def stimuli_dir_path(data_dir):
    """Directory holding the stimuli on disk."""
    return Path(data_dir) / "stimuli"


def stimuli_h5_path(data_dir):
    """HDF5 file of all stimulus images, indexed 0..N-1 by row."""
    return stimuli_dir_path(data_dir) / "task-images_stimuli.h5"


def stimuli_metadata_path(data_dir):
    """Stimulus metadata CSV. Row ``i`` matches HDF5 index ``i``."""
    return stimuli_dir_path(data_dir) / "task-images_metadata.csv"


def embeddings_h5_path(data_dir, model):
    """HDF5 file of pretrained image embeddings for ``model``.

    Sits next to the stimulus images and shares the BIDS ``desc-``
    convention -- e.g. ``task-images_desc-CLIP_embeddings.h5``.
    """
    return (
        stimuli_dir_path(data_dir)
        / f"task-images_desc-{model}_embeddings.h5"
    )


def segmentations_h5_path(data_dir):
    """HDF5 file of per-stimulus object-segmentation masks.

    Stacked ``(N, H, W)`` uint8 dataset of binary masks; row
    alignment is described by the sibling metadata CSV.
    """
    return (
        stimuli_dir_path(data_dir)
        / "task-images_desc-segmentations.h5"
    )


def segmentations_metadata_path(data_dir):
    """Sidecar CSV mapping each segmentation row to its source
    image and noun.
    """
    return (
        stimuli_dir_path(data_dir)
        / "task-images_desc-segmentations_metadata.csv"
    )


def captions_path(data_dir):
    """CSV of per-stimulus captions (human + AI), long form.

    One row per caption. Columns:
    ``image_name``, ``caption_idx``, ``source``, ``caption``,
    ``origin_collection``, ``participant_id``, ``ai_model``.
    """
    return stimuli_dir_path(data_dir) / "task-images_desc-captions.csv"


# ── Dataset-level files ─────────────────────────────────────────

def participants_tsv_path(data_dir):
    """Path to the participants TSV file."""
    return Path(data_dir) / "participants.tsv"


# ── Markers ─────────────────────────────────────────────────────

def license_marker_path(data_dir):
    """Marker for accepted dataset (CC0) license.

    Stimulus terms are governed by the access service and no longer
    tracked as a local marker.
    """
    return Path(data_dir) / ".laion_fmri" / "license_accepted"
