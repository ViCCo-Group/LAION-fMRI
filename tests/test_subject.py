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
    assert configured_subject.get_n_voxels() == N_BRAIN_VOXELS


# ── Brain mask ─────────────────────────────────────────────────


def test_get_brain_mask(configured_subject):
    mask = configured_subject.get_brain_mask()
    assert mask.dtype == bool
    assert mask.sum() == N_BRAIN_VOXELS


# ── get_betas ──────────────────────────────────────────────────


def test_get_betas_requires_session(configured_subject):
    with pytest.raises(ValueError, match="session is required"):
        configured_subject.get_betas(session=None)


def test_get_betas_per_session(configured_subject):
    betas = configured_subject.get_betas(session="ses-01")
    assert isinstance(betas, np.ndarray)
    assert betas.shape == (N_TRIALS_PER_SESSION, N_BRAIN_VOXELS)


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
    mask = np.zeros(N_BRAIN_VOXELS, dtype=bool)
    mask[:10] = True
    betas = configured_subject.get_betas(
        session="ses-01", mask=mask,
    )
    assert betas.shape == (N_TRIALS_PER_SESSION, 10)


def test_get_betas_roi_and_mask_raises(configured_subject):
    mask = np.zeros(N_BRAIN_VOXELS, dtype=bool)
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
    assert betas.shape[1] <= N_BRAIN_VOXELS


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
    assert betas.shape == (expected_n, N_BRAIN_VOXELS)


def test_get_betas_stimuli_unique(configured_subject):
    betas = configured_subject.get_betas(
        session="ses-01", stimuli="unique",
    )
    expected_n = N_UNIQUE * (N_TRIALS_PER_SESSION // N_STIMULI)
    assert betas.shape == (expected_n, N_BRAIN_VOXELS)


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
        assert arr.shape == (N_TRIALS_PER_SESSION, N_BRAIN_VOXELS)


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
    assert len(mask) == N_BRAIN_VOXELS
    assert mask.sum() == N_HLVIS_VOXELS


def test_get_roi_masks(configured_subject):
    masks = configured_subject.get_roi_masks(["hlvis", "visual"])
    assert masks["hlvis"].sum() == N_HLVIS_VOXELS
    assert masks["visual"].sum() == N_VISUAL_VOXELS


def test_get_roi_mask_invalid_raises(configured_subject):
    with pytest.raises(ValueError):
        configured_subject.get_roi_mask("nonexistent_roi")


# ── Noise ceiling ──────────────────────────────────────────────


def test_get_noise_ceiling_session(configured_subject):
    nc = configured_subject.get_noise_ceiling(session="ses-01")
    assert isinstance(nc, np.ndarray)
    assert len(nc) == N_BRAIN_VOXELS


def test_get_noise_ceiling_subject_desc(configured_subject):
    nc = configured_subject.get_noise_ceiling(desc=SUBJECT_NC_DESC)
    assert len(nc) == N_BRAIN_VOXELS


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
        assert arr.shape == (N_BRAIN_VOXELS,)


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


# ── Stimulus images ────────────────────────────────────────────


def test_get_images_pil(configured_subject):
    from PIL import Image

    images = configured_subject.get_images()
    assert len(images) == N_STIMULI
    assert isinstance(images[0], Image.Image)


def test_get_images_shared(configured_subject):
    images = configured_subject.get_images(stimuli="shared")
    assert len(images) == N_SHARED


def test_get_images_numpy(configured_subject):
    images = configured_subject.get_images(format="numpy")
    assert images.shape[0] == N_STIMULI
    assert images.shape[3] == 3
    assert images.dtype == np.uint8


def test_get_image_single(configured_subject):
    from PIL import Image

    assert isinstance(configured_subject.get_image(0), Image.Image)


def test_get_images_not_downloaded_raises(tmp_path, monkeypatch):
    """Subject without stimuli directory raises error."""
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
        sub.get_images()


# ── Stimulus metadata ──────────────────────────────────────────


def test_get_stimulus_metadata(configured_subject):
    df = configured_subject.get_stimulus_metadata()
    assert "stimulus_id" in df.columns
    assert "shared" in df.columns
    assert len(df) == N_STIMULI


def test_get_stimulus_metadata_raises_when_tsv_missing(
    tmp_path, monkeypatch,
):
    """No stimuli/stimuli.tsv -> StimuliNotDownloadedError, not pd error."""
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
        sub.get_stimulus_metadata()


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


# ── Trial-to-stimulus mapping ──────────────────────────────────


def test_get_trial_stimulus_indices_per_session(configured_subject):
    indices = configured_subject.get_trial_stimulus_indices(
        session="ses-01",
    )
    assert isinstance(indices, np.ndarray)
    assert len(indices) == N_TRIALS_PER_SESSION
    assert indices.min() >= 0
    assert indices.max() < N_STIMULI


def test_get_trial_stimulus_indices_list_returns_dict(
    configured_subject,
):
    result = configured_subject.get_trial_stimulus_indices(
        session=["ses-01", "ses-02"],
    )
    assert isinstance(result, dict)
    assert set(result) == {"ses-01", "ses-02"}
    for arr in result.values():
        assert isinstance(arr, np.ndarray)
        assert len(arr) == N_TRIALS_PER_SESSION
