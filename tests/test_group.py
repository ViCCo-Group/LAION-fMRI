import numpy as np
import pandas as pd
import pytest

from laion_fmri.group import load_subjects
from laion_fmri.subject import Subject
from tests.conftest import (
    N_HLVIS_VOXELS,
    N_REPS_PER_STIMULUS,
    N_SHARED,
)


@pytest.fixture
def configured_group(synthetic_data_dir, monkeypatch):
    """Return a Group loaded from synthetic data."""
    config_home = synthetic_data_dir / ".." / "grp_cfg"
    config_home.mkdir(exist_ok=True)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(synthetic_data_dir))

    return load_subjects(["sub-01", "sub-03"])


def test_load_subjects_by_list(configured_group):
    assert len(configured_group) == 2


def test_load_subjects_all(synthetic_data_dir, monkeypatch):
    config_home = synthetic_data_dir / ".." / "grp_all_cfg"
    config_home.mkdir(exist_ok=True)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(synthetic_data_dir))

    # "all" expands via the S3-backed get_subjects -- mock it so the
    # test doesn't hit the network.
    monkeypatch.setattr(
        "laion_fmri.group.get_subjects",
        lambda: ["sub-01", "sub-03"],
    )

    group = load_subjects("all")
    assert len(group) == 2


def test_group_getitem_by_id(configured_group):
    sub = configured_group["sub-01"]
    assert isinstance(sub, Subject)
    assert sub.subject_id == "sub-01"


def test_group_getitem_by_index(configured_group):
    sub = configured_group[0]
    assert isinstance(sub, Subject)


def test_group_getitem_invalid_raises(configured_group):
    with pytest.raises(KeyError):
        configured_group["sub-99"]


def test_group_iter(configured_group):
    items = list(configured_group)
    assert len(items) == 2
    for sub_id, sub in items:
        assert isinstance(sub_id, str)
        assert isinstance(sub, Subject)


def test_get_shared_betas_requires_session(configured_group):
    with pytest.raises(TypeError):
        configured_group.get_shared_betas()  # missing session


def test_get_shared_betas_per_session(configured_group):
    shared = configured_group.get_shared_betas(session="ses-01")
    assert isinstance(shared, dict)
    assert "sub-01" in shared
    assert "sub-03" in shared
    expected_n_trials = N_SHARED * N_REPS_PER_STIMULUS
    for betas in shared.values():
        assert isinstance(betas, np.ndarray)
        assert betas.shape[0] == expected_n_trials


def test_get_shared_betas_consistent_rows(configured_group):
    shared = configured_group.get_shared_betas(session="ses-01")
    shapes = [b.shape[0] for b in shared.values()]
    assert len(set(shapes)) == 1


def test_get_shared_betas_with_roi(configured_group):
    shared = configured_group.get_shared_betas(
        session="ses-01", roi="hlvis",
    )
    expected_n_trials = N_SHARED * N_REPS_PER_STIMULUS
    for betas in shared.values():
        assert betas.shape == (expected_n_trials, N_HLVIS_VOXELS)


def test_get_shared_images(configured_group):
    from PIL import Image

    images = configured_group.get_shared_images()
    assert len(images) == N_SHARED
    assert isinstance(images[0], Image.Image)


def test_get_shared_stimulus_metadata(configured_group):
    meta = configured_group.get_shared_stimulus_metadata()
    assert isinstance(meta, pd.DataFrame)
    assert len(meta) == N_SHARED
    assert all(meta["shared"])
