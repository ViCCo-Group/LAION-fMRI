"""Synthetic-data fixtures for unit tests.

Mirrors the on-disk layout produced by ``download(...)`` against
the real ``s3://laion-fmri/`` bucket so that ``Subject`` and the
loaders can be exercised offline.

Layout:
    {tmp}/
    ├── .laion_fmri/
    │   └── config.json
    ├── dataset_description.json
    ├── participants.tsv
    ├── participants.json
    ├── README
    ├── stimuli/                          (forward-compat; optional)
    │   ├── images/   (10x10 PNGs)
    │   ├── stimuli.tsv
    │   └── stimuli.json
    └── derivatives/
        ├── glmsingle-tedana/sub-XX/
        │   ├── <subject-level brain mask .nii.gz>
        │   ├── <subject-level noise-ceiling .nii.gz>
        │   └── ses-XX/func/
        │       ├── <single-trial effect statmap .nii.gz>
        │       ├── <per-session noise-ceiling statmap .nii.gz>
        │       └── <GLMsingle events .tsv>
        └── rois/sub-XX/
            ├── visualcat/
            │   ├── sub-XX_space-T1w_res-1pt8_label-visual_mask.nii.gz
            │   ├── sub-XX_hemi-L_space-fsnative_label-visual_mask.func.gii
            │   ├── sub-XX_hemi-L_space-fsnative_label-visual_mask.label
            │   ├── sub-XX_hemi-R_space-fsnative_label-visual_mask.func.gii
            │   └── sub-XX_hemi-R_space-fsnative_label-visual_mask.label
            └── hlviscat/
                └── ... (same five files for label-hlvis)

See ``_trial_betas_filename`` etc. below for the exact patterns.
"""

import json

import nibabel as nib
import numpy as np
import pandas as pd
import pytest


# ── Constants ───────────────────────────────────────────────────

BRAIN_SHAPE = (5, 5, 5)
N_TOTAL_VOXELS = 125
N_BRAIN_VOXELS = 50
N_VISUAL_VOXELS = 30
N_HLVIS_VOXELS = 15
N_STIMULI = 20
N_SHARED = 12
N_UNIQUE = 8
N_SESSIONS = 2
N_REPS_PER_STIMULUS = 3
N_TRIALS_PER_SESSION = N_STIMULI * N_REPS_PER_STIMULUS  # 60
AFFINE = np.eye(4)
SUBJECT_NC_DESC = "Noiseceiling12rep"

# ROI categories on disk under derivatives/rois/{sub}/{category}/
VISUAL_CATEGORY = "visualcat"
HLVIS_CATEGORY = "hlviscat"

# Surface mesh sizes used by GIFTI / FreeSurfer-label fixtures
N_VERTICES_L = 8
N_VERTICES_R = 6
VISUAL_VERT_INDICES_L = (0, 1, 2, 3)
VISUAL_VERT_INDICES_R = (0, 1, 2)
HLVIS_VERT_INDICES_L = (0, 1)
HLVIS_VERT_INDICES_R = (0,)


# ── File-name helpers ───────────────────────────────────────────

def _trial_betas_filename(sub, ses):
    return (
        f"{sub}_{ses}_task-images_space-T1w_stat-effect_"
        f"desc-SingletrialBetas_statmap.nii.gz"
    )


def _session_nc_filename(sub, ses):
    return (
        f"{sub}_{ses}_task-images_space-T1w_"
        f"desc-Noiseceiling_statmap.nii.gz"
    )


def _events_filename(sub, ses):
    return (
        f"{sub}_{ses}_task-images_"
        f"desc-SingletrialBetas_trials.tsv"
    )


def _r2mean_filename(sub):
    """Subject-level mean-R^2 file the loader uses to derive the brain mask."""
    return (
        f"{sub}_task-images_space-T1w_"
        f"stat-rsquare_desc-R2mean_statmap.nii.gz"
    )


def _subject_nc_filename(sub, desc):
    return (
        f"{sub}_task-images_space-T1w_desc-{desc}_statmap.nii.gz"
    )


# ── Volume builders ─────────────────────────────────────────────

def _make_brain_mask():
    """Return a 5x5x5 brain mask with 50 True voxels."""
    mask = np.zeros(BRAIN_SHAPE, dtype=bool)
    mask[1:4, 1:4, :] = True  # 3*3*5 = 45
    mask[0, 0, :] = True      # + 5 = 50
    return mask


def _make_roi_masks(brain_mask):
    """Return (visual, hlvis) ROI volumes (boolean)."""
    brain_indices = np.where(brain_mask.ravel())[0]

    visual_vol = np.zeros(BRAIN_SHAPE, dtype=bool)
    flat = visual_vol.ravel()
    flat[brain_indices[:N_VISUAL_VOXELS]] = True
    visual_vol = flat.reshape(BRAIN_SHAPE)

    hlvis_vol = np.zeros(BRAIN_SHAPE, dtype=bool)
    flat = hlvis_vol.ravel()
    flat[brain_indices[:N_HLVIS_VOXELS]] = True
    hlvis_vol = flat.reshape(BRAIN_SHAPE)

    return visual_vol, hlvis_vol


def _save_nifti(arr, path, dtype=None):
    """Write ``arr`` as a NIfTI to ``path`` with the standard affine."""
    if dtype is not None:
        arr = arr.astype(dtype)
    img = nib.Nifti1Image(arr, AFFINE)
    nib.save(img, str(path))


def _make_events(stim_meta):
    """Return a single-session events DataFrame."""
    rows = []
    trial_idx = 0
    for rep in range(N_REPS_PER_STIMULUS):
        for _, stim_row in stim_meta.iterrows():
            rows.append({
                "trial_idx": trial_idx,
                "run": f"run-{(rep % 3) + 1:02d}",
                "stimulus_id": stim_row["stimulus_id"],
                "rep_index": rep,
            })
            trial_idx += 1
    return pd.DataFrame(rows)


def _make_stimulus_metadata():
    rows = []
    for i in range(N_STIMULI):
        rows.append({
            "stimulus_id": f"stim_{i:03d}",
            "shared": i < N_SHARED,
            "filename": f"stim_{i:03d}.png",
            "category": "object",
        })
    return pd.DataFrame(rows)


def _save_placeholder_pngs(images_dir, stim_meta):
    from PIL import Image

    images_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    for _, row in stim_meta.iterrows():
        arr = rng.integers(0, 255, (10, 10, 3), dtype=np.uint8)
        img = Image.fromarray(arr)
        img.save(images_dir / row["filename"])


# ── Per-subject builder ─────────────────────────────────────────

def _build_subject(data_dir, sub_id, brain_mask, stim_meta, rng):
    """Populate the on-disk tree for one subject."""
    sub_dir = (
        data_dir / "derivatives" / "glmsingle-tedana" / sub_id
    )
    sub_dir.mkdir(parents=True)

    # Subject-level R2mean (the file the loader derives the brain
    # mask from). Synthetic R^2: positive value where the brain
    # mask is True, zero elsewhere.
    r2_subject = brain_mask.astype(np.float32) * 0.5
    _save_nifti(
        r2_subject, sub_dir / _r2mean_filename(sub_id),
        dtype=np.float32,
    )

    # Subject-level NC variant (one is enough for tests)
    nc_subject = np.zeros(BRAIN_SHAPE, dtype=np.float32)
    nc_subject[brain_mask] = rng.uniform(
        0.0, 1.0, N_BRAIN_VOXELS,
    ).astype(np.float32)
    _save_nifti(
        nc_subject,
        sub_dir / _subject_nc_filename(sub_id, SUBJECT_NC_DESC),
        dtype=np.float32,
    )

    # Per-session files
    for ses_idx in range(N_SESSIONS):
        ses_id = f"ses-{ses_idx + 1:02d}"
        func_dir = sub_dir / ses_id / "func"
        func_dir.mkdir(parents=True)

        # 4D single-trial betas: (X, Y, Z, n_trials)
        betas = np.zeros(
            BRAIN_SHAPE + (N_TRIALS_PER_SESSION,), dtype=np.float32,
        )
        flat = betas.reshape(-1, N_TRIALS_PER_SESSION)
        flat[brain_mask.ravel()] = rng.standard_normal(
            (N_BRAIN_VOXELS, N_TRIALS_PER_SESSION),
        ).astype(np.float32)
        _save_nifti(
            flat.reshape(BRAIN_SHAPE + (N_TRIALS_PER_SESSION,)),
            func_dir / _trial_betas_filename(sub_id, ses_id),
            dtype=np.float32,
        )

        # 3D per-session noise ceiling
        nc_session = np.zeros(BRAIN_SHAPE, dtype=np.float32)
        nc_session[brain_mask] = rng.uniform(
            0.0, 1.0, N_BRAIN_VOXELS,
        ).astype(np.float32)
        _save_nifti(
            nc_session,
            func_dir / _session_nc_filename(sub_id, ses_id),
            dtype=np.float32,
        )

        # Events TSV
        events = _make_events(stim_meta)
        events["session"] = ses_id
        events.to_csv(
            func_dir / _events_filename(sub_id, ses_id),
            sep="\t", index=False,
        )


def _save_gifti_mask(mask_array, path):
    """Write a 1-D bool mask as a tiny ``.func.gii`` file."""
    data = np.asarray(mask_array, dtype=np.float32)
    darray = nib.gifti.GiftiDataArray(data)
    img = nib.gifti.GiftiImage(darrays=[darray])
    nib.save(img, str(path))


def _save_freesurfer_label(vertex_indices, path):
    """Write a minimal FreeSurfer ASCII ``.label`` file."""
    indices = list(vertex_indices)
    lines = [
        "#!ascii label, from synthetic conftest",
        f"{len(indices)}",
    ]
    for vid in indices:
        lines.append(f"{vid} 0.000 0.000 0.000 0.000")
    path.write_text("\n".join(lines) + "\n")


def _surface_mask(vertex_indices, n_vertices):
    """Boolean 1-D mask flagging ``vertex_indices`` as True."""
    mask = np.zeros(n_vertices, dtype=bool)
    for vid in vertex_indices:
        mask[vid] = True
    return mask


def _write_roi_files(
    category_dir, sub_id, roi, vol_mask,
    indices_l, indices_r,
):
    """Write the five ROI files (volume + per-hemi func.gii + label)."""
    base = f"{sub_id}"

    # Volume
    _save_nifti(
        vol_mask,
        category_dir / (
            f"{base}_space-T1w_res-1pt8_"
            f"label-{roi}_mask.nii.gz"
        ),
        dtype=np.uint8,
    )

    # Surface (per hemi)
    surf_l = _surface_mask(indices_l, N_VERTICES_L)
    surf_r = _surface_mask(indices_r, N_VERTICES_R)
    _save_gifti_mask(
        surf_l,
        category_dir / (
            f"{base}_hemi-L_space-fsnative_"
            f"label-{roi}_mask.func.gii"
        ),
    )
    _save_gifti_mask(
        surf_r,
        category_dir / (
            f"{base}_hemi-R_space-fsnative_"
            f"label-{roi}_mask.func.gii"
        ),
    )

    # FreeSurfer ASCII label
    _save_freesurfer_label(
        indices_l,
        category_dir / (
            f"{base}_hemi-L_space-fsnative_"
            f"label-{roi}_mask.label"
        ),
    )
    _save_freesurfer_label(
        indices_r,
        category_dir / (
            f"{base}_hemi-R_space-fsnative_"
            f"label-{roi}_mask.label"
        ),
    )


def _build_rois(data_dir, sub_id, brain_mask):
    """Build per-subject ROI tree under ``derivatives/rois/``."""
    visual_vol, hlvis_vol = _make_roi_masks(brain_mask)
    rois_root = data_dir / "derivatives" / "rois" / sub_id

    visual_dir = rois_root / VISUAL_CATEGORY
    visual_dir.mkdir(parents=True)
    _write_roi_files(
        visual_dir, sub_id, "visual", visual_vol,
        VISUAL_VERT_INDICES_L, VISUAL_VERT_INDICES_R,
    )

    hlvis_dir = rois_root / HLVIS_CATEGORY
    hlvis_dir.mkdir(parents=True)
    _write_roi_files(
        hlvis_dir, sub_id, "hlvis", hlvis_vol,
        HLVIS_VERT_INDICES_L, HLVIS_VERT_INDICES_R,
    )


# ── Fixtures ────────────────────────────────────────────────────

@pytest.fixture
def synthetic_data_dir(tmp_path):
    """Build a minimal synthetic dataset matching the bucket layout."""
    data_dir = tmp_path / "laion_fmri_data"
    data_dir.mkdir()

    rng = np.random.default_rng(42)
    brain_mask = _make_brain_mask()
    stim_meta = _make_stimulus_metadata()

    # Metadata directory
    (data_dir / ".laion_fmri").mkdir()
    (data_dir / ".laion_fmri" / "config.json").write_text(
        json.dumps({"data_dir": str(data_dir)}),
    )

    # Root-level files
    (data_dir / "dataset_description.json").write_text(
        json.dumps({
            "Name": "LAION-fMRI",
            "BIDSVersion": "1.8.0",
            "DatasetType": "derivative",
        }),
    )
    pd.DataFrame({
        "participant_id": ["sub-01", "sub-03"],
        "age": [25, 30],
        "sex": ["M", "F"],
    }).to_csv(data_dir / "participants.tsv", sep="\t", index=False)
    (data_dir / "participants.json").write_text(json.dumps({
        "age": {"Description": "Age in years"},
        "sex": {"Description": "Self-reported sex"},
    }))
    (data_dir / "README").write_text("LAION-fMRI synthetic test data\n")

    # Stimuli (forward-compat)
    stimuli_dir = data_dir / "stimuli"
    stimuli_dir.mkdir()
    stim_meta.to_csv(
        stimuli_dir / "stimuli.tsv", sep="\t", index=False,
    )
    (stimuli_dir / "stimuli.json").write_text(
        json.dumps({"description": "LAION-fMRI stimulus set"}),
    )
    _save_placeholder_pngs(stimuli_dir / "images", stim_meta)

    # Per-subject derivatives
    for sub_id in ["sub-01", "sub-03"]:
        _build_subject(data_dir, sub_id, brain_mask, stim_meta, rng)
        _build_rois(data_dir, sub_id, brain_mask)

    return data_dir


@pytest.fixture
def config_dir(tmp_path):
    """Provide a clean temporary config directory for isolation."""
    config_home = tmp_path / "config_home"
    config_home.mkdir()
    return config_home
