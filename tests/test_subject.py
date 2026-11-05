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
    N_ECHOES,
    N_HLVIS_VOXELS,
    N_VERTICES_L,
    N_RAW_TRIALS_PER_RUN,
    N_RUNS_PER_SESSION,
    N_SESSIONS,
    N_SHARED,
    N_STIMULI,
    N_TISSUE_VOXELS,
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


@pytest.fixture
def mapping_data_dir(tmp_path, monkeypatch):
    """An initialized, empty data dir; tests add the trees they need."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))

    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(data_dir))
    return data_dir


@pytest.mark.parametrize("tree", [
    "derivatives/retinotopy/sub-04",
    "derivatives/localizers/sub-04",
    "derivatives/rois/sub-04",
])
def test_load_subject_mapping_only_subject_loads_without_betas(
    mapping_data_dir, tree,
):
    (mapping_data_dir / tree).mkdir(parents=True)
    assert load_subject("sub-04").subject_id == "sub-04"


def test_load_subject_main_subject_loads_with_mapping_data_only(
    mapping_data_dir,
):
    """download_mapping(subject="sub-03") alone is enough to load."""
    (mapping_data_dir / "derivatives/localizers/sub-03").mkdir(parents=True)
    assert load_subject("sub-03").subject_id == "sub-03"


@pytest.mark.parametrize("subject, hint", [
    ("sub-01", r"download\(subject='sub-01'\)"),
    ("sub-04", r"download_mapping\(subject='sub-04'\)"),
    ("sub-08", r"download_mapping\(subject='sub-08'\)"),
])
def test_load_subject_not_downloaded_hint_matches_the_dataset(
    mapping_data_dir, subject, hint,
):
    with pytest.raises(DataNotDownloadedError, match=hint):
        load_subject(subject)


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


def test_get_t1w_res_1pt5(configured_subject):
    """``get_t1w(res='1pt5')`` returns the pRF / localizer-grid T1w path."""
    path = configured_subject.get_t1w(res="1pt5")
    assert path.is_file()
    assert path.name.endswith("_res-1pt5_T1w.nii.gz")


@pytest.mark.parametrize("res", [None, "1pt8", "1pt5"])
def test_get_anatomical_tissue_mask_paths(configured_subject, res):
    """Each tissue label resolves to its ``label-`` file on each grid."""
    res_token = f"_res-{res}" if res else ""
    for label in N_TISSUE_VOXELS:
        path = configured_subject.get_anatomical_tissue_mask(
            label, res=res,
        )
        assert path.is_file()
        assert path.name.endswith(
            f"_space-T1w{res_token}_label-{label}_mask.nii.gz"
        )


def test_get_tissue_mask_on_voxel_axis(configured_subject):
    """The mask spans the brain-mask voxels and counts the label's voxels."""
    n_voxels = configured_subject.get_n_voxels()
    for label, n in N_TISSUE_VOXELS.items():
        mask = configured_subject.get_tissue_mask(label)
        assert mask.dtype == bool
        assert mask.shape == (n_voxels,)
        assert mask.sum() == n


def test_get_tissue_mask_on_the_fit_grid(configured_subject):
    """``res="1pt5"`` is indexed by the res-1pt5 brain mask."""
    n_voxels = configured_subject.get_n_voxels(res="1pt5")
    mask = configured_subject.get_tissue_mask("CGM", res="1pt5")
    assert mask.shape == (n_voxels,)
    with pytest.raises(ValueError, match="rsquare"):
        configured_subject.get_tissue_mask(
            "CGM", mask_source="rsquare", res="1pt5",
        )


def test_get_tissue_mask_list_unions(configured_subject):
    """A list of labels is the voxel-wise union, here all grey matter."""
    grey_labels = ["CGM", "SGM", "BS", "CBM"]
    grey = configured_subject.get_tissue_mask(grey_labels)
    assert grey.sum() == sum(N_TISSUE_VOXELS[lab] for lab in grey_labels)
    expected = np.zeros_like(grey)
    for lab in grey_labels:
        expected |= configured_subject.get_tissue_mask(lab)
    assert np.array_equal(grey, expected)


def test_get_tissue_mask_classes_do_not_overlap(configured_subject):
    """No brain-mask voxel carries two tissue labels."""
    stacked = np.stack([
        configured_subject.get_tissue_mask(label)
        for label in N_TISSUE_VOXELS
    ])
    assert stacked.sum(axis=0).max() == 1


def test_get_tissue_mask_feeds_get_betas(configured_subject):
    """The voxel-axis mask is accepted as ``mask=`` by ``get_betas``."""
    cgm = configured_subject.get_tissue_mask("CGM")
    betas = configured_subject.get_betas(session="ses-01", mask=cgm)
    assert betas.shape[1] == N_TISSUE_VOXELS["CGM"]


def test_get_tissue_mask_unknown_label_raises(configured_subject):
    """An unknown label raises ``ValueError`` before touching disk."""
    with pytest.raises(ValueError, match="label must be one of"):
        configured_subject.get_tissue_mask("GM")


def test_get_anatomical_tissue_mask_raises_when_missing(
    configured_subject, synthetic_data_dir,
):
    """A tissue mask absent on disk raises ``DataNotDownloadedError``."""
    path = configured_subject.get_anatomical_tissue_mask("WM", res="1pt5")
    path.unlink()
    with pytest.raises(DataNotDownloadedError, match="include_anatomical"):
        configured_subject.get_anatomical_tissue_mask("WM", res="1pt5")


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


# ── Raw BIDS access ────────────────────────────────────────────


def test_has_raw_true_when_present(configured_subject):
    """Synthetic fixture writes the raw tree -- has_raw is True."""
    assert configured_subject.has_raw() is True


def test_has_raw_false_when_missing(
    configured_subject, synthetic_data_dir,
):
    """Subject without a raw BIDS directory reports False."""
    import shutil

    raw_dir = synthetic_data_dir / "sub-01"
    shutil.rmtree(raw_dir)
    assert configured_subject.has_raw() is False


def test_has_raw_session_scoped_true(configured_subject):
    """``has_raw(session=...)`` narrows to a specific session."""
    assert configured_subject.has_raw(session="ses-01") is True


def test_has_raw_session_scoped_false(
    configured_subject, synthetic_data_dir,
):
    """``has_raw(session=...)`` returns False when that session absent."""
    import shutil

    ses_dir = synthetic_data_dir / "sub-01" / "ses-01"
    shutil.rmtree(ses_dir)
    assert configured_subject.has_raw(session="ses-01") is False


def test_get_events_single_run_returns_dataframe(configured_subject):
    """Single-run call returns exactly that run's event table."""
    df = configured_subject.get_events(session="ses-01", run="01")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == N_RAW_TRIALS_PER_RUN


def test_get_events_bids_columns_present(configured_subject):
    """The BIDS core columns (onset, duration, trial_type) survive."""
    df = configured_subject.get_events(session="ses-01", run="01")
    for col in ("onset", "duration", "trial_type"):
        assert col in df.columns


def test_get_events_no_run_concatenates_all_runs_with_run_column(
    configured_subject,
):
    """``run=None`` concatenates every run in the session and tags
    each row with the ``run`` it came from.
    """
    df = configured_subject.get_events(session="ses-01")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == N_RAW_TRIALS_PER_RUN * N_RUNS_PER_SESSION
    assert "run" in df.columns
    assert set(df["run"].unique()) == {"run-01", "run-02"}


def test_get_events_accepts_bare_run_value(configured_subject):
    """``run=1`` or ``run="1"`` should work as well as ``run="01"``."""
    df = configured_subject.get_events(session="ses-01", run=1)
    assert len(df) == N_RAW_TRIALS_PER_RUN


def test_get_events_missing_raises_data_not_downloaded(
    configured_subject, synthetic_data_dir,
):
    """No events on disk for the requested session -> clear error."""
    import shutil

    ses_dir = synthetic_data_dir / "sub-01" / "ses-01"
    shutil.rmtree(ses_dir)
    with pytest.raises(DataNotDownloadedError, match="events"):
        configured_subject.get_events(session="ses-01", run="01")


def test_get_events_requires_session(configured_subject):
    """Empty ``session`` argument raises a clear error."""
    with pytest.raises(ValueError, match="session"):
        configured_subject.get_events(session=None)


def test_get_raw_bold_shape_matches_mask(configured_subject):
    """Raw BOLD comes back as ``(n_volumes, n_mask_voxels)`` float32."""
    arr = configured_subject.get_raw_bold(
        session="ses-01", run="01", echo="1",
    )
    assert arr.shape == (
        N_RAW_TRIALS_PER_RUN, N_ANATOMICAL_BRAIN_VOXELS,
    )
    assert arr.dtype == np.float32


def test_get_raw_bold_defaults_to_mag_part(
    configured_subject,
):
    """The default ``part`` is ``"mag"`` (the standard magnitude BOLD)."""
    default = configured_subject.get_raw_bold(
        session="ses-01", run="01", echo="1",
    )
    explicit = configured_subject.get_raw_bold(
        session="ses-01", run="01", echo="1", part="mag",
    )
    assert np.array_equal(default, explicit)


def test_get_raw_bold_missing_raises_data_not_downloaded(
    configured_subject, synthetic_data_dir,
):
    """No raw BOLD file for the requested echo -> clear error."""
    import shutil

    ses_dir = synthetic_data_dir / "sub-01" / "ses-01"
    shutil.rmtree(ses_dir)
    with pytest.raises(DataNotDownloadedError, match="raw"):
        configured_subject.get_raw_bold(
            session="ses-01", run="01", echo="1",
        )


def test_get_sbref_returns_expected_shape(configured_subject):
    """SBRef comes back as a 1-D vector over the brain mask."""
    arr = configured_subject.get_sbref(
        session="ses-01", run="01", echo="1",
    )
    assert arr.shape == (N_ANATOMICAL_BRAIN_VOXELS,)
    assert arr.dtype == np.float32


def test_get_sbref_defaults_to_mag_part(configured_subject):
    """The default ``part`` is ``"mag"`` for sbref too."""
    default = configured_subject.get_sbref(
        session="ses-01", run="01", echo="1",
    )
    explicit = configured_subject.get_sbref(
        session="ses-01", run="01", echo="1", part="mag",
    )
    assert np.array_equal(default, explicit)


def test_raw_all_echoes_readable(configured_subject):
    """Every echo in the synthetic fixture is reachable through the API."""
    for echo in range(1, N_ECHOES + 1):
        arr = configured_subject.get_raw_bold(
            session="ses-01", run="01", echo=str(echo),
        )
        assert arr.shape[0] == N_RAW_TRIALS_PER_RUN


# ── pRF maps ────────────────────────────────────────────────────


def _write_prf(data_dir, name, values):
    import nibabel as nib

    path = data_dir / "derivatives/retinotopy/sub-01/func" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    values = np.asarray(values, dtype=np.float32)
    if name.endswith(".func.gii"):
        arr = nib.gifti.GiftiDataArray(values)
        nib.save(nib.GiftiImage(darrays=[arr]), str(path))
    else:
        nib.save(nib.Nifti1Image(values, np.eye(4)), str(path))


def _prf_volume_name(param, res="1pt8"):
    return (
        f"sub-01_paradigm-best_space-T1w_res-{res}_param-{param}_"
        "model-dnhrf_statmap.nii.gz"
    )


def test_get_prf_volume_is_indexed_like_the_betas(
    configured_subject, synthetic_data_dir,
):
    """One value per brain-mask voxel, in the voxel axis' order; roi
    selects within it."""
    sub = configured_subject
    grid = np.arange(125, dtype=np.float32).reshape(5, 5, 5)
    _write_prf(synthetic_data_dir, _prf_volume_name("angle"), grid)
    brain = sub.get_brain_mask()
    angle = sub.get_prf("angle")
    assert angle.shape == (N_ANATOMICAL_BRAIN_VOXELS,)
    np.testing.assert_array_equal(angle, grid.ravel()[brain])
    in_roi = sub.get_prf("angle", roi="hlvis")
    np.testing.assert_array_equal(in_roi, angle[sub.get_roi_mask("hlvis")])
    assert in_roi.shape == (N_HLVIS_VOXELS,)


def test_get_prf_surface_roi(configured_subject, synthetic_data_dir):
    from laion_fmri._paths import roi_surface_path
    from laion_fmri.io import load_gifti_mask

    sub = configured_subject
    values = np.arange(N_VERTICES_L, dtype=np.float32)
    _write_prf(
        synthetic_data_dir,
        "sub-01_paradigm-standard_hemi-L_space-fsnative_param-x_"
        "model-dnhrf_desc-filtered_statmap.func.gii",
        values,
    )
    kw = dict(paradigm="standard", desc="filtered", space="fsnative",
              hemi="L")
    np.testing.assert_array_equal(sub.get_prf("x", **kw), values)
    keep = load_gifti_mask(
        roi_surface_path(synthetic_data_dir, "sub-01", "hlvis", "L"))
    np.testing.assert_array_equal(
        sub.get_prf("x", roi="hlvis", **kw), values[keep])


def test_get_prf_missing_map_says_how_to_download(configured_subject):
    with pytest.raises(DataNotDownloadedError, match="include-retinotopy"):
        configured_subject.get_prf("ecc", paradigm="foveal")


def test_get_prf_best_without_a_noise_ceiling_says_why(configured_subject):
    """Downloading cannot help here, so no download hint."""
    with pytest.raises(ValueError, match="paradigm='standard'"):
        configured_subject.get_prf("nc", desc="half")


@pytest.mark.parametrize("call", [
    lambda s: s.get_prf("ecc"),
    lambda s: s.get_localizer("floc", "faceVsOthers"),
    lambda s: s.get_localizer_fitted_mask("floc"),
])
def test_missing_maps_of_a_mapping_only_subject_point_to_download_mapping(
    tmp_path, call,
):
    """``download`` refuses sub-04, so the hint names download-mapping."""
    with pytest.raises(
        DataNotDownloadedError, match="download-mapping --subject sub-04$",
    ):
        call(Subject("sub-04", str(tmp_path)))


def test_missing_anatomy_of_a_mapping_only_subject_points_to_download_mapping(
    tmp_path,
):
    with pytest.raises(
        DataNotDownloadedError,
        match=r"download_mapping\(subject='sub-04', include_anatomical",
    ):
        Subject("sub-04", str(tmp_path)).get_t1w()


def test_get_prf_winner_names_volume_and_surface(
    configured_subject, synthetic_data_dir,
):
    """Paradigm names from the seg-winner dseg, indexed like get_prf."""
    import nibabel as nib

    sub = configured_subject
    levels = ["none", "standard", "foveal", "corners"]
    d = synthetic_data_dir / "derivatives/retinotopy/sub-01/func"
    d.mkdir(parents=True, exist_ok=True)
    codes = (np.arange(125) % 4).astype(np.int16).reshape(5, 5, 5)
    nib.save(
        nib.Nifti1Image(codes, np.eye(4)),
        str(d / "sub-01_paradigm-best_space-T1w_res-1pt8_model-dnhrf_"
                "seg-winner_dseg.nii.gz"),
    )
    names = sub.get_prf("winner")
    expect = np.array(levels)[codes.ravel()[sub.get_brain_mask()]]
    np.testing.assert_array_equal(names, expect)
    np.testing.assert_array_equal(
        sub.get_prf("winner", roi="hlvis"),
        expect[sub.get_roi_mask("hlvis")],
    )

    surf = (np.arange(N_VERTICES_L) % 4).astype(np.int32)
    nib.save(
        nib.GiftiImage(darrays=[nib.gifti.GiftiDataArray(
            surf, intent="NIFTI_INTENT_LABEL", datatype="NIFTI_TYPE_INT32",
        )]),
        str(d / "sub-01_paradigm-best_hemi-L_space-fsnative_model-dnhrf_"
                "seg-winner_desc-filtered_dseg.label.gii"),
    )
    got = sub.get_prf("winner", desc="filtered", space="fsnative", hemi="L")
    assert got.tolist() == [levels[c] for c in surf]


def test_get_prf_winner_missing_says_how_to_download(configured_subject):
    with pytest.raises(DataNotDownloadedError, match="include-retinotopy"):
        configured_subject.get_prf("winner", space="fsnative", hemi="R")


@pytest.mark.parametrize(
    "kw",
    [dict(paradigm="standard"), dict(stage="gauss"), dict(desc="odd")],
)
def test_get_prf_winner_only_for_the_dnhrf_best_of(configured_subject, kw):
    with pytest.raises(ValueError, match="winner"):
        configured_subject.get_prf("winner", **kw)


def test_get_prf_roi_and_mask_raises(configured_subject):
    mask = np.zeros(N_ANATOMICAL_BRAIN_VOXELS, dtype=bool)
    with pytest.raises(ValueError, match="mutually exclusive"):
        configured_subject.get_prf("angle", roi="hlvis", mask=mask)


def test_get_noise_ceiling_roi_and_mask_raises(configured_subject):
    mask = np.zeros(N_ANATOMICAL_BRAIN_VOXELS, dtype=bool)
    with pytest.raises(ValueError, match="mutually exclusive"):
        configured_subject.get_noise_ceiling(
            session="ses-01", roi="hlvis", mask=mask,
        )


# ── Localizer maps ──────────────────────────────────────────────


def _write_face_roi_and_zmap(data_dir, z):
    """FFA1 in the face category (the hlvis voxels), and the 1pt8
    faceVsOthers z-map it is thresholded on."""
    import shutil

    import nibabel as nib

    rois = data_dir / "derivatives/rois/sub-01"
    (rois / "face").mkdir()
    shutil.copy(
        next((rois / "hlviscat").glob("*_res-1pt8_label-hlvis_mask.nii.gz")),
        rois / "face/sub-01_space-T1w_res-1pt8_label-FFA1_mask.nii.gz",
    )
    d = data_dir / "derivatives/localizers/sub-01/ses-4BarScreenfLoc/func"
    d.mkdir(parents=True)
    nib.save(
        nib.Nifti1Image(np.asarray(z, dtype=np.float32), np.eye(4)),
        str(d / "sub-01_ses-4BarScreenfLoc_task-floc_space-T1w_res-1pt8_"
                "contrast-faceVsOthers_stat-z_statmap.nii.gz"),
    )


def test_get_localizer_is_indexed_like_the_betas(
    configured_subject, synthetic_data_dir,
):
    sub = configured_subject
    z = np.linspace(-3, 9, 125).reshape(5, 5, 5)
    _write_face_roi_and_zmap(synthetic_data_dir, z)
    brain = sub.get_brain_mask()
    got = sub.get_localizer("floc", "faceVsOthers")
    np.testing.assert_allclose(got, z.ravel()[brain].astype(np.float32))
    np.testing.assert_allclose(
        sub.get_localizer("floc", "faceVsOthers", roi="FFA1"),
        got[sub.get_roi_mask("FFA1")],
    )


def test_get_localizer_missing_says_how_to_download(configured_subject):
    with pytest.raises(DataNotDownloadedError, match="include-localizers"):
        configured_subject.get_localizer("oloc", "objectVsScrambled")


def test_get_roi_mask_z_threshold_uses_the_defining_contrast(
    configured_subject, synthetic_data_dir,
):
    sub = configured_subject
    z = np.linspace(-3, 9, 125).reshape(5, 5, 5)
    _write_face_roi_and_zmap(synthetic_data_dir, z)
    roi = sub.get_roi_mask("FFA1")
    zb = sub.get_localizer("floc", "faceVsOthers")
    t = float(np.median(zb[roi]))
    kept = sub.get_roi_mask("FFA1", z_threshold=t)
    np.testing.assert_array_equal(kept, roi & (zb > t))
    assert 0 < kept.sum() < roi.sum()
    np.testing.assert_array_equal(
        sub.get_roi_mask("face", z_threshold=t), kept)


def test_get_roi_mask_z_threshold_refuses_rois_without_a_contrast(
    configured_subject,
):
    with pytest.raises(ValueError, match="hlvis"):
        configured_subject.get_roi_mask("hlvis", z_threshold=5)


# ── res-1pt5: the grid the volumetric fits were computed on ──────


def _save_volume(path, data, dtype=np.float32):
    import nibabel as nib

    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(
        nib.Nifti1Image(np.asarray(data, dtype=dtype), np.eye(4)), str(path),
    )


def _write_1pt5_brain_mask(data_dir):
    """A res-1pt5 brain mask that differs from the res-1pt8 one, so a
    test can tell which grid's mask indexed the result."""
    mask = np.zeros((5, 5, 5), dtype=np.uint8)
    mask[:, :, :2] = 1
    _save_volume(
        data_dir / "derivatives/anatomical/sub-01/ses-PrismaAnat/anat/"
        "sub-01_ses-PrismaAnat_space-T1w_res-1pt5_desc-brain_mask.nii.gz",
        mask, np.uint8,
    )
    return mask.ravel().astype(bool)


def test_get_prf_res_1pt5_reads_the_fit_grid(
    configured_subject, synthetic_data_dir,
):
    sub = configured_subject
    brain15 = _write_1pt5_brain_mask(synthetic_data_dir)
    grid8 = np.arange(125, dtype=np.float32).reshape(5, 5, 5)
    grid15 = -grid8
    _write_prf(synthetic_data_dir, _prf_volume_name("angle"), grid8)
    _write_prf(synthetic_data_dir, _prf_volume_name("angle", "1pt5"), grid15)
    np.testing.assert_array_equal(
        sub.get_prf("angle", res="1pt5"), grid15.ravel()[brain15])
    np.testing.assert_array_equal(
        sub.get_prf("angle"), grid8.ravel()[sub.get_brain_mask()])


def test_get_localizer_res_1pt5_reads_the_fit_grid(
    configured_subject, synthetic_data_dir,
):
    brain15 = _write_1pt5_brain_mask(synthetic_data_dir)
    z = np.linspace(-3, 9, 125).reshape(5, 5, 5)
    _save_volume(
        synthetic_data_dir
        / "derivatives/localizers/sub-01/ses-4BarScreenfLoc/func/"
        "sub-01_ses-4BarScreenfLoc_task-floc_space-T1w_res-1pt5_"
        "contrast-faceVsOthers_stat-z_statmap.nii.gz",
        z,
    )
    got = configured_subject.get_localizer(
        "floc", "faceVsOthers", res="1pt5")
    np.testing.assert_allclose(got, z.ravel()[brain15].astype(np.float32))


def test_get_roi_mask_res_1pt5_and_rois_present_on_one_grid_only(
    configured_subject, synthetic_data_dir,
):
    """A ROI shipped on res-1pt5 only (sub-04, sub-08) is still found,
    and selects within the res-1pt5 brain mask."""
    sub = configured_subject
    brain15 = _write_1pt5_brain_mask(synthetic_data_dir)
    roi = np.zeros((5, 5, 5), dtype=np.uint8)
    roi[2, 2, :] = 1
    _save_volume(
        synthetic_data_dir / "derivatives/rois/sub-01/retinotopy/"
        "sub-01_space-T1w_res-1pt5_label-V1d_mask.nii.gz",
        roi, np.uint8,
    )
    got = sub.get_roi_mask("V1d", res="1pt5")
    np.testing.assert_array_equal(got, roi.ravel().astype(bool)[brain15])
    assert got.sum() == 2
    grid15 = np.arange(125, dtype=np.float32).reshape(5, 5, 5)
    _write_prf(synthetic_data_dir, _prf_volume_name("ecc", "1pt5"), grid15)
    np.testing.assert_array_equal(
        sub.get_prf("ecc", res="1pt5", roi="V1d"),
        grid15.ravel()[brain15][got],
    )


@pytest.mark.parametrize("call", [
    lambda s: s.get_prf("angle", res="1pt5", mask_source="rsquare"),
    lambda s: s.get_localizer(
        "floc", "faceVsOthers", res="1pt5", mask_source="rsquare"),
    lambda s: s.get_roi_mask("hlvis", res="1pt5", mask_source="rsquare"),
    lambda s: s.get_localizer_fitted_mask(
        "floc", res="1pt5", mask_source="rsquare"),
])
def test_rsquare_brain_mask_exists_on_the_beta_grid_only(
    configured_subject, call,
):
    with pytest.raises(ValueError, match="beta grid only"):
        call(configured_subject)


def test_get_localizer_fitted_mask_per_session_and_grid(
    configured_subject, synthetic_data_dir,
):
    sub = configured_subject
    brain15 = _write_1pt5_brain_mask(synthetic_data_dir)
    fitted = np.zeros((5, 5, 5), dtype=np.uint8)
    fitted[1:4, 1:4, 1:4] = 1
    d = (synthetic_data_dir
         / "derivatives/localizers/sub-01/ses-MotionLocBarsSML/func")
    for res in ("1pt8", "1pt5"):
        _save_volume(
            d / f"sub-01_ses-MotionLocBarsSML_space-T1w_res-{res}_"
            "desc-fitted_mask.nii.gz",
            fitted, np.uint8,
        )
    flat = fitted.ravel().astype(bool)
    left = sub.get_localizer_fitted_mask("MotionLeft")
    np.testing.assert_array_equal(left, flat[sub.get_brain_mask()])
    np.testing.assert_array_equal(
        sub.get_localizer_fitted_mask("MotionRight"), left)
    np.testing.assert_array_equal(
        sub.get_localizer_fitted_mask("MotionLeft", res="1pt5"),
        flat[brain15],
    )


def test_get_localizer_fitted_mask_missing_says_how_to_download(
    configured_subject,
):
    with pytest.raises(DataNotDownloadedError, match="include-localizers"):
        configured_subject.get_localizer_fitted_mask("floc")


def test_laionstim_category_is_queryable(
    configured_subject, synthetic_data_dir,
):
    """The laionstim group needs no special casing: a category directory
    whose (de-hyphenated) labels resolve by name and by category."""
    import shutil

    sub = configured_subject
    rois = synthetic_data_dir / "derivatives/rois/sub-01"
    (rois / "laionstim").mkdir()
    shutil.copy(
        next((rois / "hlviscat").glob("*_res-1pt8_label-hlvis_mask.nii.gz")),
        rois / "laionstim/"
        "sub-01_space-T1w_res-1pt8_label-laionstimV1d_mask.nii.gz",
    )
    assert sub.get_available_rois(category="laionstim") == ["laionstimV1d"]
    hlvis = sub.get_roi_mask("hlvis")
    np.testing.assert_array_equal(sub.get_roi_mask("laionstimV1d"), hlvis)
    np.testing.assert_array_equal(sub.get_roi_mask("laionstim"), hlvis)
