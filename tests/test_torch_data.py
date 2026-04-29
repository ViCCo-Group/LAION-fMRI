import pytest

torch = pytest.importorskip("torch")

from laion_fmri.subject import load_subject  # noqa: E402
from laion_fmri.torch_data import LaionFMRIDataset  # noqa: E402
from tests.conftest import (  # noqa: E402
    N_HLVIS_VOXELS,
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
