import numpy as np
import pandas as pd
import pytest

from laion_fmri._errors import (
    DataNotDownloadedError,
    StimuliNotDownloadedError,
    SubjectNotFoundError,
)
from laion_fmri.subject import Subject, load_subject
from tests.conftest import (
    N_ANATOMICAL_BRAIN_VOXELS,
    N_BRAIN_VOXELS,
    N_HLVIS_VOXELS,
    N_SESSIONS,
    N_SHARED,
    N_STIMULI,
    N_TRIALS_PER_SESSION,
    N_UNIQUE,
    N_VISUAL_VOXELS,
    SUBJECT_NC_DESC,
)


@pytest.fixture
def configured_subject(synthetic_data_dir, monkeypatch):
    """Return a Subject loaded from synthetic data."""
    config_home = synthetic_data_dir / ".." / "sub_cfg"
    config_home.mkdir(exist_ok=True)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(synthetic_data_dir))

    return load_subject("sub-01")


# ── Construction and basic properties ──────────────────────────


def test_load_subject_by_bids_id(configured_subject):
    assert configured_subject.subject_id == "sub-01"


def test_load_subject_by_bare_value(synthetic_data_dir, monkeypatch):
    """``"01"`` is normalized to ``"sub-01"``."""
    config_home = synthetic_data_dir / ".." / "bare_cfg"
    config_home.mkdir(exist_ok=True)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(synthetic_data_dir))

    sub = load_subject("01")
    assert sub.subject_id == "sub-01"


def test_load_subject_unknown_id_raises_not_downloaded(
    synthetic_data_dir, monkeypatch,
):
    """Unknown but well-formed IDs surface as DataNotDownloaded.

    ``resolve_subject_id`` is a pure normalizer; existence is
    decided by the bucket / disk. A well-formed ID that has no
    local data raises ``DataNotDownloadedError`` rather than
    ``SubjectNotFoundError``.
    """
    config_home = synthetic_data_dir / ".." / "inv_cfg"
    config_home.mkdir(exist_ok=True)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(synthetic_data_dir))

    with pytest.raises(DataNotDownloadedError):
        load_subject("sub-99")


def test_load_subject_malformed_id_raises_subject_not_found(
    synthetic_data_dir, monkeypatch,
):
    """Empty / bare-prefix IDs are rejected by the resolver."""
    config_home = synthetic_data_dir / ".." / "malf_cfg"
    config_home.mkdir(exist_ok=True)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(synthetic_data_dir))

    with pytest.raises(SubjectNotFoundError):
        load_subject("")


def test_load_subject_not_downloaded_raises(tmp_path, monkeypatch):
    data_dir = tmp_path / "empty"
    data_dir.mkdir()
    (data_dir / ".laion_fmri").mkdir()

    config_home = tmp_path / "nd_cfg"
    config_home.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(data_dir))

    with pytest.raises(DataNotDownloadedError):
        load_subject("sub-01")


# ── Discovery ──────────────────────────────────────────────────


def test_subject_get_sessions(configured_subject):
    sessions = configured_subject.get_sessions()
    assert len(sessions) == N_SESSIONS
    assert "ses-01" in sessions
    assert "ses-02" in sessions


def test_subject_get_available_rois(configured_subject):
    rois = configured_subject.get_available_rois()
    assert "visual" in rois
    assert "hlvis" in rois


def test_subject_get_n_stimuli(configured_subject):
    assert configured_subject.get_n_stimuli() == N_STIMULI


def test_subject_get_n_stimuli_shared(configured_subject):
    assert (
        configured_subject.get_n_stimuli(stimuli="shared") == N_SHARED
    )


def test_subject_get_n_stimuli_unique(configured_subject):
    assert (
        configured_subject.get_n_stimuli(stimuli="unique") == N_UNIQUE
    )


def test_subject_get_n_voxels(configured_subject):
    assert configured_subject.get_n_voxels() == N_ANATOMICAL_BRAIN_VOXELS


# ── Brain mask ─────────────────────────────────────────────────


def test_get_brain_mask(configured_subject):
    mask = configured_subject.get_brain_mask()
    assert mask.dtype == bool
    assert mask.sum() == N_ANATOMICAL_BRAIN_VOXELS


def test_get_brain_mask_anatomical_default(configured_subject):
    """``source="anatomical"`` is the default and matches no-arg call."""
    default = configured_subject.get_brain_mask()
    explicit = configured_subject.get_brain_mask(source="anatomical")
    assert np.array_equal(default, explicit)


def test_get_brain_mask_rsquare_opt_in(configured_subject):
    """``source="rsquare"`` returns the rsquare-derived mask."""
    rsquare = configured_subject.get_brain_mask(source="rsquare")
    assert rsquare.dtype == bool
    assert rsquare.sum() == N_BRAIN_VOXELS


def test_get_brain_mask_anatomical_distinct(configured_subject):
    """``source="anatomical"`` returns the larger anat-derived mask."""
    rsquare = configured_subject.get_brain_mask(source="rsquare")
    anatomical = configured_subject.get_brain_mask(
        source="anatomical",
    )
    assert anatomical.dtype == bool
    assert anatomical.sum() == N_ANATOMICAL_BRAIN_VOXELS
    assert anatomical.sum() > rsquare.sum()
    # Anatomical is a strict superset of rsquare in the synthetic
    # fixture, so the union equals the anatomical mask.
    assert np.array_equal(anatomical | rsquare, anatomical)


def test_get_brain_mask_rejects_unknown_source(configured_subject):
    """An unknown ``source`` raises ``ValueError``."""
    with pytest.raises(ValueError, match="source"):
        configured_subject.get_brain_mask(source="bogus")


def test_get_brain_mask_anatomical_res_kwarg(configured_subject):
    """``res`` selects which anatomical mask file is loaded.

    The synthetic fixture writes the same mask under both
    resolutions, so both kwargs must succeed and return the
    same content.
    """
    default = configured_subject.get_brain_mask(source="anatomical")
    explicit_1pt8 = configured_subject.get_brain_mask(
        source="anatomical", res="1pt8",
    )
    full_res = configured_subject.get_brain_mask(
        source="anatomical", res=None,
    )
    assert default.sum() == N_ANATOMICAL_BRAIN_VOXELS
    assert np.array_equal(default, explicit_1pt8)
    assert np.array_equal(default, full_res)


def test_get_brain_mask_rsquare_ignores_res(configured_subject):
    """rsquare-source ignores ``res`` (only one resolution exists)."""
    default = configured_subject.get_brain_mask(source="rsquare")
    with_res = configured_subject.get_brain_mask(
        source="rsquare", res=None,
    )
    assert np.array_equal(default, with_res)


def test_get_n_voxels_res_kwarg(configured_subject):
    """``get_n_voxels`` forwards ``res`` to the brain-mask path."""
    assert (
        configured_subject.get_n_voxels(
            source="anatomical", res=None,
        )
        == N_ANATOMICAL_BRAIN_VOXELS
    )


def test_get_n_voxels_with_source(configured_subject):
    """``get_n_voxels`` honors the ``source`` kwarg too."""
    assert (
        configured_subject.get_n_voxels(source="rsquare")
        == N_BRAIN_VOXELS
    )
    assert (
        configured_subject.get_n_voxels(source="anatomical")
        == N_ANATOMICAL_BRAIN_VOXELS
    )


# ── mask_source threaded through downstream accessors ──────────


def test_get_betas_with_anatomical_mask_source(configured_subject):
    """``get_betas(mask_source="anatomical")`` uses the wider mask."""
    betas = configured_subject.get_betas(
        session="ses-01", mask_source="anatomical",
    )
    assert betas.shape == (
        N_TRIALS_PER_SESSION, N_ANATOMICAL_BRAIN_VOXELS,
    )


def test_get_noise_ceiling_with_anatomical_mask_source(
    configured_subject,
):
    """NC honors ``mask_source`` with the anatomical voxel count."""
    nc = configured_subject.get_noise_ceiling(
        session="ses-01", mask_source="anatomical",
    )
    assert nc.shape == (N_ANATOMICAL_BRAIN_VOXELS,)


def test_to_nifti_with_anatomical_mask_source(
    configured_subject, tmp_path,
):
    """``to_nifti`` scatters an anatomical-sized array."""
    import nibabel as nib

    values = np.arange(
        N_ANATOMICAL_BRAIN_VOXELS, dtype=np.float32,
    )
    out = tmp_path / "anat_scatter.nii.gz"
    configured_subject.to_nifti(
        values, str(out), mask_source="anatomical",
    )
    img = nib.load(str(out))
    flat = np.asarray(img.dataobj).ravel()
    anat_mask = configured_subject.get_brain_mask(
        source="anatomical",
    )
    np.testing.assert_array_equal(flat[anat_mask], values)


def test_get_voxel_coordinates_with_anatomical_mask_source(
    configured_subject,
):
    """Voxel coords match the anatomical brain-mask voxel count."""
    coords = configured_subject.get_voxel_coordinates(
        mask_source="anatomical",
    )
    assert coords.shape == (N_ANATOMICAL_BRAIN_VOXELS, 3)


# ── get_betas ──────────────────────────────────────────────────


def test_get_betas_requires_session(configured_subject):
    with pytest.raises(ValueError, match="session is required"):
        configured_subject.get_betas(session=None)


def test_get_betas_preserves_nan_voxels(
    configured_subject, synthetic_data_dir,
):
    """``get_betas`` preserves NaN at unmodeled voxels.

    GLMsingle writes ``NaN`` at brain-mask voxels where the
    model failed to fit a particular trial. ``NaN`` carries
    semantically distinct information ("no estimate") that 0
    ("estimate is 0") does not -- the loader keeps the NaN and
    leaves it to the caller to decide what to do with them.
    """
    import nibabel as nib
    from laion_fmri._paths import betas_path

    # Overwrite one trial's first three voxels with NaN.
    path = betas_path(synthetic_data_dir, "sub-01", "ses-01")
    img = nib.load(str(path))
    data = np.asarray(img.dataobj).copy()
    data[0, 0, 0, 0] = np.nan
    data[1, 1, 0, 0] = np.nan
    data[2, 2, 0, 0] = np.nan
    nib.save(
        nib.Nifti1Image(data, img.affine, img.header), str(path),
    )

    betas = configured_subject.get_betas(session="ses-01")
    # At least one NaN should survive into the returned array.
    assert np.isnan(betas).any()


def test_get_betas_per_session(configured_subject):
    betas = configured_subject.get_betas(session="ses-01")
    assert isinstance(betas, np.ndarray)
    assert betas.shape == (
        N_TRIALS_PER_SESSION, N_ANATOMICAL_BRAIN_VOXELS,
    )


def test_get_betas_roi_visual(configured_subject):
    betas = configured_subject.get_betas(
        session="ses-01", roi="visual",
    )
    assert betas.shape == (N_TRIALS_PER_SESSION, N_VISUAL_VOXELS)


def test_get_betas_roi_hlvis(configured_subject):
    betas = configured_subject.get_betas(
        session="ses-01", roi="hlvis",
    )
    assert betas.shape == (N_TRIALS_PER_SESSION, N_HLVIS_VOXELS)


def test_get_betas_multiple_rois_union(configured_subject):
    """visual ⊃ hlvis -> union has visual count."""
    betas = configured_subject.get_betas(
        session="ses-01", roi=["hlvis", "visual"],
    )
    assert betas.shape == (N_TRIALS_PER_SESSION, N_VISUAL_VOXELS)


def test_get_betas_custom_mask(configured_subject):
    mask = np.zeros(N_ANATOMICAL_BRAIN_VOXELS, dtype=bool)
    mask[:10] = True
    betas = configured_subject.get_betas(
        session="ses-01", mask=mask,
    )
    assert betas.shape == (N_TRIALS_PER_SESSION, 10)


def test_get_betas_roi_and_mask_raises(configured_subject):
    mask = np.zeros(N_ANATOMICAL_BRAIN_VOXELS, dtype=bool)
    mask[:5] = True
    with pytest.raises(ValueError, match="mutually exclusive"):
        configured_subject.get_betas(
            session="ses-01", roi="hlvis", mask=mask,
        )


def test_get_betas_nc_threshold(configured_subject):
    betas = configured_subject.get_betas(
        session="ses-01", nc_threshold=0.5,
    )
    assert betas.shape[0] == N_TRIALS_PER_SESSION
    assert betas.shape[1] <= N_ANATOMICAL_BRAIN_VOXELS


def test_get_betas_roi_and_nc_threshold(configured_subject):
    betas = configured_subject.get_betas(
        session="ses-01", roi="hlvis", nc_threshold=0.5,
    )
    assert betas.shape[0] == N_TRIALS_PER_SESSION
    assert betas.shape[1] <= N_HLVIS_VOXELS


def test_get_betas_stimuli_shared(configured_subject):
    betas = configured_subject.get_betas(
        session="ses-01", stimuli="shared",
    )
    expected_n = N_SHARED * (N_TRIALS_PER_SESSION // N_STIMULI)
    assert betas.shape == (expected_n, N_ANATOMICAL_BRAIN_VOXELS)


def test_get_betas_stimuli_unique(configured_subject):
    betas = configured_subject.get_betas(
        session="ses-01", stimuli="unique",
    )
    expected_n = N_UNIQUE * (N_TRIALS_PER_SESSION // N_STIMULI)
    assert betas.shape == (expected_n, N_ANATOMICAL_BRAIN_VOXELS)


def test_stimulus_filter_uses_label_prefix(
    configured_subject, monkeypatch,
):
    """Real-bucket schema (``label`` column) drives shared/unique
    via the ``shared_`` / ``unique_`` filename prefix, no
    stimulus-metadata table needed.
    """
    label_trials = pd.DataFrame({
        "session": ["ses-01"] * N_TRIALS_PER_SESSION,
        "run": [1] * N_TRIALS_PER_SESSION,
        "beta_index": list(range(N_TRIALS_PER_SESSION)),
        "label": (
            ["shared_12rep_LAION_cluster_1_i0.jpg"] * 30
            + ["unique_LAION_initial_cluster_2_i1.jpg"] * 30
        ),
    })
    monkeypatch.setattr(
        configured_subject, "get_trial_info",
        lambda session=None: label_trials,
    )

    betas_shared = configured_subject.get_betas(
        session="ses-01", stimuli="shared",
    )
    betas_unique = configured_subject.get_betas(
        session="ses-01", stimuli="unique",
    )
    assert betas_shared.shape[0] == 30
    assert betas_unique.shape[0] == 30


def test_stimulus_filter_invalid_value_raises(configured_subject):
    with pytest.raises(ValueError, match="shared.*unique"):
        configured_subject.get_betas(
            session="ses-01", stimuli="something_else",
        )


def test_get_betas_list_of_sessions_returns_dict(
    configured_subject,
):
    """Passing a list yields a dict keyed by session ID."""
    result = configured_subject.get_betas(
        session=["ses-01", "ses-02"],
    )
    assert isinstance(result, dict)
    assert set(result) == {"ses-01", "ses-02"}
    for ses, arr in result.items():
        assert isinstance(arr, np.ndarray)
        assert arr.shape == (
            N_TRIALS_PER_SESSION, N_ANATOMICAL_BRAIN_VOXELS,
        )


def test_get_betas_list_with_filters(configured_subject):
    """Filters apply per session when a list is given."""
    result = configured_subject.get_betas(
        session=["ses-01", "ses-02"], roi="hlvis",
    )
    for arr in result.values():
        assert arr.shape == (N_TRIALS_PER_SESSION, N_HLVIS_VOXELS)


def test_get_betas_single_session_preserves_array_return(
    configured_subject,
):
    """A bare string still returns an ndarray, not a dict."""
    result = configured_subject.get_betas(session="ses-01")
    assert isinstance(result, np.ndarray)


# ── ROI masks ──────────────────────────────────────────────────


def test_get_roi_mask(configured_subject):
    mask = configured_subject.get_roi_mask("hlvis")
    assert isinstance(mask, np.ndarray)
    assert mask.dtype == bool
    assert len(mask) == N_ANATOMICAL_BRAIN_VOXELS
    assert mask.sum() == N_HLVIS_VOXELS


def test_get_roi_masks(configured_subject):
    masks = configured_subject.get_roi_masks(["hlvis", "visual"])
    assert masks["hlvis"].sum() == N_HLVIS_VOXELS
    assert masks["visual"].sum() == N_VISUAL_VOXELS


def test_get_roi_mask_invalid_raises(configured_subject):
    with pytest.raises(ValueError):
        configured_subject.get_roi_mask("nonexistent_roi")


# ── Categories + multi-level ROI query ─────────────────────────


def test_get_available_categories(configured_subject):
    cats = configured_subject.get_available_categories()
    assert cats == ["hlviscat", "visualcat"]


def test_get_available_rois_category_filter(configured_subject):
    visual_only = configured_subject.get_available_rois(
        category="visualcat",
    )
    hlvis_only = configured_subject.get_available_rois(
        category="hlviscat",
    )
    assert visual_only == ["visual"]
    assert hlvis_only == ["hlvis"]


def test_get_roi_mask_all_unions_every_roi(configured_subject):
    """``"all"`` is the union of every ROI on disk.

    In the fixture, hlvis ⊂ visual, so the union equals visual.
    """
    mask_all = configured_subject.get_roi_mask("all")
    mask_visual = configured_subject.get_roi_mask("visual")
    assert mask_all.sum() == mask_visual.sum()
    assert (mask_all == mask_visual).all()


def test_get_roi_mask_category_unions(configured_subject):
    """Single-ROI category equals that ROI in the fixture."""
    mask_cat = configured_subject.get_roi_mask("visualcat")
    mask_named = configured_subject.get_roi_mask("visual")
    assert (mask_cat == mask_named).all()


def test_get_roi_mask_mixed_list(configured_subject):
    """Mixing category + specific name unions correctly."""
    mask = configured_subject.get_roi_mask(["visualcat", "hlvis"])
    expected = configured_subject.get_roi_mask("visual")  # hlvis ⊂ visual
    assert (mask == expected).all()


def test_get_betas_roi_all(configured_subject):
    betas = configured_subject.get_betas(
        session="ses-01", roi="all",
    )
    assert betas.shape == (N_TRIALS_PER_SESSION, N_VISUAL_VOXELS)


def test_get_betas_roi_category(configured_subject):
    betas = configured_subject.get_betas(
        session="ses-01", roi="visualcat",
    )
    assert betas.shape == (N_TRIALS_PER_SESSION, N_VISUAL_VOXELS)


def test_get_betas_roi_mixed_list(configured_subject):
    betas = configured_subject.get_betas(
        session="ses-01", roi=["visualcat", "hlvis"],
    )
    assert betas.shape == (N_TRIALS_PER_SESSION, N_VISUAL_VOXELS)


def test_roi_query_unknown_raises_with_hint(configured_subject):
    """Error message lists both ROI names and category names."""
    with pytest.raises(ValueError) as excinfo:
        configured_subject.get_roi_mask("not_a_thing")
    msg = str(excinfo.value)
    assert "visual" in msg
    assert "hlvis" in msg
    assert "visualcat" in msg
    assert "hlviscat" in msg


def test_get_roi_masks_mixed_keys(configured_subject):
    """Returned dict preserves user-supplied keys verbatim."""
    masks = configured_subject.get_roi_masks(["visual", "visualcat"])
    assert set(masks) == {"visual", "visualcat"}
    # Both resolve to the visual ROI in the fixture.
    assert (masks["visual"] == masks["visualcat"]).all()


# ── get_roi_data (multi-format / hemi) ─────────────────────────


def test_get_roi_data_specific_volume(configured_subject):
    out = configured_subject.get_roi_data(
        "visual", format="volume",
    )
    assert set(out) == {"visual"}
    assert set(out["visual"]) == {"volume"}
    vol = out["visual"]["volume"]
    assert isinstance(vol, np.ndarray)
    assert vol.dtype == bool
    assert vol.sum() == N_VISUAL_VOXELS


def test_get_roi_data_specific_format_nii_gz_synonym(configured_subject):
    """``format="nii.gz"`` is a synonym for ``format="volume"``."""
    out = configured_subject.get_roi_data(
        "visual", format="nii.gz",
    )
    assert set(out["visual"]) == {"volume"}


def test_get_roi_data_specific_gii_left(configured_subject):
    out = configured_subject.get_roi_data(
        "visual", format="gii", hemi="L",
    )
    visual = out["visual"]
    assert set(visual) == {"gii"}
    assert set(visual["gii"]) == {"hemi-L"}
    inner = visual["gii"]["hemi-L"]
    assert set(inner) == {"func.gii", "label"}
    # func.gii is a 1-D bool of vertex count
    assert inner["func.gii"].dtype == bool
    assert inner["func.gii"].shape[0] > 0
    # label is 1-D int vertex indices
    assert np.issubdtype(inner["label"].dtype, np.integer)


def test_get_roi_data_specific_format_func_gii_only(
    configured_subject,
):
    out = configured_subject.get_roi_data(
        "visual", format="func.gii",
    )
    visual = out["visual"]
    assert set(visual["gii"]) == {"hemi-L", "hemi-R"}
    # label key must be absent
    assert "label" not in visual["gii"]["hemi-L"]
    assert "label" not in visual["gii"]["hemi-R"]
    assert "func.gii" in visual["gii"]["hemi-L"]


def test_get_roi_data_all_formats_all_hemi(configured_subject):
    out = configured_subject.get_roi_data(
        "visual", format="all", hemi="all",
    )
    visual = out["visual"]
    assert set(visual) == {"volume", "gii"}
    assert set(visual["gii"]) == {"hemi-L", "hemi-R"}
    for hemi in ("hemi-L", "hemi-R"):
        assert set(visual["gii"][hemi]) == {"func.gii", "label"}


def test_get_roi_data_category_returns_one_entry(
    configured_subject,
):
    out = configured_subject.get_roi_data(
        "visualcat", format="volume",
    )
    assert set(out) == {"visual"}
    assert out["visual"]["volume"].sum() == N_VISUAL_VOXELS


def test_get_roi_data_all_returns_one_entry_per_roi(
    configured_subject,
):
    out = configured_subject.get_roi_data("all", format="volume")
    assert set(out) == {"visual", "hlvis"}


def test_get_roi_data_unknown_format_raises(configured_subject):
    with pytest.raises(ValueError):
        configured_subject.get_roi_data("visual", format="bogus")


def test_get_roi_data_unknown_hemi_raises(configured_subject):
    with pytest.raises(ValueError):
        configured_subject.get_roi_data(
            "visual", format="gii", hemi="X",
        )


# ── Noise ceiling ──────────────────────────────────────────────


def test_get_noise_ceiling_session(configured_subject):
    nc = configured_subject.get_noise_ceiling(session="ses-01")
    assert isinstance(nc, np.ndarray)
    assert len(nc) == N_ANATOMICAL_BRAIN_VOXELS


def test_get_noise_ceiling_subject_desc(configured_subject):
    nc = configured_subject.get_noise_ceiling(desc=SUBJECT_NC_DESC)
    assert len(nc) == N_ANATOMICAL_BRAIN_VOXELS


def test_get_noise_ceiling_requires_session_or_desc(
    configured_subject,
):
    with pytest.raises(ValueError, match="session.*desc"):
        configured_subject.get_noise_ceiling()


def test_get_noise_ceiling_rejects_both_session_and_desc(
    configured_subject,
):
    with pytest.raises(ValueError, match="session.*desc"):
        configured_subject.get_noise_ceiling(
            session="ses-01", desc=SUBJECT_NC_DESC,
        )


def test_get_noise_ceiling_unknown_desc_raises(configured_subject):
    with pytest.raises(FileNotFoundError):
        configured_subject.get_noise_ceiling(desc="does-not-exist")


def test_get_noise_ceiling_with_roi(configured_subject):
    nc = configured_subject.get_noise_ceiling(
        session="ses-01", roi="hlvis",
    )
    assert len(nc) == N_HLVIS_VOXELS


def test_get_noise_ceiling_list_of_sessions_returns_dict(
    configured_subject,
):
    result = configured_subject.get_noise_ceiling(
        session=["ses-01", "ses-02"],
    )
    assert isinstance(result, dict)
    assert set(result) == {"ses-01", "ses-02"}
    for arr in result.values():
        assert arr.shape == (N_ANATOMICAL_BRAIN_VOXELS,)


# ── Trial info ─────────────────────────────────────────────────


def test_get_trial_info_requires_session(configured_subject):
    with pytest.raises(ValueError, match="session"):
        configured_subject.get_trial_info(session=None)


def test_get_trial_info_per_session(configured_subject):
    df = configured_subject.get_trial_info(session="ses-01")
    assert isinstance(df, pd.DataFrame)
    assert "stimulus_id" in df.columns
    assert len(df) == N_TRIALS_PER_SESSION
    assert all(df["session"] == "ses-01")


def test_get_trial_info_list_of_sessions_returns_dict(
    configured_subject,
):
    result = configured_subject.get_trial_info(
        session=["ses-01", "ses-02"],
    )
    assert isinstance(result, dict)
    assert set(result) == {"ses-01", "ses-02"}
    for ses, df in result.items():
        assert isinstance(df, pd.DataFrame)
        assert all(df["session"] == ses)


# ── Stimulus images via sub.images namespace ───────────────────


def test_sub_images_get_returns_pil(configured_subject):
    from PIL import Image

    img = configured_subject.images.get(0)
    assert isinstance(img, Image.Image)


def test_sub_images_get_can_preserve_rgba(configured_subject):
    img = configured_subject.images.get(0, as_displayed=False)
    assert img.mode == "RGBA"


def test_sub_images_get_composites_rgba_by_default(configured_subject):
    img = configured_subject.images.get(0)
    assert img.mode == "RGB"
    assert img.getpixel((0, 0)) == (128, 128, 128)
    assert img.getpixel((1, 0)) == (255, 0, 0)
    assert img.getpixel((2, 0)) == (192, 64, 64)


def test_sub_images_array(configured_subject):
    arr = configured_subject.images.array()
    n_total = N_SESSIONS * N_TRIALS_PER_SESSION
    assert arr.shape[0] == n_total
    assert arr.shape[3] == 3
    assert arr.dtype == np.uint8
    assert tuple(arr[0, 0, 0]) == (128, 128, 128)


def test_sub_images_all_session_filter(configured_subject):
    images = list(configured_subject.images.all(session="ses-01"))
    assert len(images) == N_TRIALS_PER_SESSION
    assert images[0].mode == "RGB"


def test_sub_images_not_downloaded_raises(tmp_path, monkeypatch):
    """Subject without stimuli directory raises error on access."""
    data_dir = tmp_path / "no_stim"
    data_dir.mkdir()
    (data_dir / ".laion_fmri").mkdir()

    # Minimum so Subject() can construct
    glm_dir = (
        data_dir / "derivatives" / "glmsingle-tedana"
        / "sub-01"
    )
    glm_dir.mkdir(parents=True)

    config_home = tmp_path / "ns_cfg"
    config_home.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(data_dir))

    sub = Subject("sub-01", str(data_dir))
    with pytest.raises(StimuliNotDownloadedError):
        _ = sub.metadata


# ── sub.metadata: aggregated trial table ───────────────────────


def test_sub_metadata_columns_and_size(configured_subject):
    df = configured_subject.metadata
    n_total = N_SESSIONS * N_TRIALS_PER_SESSION
    assert len(df) == n_total
    for col in (
        "session", "session_trial", "image_name",
        "stim_idx", "unique_or_shared", "dataset",
    ):
        assert col in df.columns
    assert df["session"].nunique() == N_SESSIONS


def test_sub_metadata_raises_when_stim_csv_missing(
    tmp_path, monkeypatch,
):
    """No stimuli metadata CSV -> StimuliNotDownloadedError."""
    data_dir = tmp_path / "no_stim_meta"
    data_dir.mkdir()
    (data_dir / ".laion_fmri").mkdir()
    glm_dir = (
        data_dir / "derivatives" / "glmsingle-tedana" / "sub-01"
    )
    glm_dir.mkdir(parents=True)

    config_home = tmp_path / "ns_meta_cfg"
    config_home.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(data_dir))

    sub = Subject("sub-01", str(data_dir))
    with pytest.raises(StimuliNotDownloadedError):
        _ = sub.metadata


def test_has_stimuli_false_when_missing(tmp_path, monkeypatch):
    data_dir = tmp_path / "no_stim_pred"
    data_dir.mkdir()
    (data_dir / ".laion_fmri").mkdir()
    glm_dir = (
        data_dir / "derivatives" / "glmsingle-tedana" / "sub-01"
    )
    glm_dir.mkdir(parents=True)

    config_home = tmp_path / "ns_pred_cfg"
    config_home.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(data_dir))

    sub = Subject("sub-01", str(data_dir))
    assert sub.has_stimuli() is False


def test_has_stimuli_true_when_present(configured_subject):
    assert configured_subject.has_stimuli() is True


# ── FreeSurfer recon access ────────────────────────────────────


def test_has_freesurfer_true_when_recon_present(configured_subject):
    """Synthetic fixture builds the recon -- has_freesurfer is True."""
    assert configured_subject.has_freesurfer() is True


def test_has_freesurfer_false_when_recon_missing(
    configured_subject, synthetic_data_dir,
):
    """Subject without a recon directory reports False."""
    import shutil

    fs_dir = (
        synthetic_data_dir / "derivatives" / "freesurfer" / "sub-01"
    )
    shutil.rmtree(fs_dir)
    assert configured_subject.has_freesurfer() is False


def test_get_freesurfer_dir_returns_local_path(
    configured_subject, synthetic_data_dir,
):
    """The path resolves under ``derivatives/freesurfer/{sub}/``."""
    fs_dir = configured_subject.get_freesurfer_dir()
    assert fs_dir.is_dir()
    assert fs_dir == (
        synthetic_data_dir / "derivatives" / "freesurfer" / "sub-01"
    )


def test_get_freesurfer_dir_raises_when_missing(
    configured_subject, synthetic_data_dir,
):
    """No recon on disk -> clear DataNotDownloaded with a fix hint."""
    import shutil

    fs_dir = (
        synthetic_data_dir / "derivatives" / "freesurfer" / "sub-01"
    )
    shutil.rmtree(fs_dir)
    with pytest.raises(DataNotDownloadedError, match="freesurfer"):
        configured_subject.get_freesurfer_dir()


# ── Anatomical derivatives access ──────────────────────────────


def test_has_anatomical_true_when_present(configured_subject):
    """Synthetic fixture writes the anat tree -- has_anatomical True."""
    assert configured_subject.has_anatomical() is True


def test_has_anatomical_false_when_missing(
    configured_subject, synthetic_data_dir,
):
    """Subject without an anatomical directory reports False."""
    import shutil

    anat_dir = (
        synthetic_data_dir / "derivatives" / "anatomical" / "sub-01"
    )
    shutil.rmtree(anat_dir)
    assert configured_subject.has_anatomical() is False


def test_get_anatomical_dir_returns_local_path(
    configured_subject, synthetic_data_dir,
):
    """The path resolves under ``derivatives/anatomical/{sub}/``."""
    anat_dir = configured_subject.get_anatomical_dir()
    assert anat_dir.is_dir()
    assert anat_dir == (
        synthetic_data_dir / "derivatives" / "anatomical" / "sub-01"
    )


def test_get_anatomical_dir_raises_when_missing(
    configured_subject, synthetic_data_dir,
):
    """No anat dir on disk -> clear DataNotDownloaded with fix hint."""
    import shutil

    anat_dir = (
        synthetic_data_dir / "derivatives" / "anatomical" / "sub-01"
    )
    shutil.rmtree(anat_dir)
    with pytest.raises(DataNotDownloadedError, match="anatomical"):
        configured_subject.get_anatomical_dir()


def test_get_t1w_full_res(configured_subject):
    """``get_t1w()`` returns the full-resolution T1w path."""
    path = configured_subject.get_t1w()
    assert path.is_file()
    assert path.name.endswith("_space-T1w_T1w.nii.gz")


def test_get_t1w_res_1pt8(configured_subject):
    """``get_t1w(res='1pt8')`` returns the functional-res T1w path."""
    path = configured_subject.get_t1w(res="1pt8")
    assert path.is_file()
    assert "res-1pt8" in path.name


def test_get_t2w_full_res(configured_subject):
    """``get_t2w()`` returns the full-resolution T2w path."""
    path = configured_subject.get_t2w()
    assert path.is_file()
    assert path.name.endswith("_space-T1w_T2w.nii.gz")


def test_get_anatomical_brain_mask_res_1pt8(configured_subject):
    """Anat brain mask at ``res-1pt8`` aligns with the functional grid."""
    path = configured_subject.get_anatomical_brain_mask(res="1pt8")
    assert path.is_file()
    assert path.name.endswith(
        "_res-1pt8_desc-brain_mask.nii.gz"
    )


def test_sub_metadata_stim_idx_range(configured_subject):
    df = configured_subject.metadata
    indices = df.query("session == 'ses-01'")["stim_idx"].to_numpy()
    assert isinstance(indices, np.ndarray)
    assert len(indices) == N_TRIALS_PER_SESSION
    assert indices.min() >= 0
    assert indices.max() < N_STIMULI


def test_sub_metadata_per_session_breakdown(configured_subject):
    df = configured_subject.metadata
    by_session = df.groupby("session").size().to_dict()
    assert set(by_session) == {"ses-01", "ses-02"}
    for n in by_session.values():
        assert n == N_TRIALS_PER_SESSION
