import pytest

torch = pytest.importorskip("torch")

from laion_fmri.subject import load_subject  # noqa: E402
from laion_fmri.torch_data import LaionFMRIDataset  # noqa: E402
from tests.conftest import (  # noqa: E402
    N_HLVIS_VOXELS,
    N_STIMULI,
    N_TRIALS_PER_SESSION,
)


@pytest.fixture
def configured_subject(synthetic_data_dir, monkeypatch):
    """Return a Subject loaded from synthetic data."""
    config_home = synthetic_data_dir / ".." / "torch_cfg"
    config_home.mkdir(exist_ok=True)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(synthetic_data_dir))

    return load_subject("sub-01")


def test_torch_dataset_len(configured_subject):
    ds = LaionFMRIDataset(
        configured_subject, session="ses-01", roi="hlvis",
    )
    assert len(ds) == N_TRIALS_PER_SESSION


def test_torch_dataset_getitem_keys(configured_subject):
    ds = LaionFMRIDataset(
        configured_subject, session="ses-01", roi="hlvis",
    )
    item = ds[0]
    assert "betas" in item
    assert "image" in item
    assert "stimulus_id" in item
    assert "session" in item
    assert "rep_index" in item


def test_torch_dataset_betas_shape(configured_subject):
    ds = LaionFMRIDataset(
        configured_subject, session="ses-01", roi="hlvis",
    )
    item = ds[0]
    assert isinstance(item["betas"], torch.Tensor)
    assert item["betas"].shape == (N_HLVIS_VOXELS,)


def test_torch_dataset_image_shape(configured_subject):
    ds = LaionFMRIDataset(
        configured_subject, session="ses-01", roi="hlvis",
    )
    item = ds[0]
    assert isinstance(item["image"], torch.Tensor)
    assert item["image"].ndim == 3
    assert item["image"].shape[0] == 3  # CHW


def test_torch_dataset_composites_rgba_on_presentation_grey(
    configured_subject,
):
    ds = LaionFMRIDataset(
        configured_subject, session="ses-01", roi="hlvis",
    )
    image = ds[0]["image"]
    expected_grey = torch.tensor([128 / 255] * 3)
    assert torch.allclose(image[:, 0, 0], expected_grey)
    assert torch.equal(image[:, 0, 1], torch.tensor([1.0, 0.0, 0.0]))
    expected_blend = torch.tensor([192 / 255, 64 / 255, 64 / 255])
    assert torch.allclose(image[:, 0, 2], expected_blend)


def test_torch_dataset_session_field(configured_subject):
    ds = LaionFMRIDataset(
        configured_subject, session="ses-01", roi="hlvis",
    )
    assert ds[0]["session"] == "ses-01"


def test_torch_dataset_with_transform(configured_subject):
    called = []

    def dummy_transform(img_tensor):
        called.append(True)
        return img_tensor

    ds = LaionFMRIDataset(
        configured_subject,
        session="ses-01",
        roi="hlvis",
        image_transform=dummy_transform,
    )
    ds[0]
    assert len(called) == 1


def test_torch_dataset_stimulus_id_is_string(configured_subject):
    ds = LaionFMRIDataset(
        configured_subject, session="ses-01", roi="hlvis",
    )
    assert isinstance(ds[0]["stimulus_id"], str)


def test_torch_dataset_real_bucket_trials_derive_rep_index(
    configured_subject, monkeypatch,
):
    """Real-bucket trial TSVs carry only ``session/run/beta_index/
    label`` -- there is no ``rep_index`` column. The dataset should
    derive it by counting prior occurrences of each stimulus label
    rather than KeyError-ing on the missing column.
    """
    import pandas as pd

    real_trials = pd.DataFrame({
        "session": ["ses-01"] * N_TRIALS_PER_SESSION,
        "run": ["run-01"] * N_TRIALS_PER_SESSION,
        "beta_index": list(range(N_TRIALS_PER_SESSION)),
        "label": [
            f"stim_{(i % N_STIMULI):03d}"
            for i in range(N_TRIALS_PER_SESSION)
        ],
    })
    monkeypatch.setattr(
        configured_subject, "get_trial_info",
        lambda session=None: real_trials,
    )

    ds = LaionFMRIDataset(
        configured_subject, session="ses-01", roi="hlvis",
    )
    # Trial 0: first occurrence of stim_000 -> rep_index 0.
    assert ds[0]["rep_index"] == 0
    # Trial N_STIMULI: second occurrence of stim_000 -> rep_index 1.
    assert ds[N_STIMULI]["rep_index"] == 1
