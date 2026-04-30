import json

import pytest

from laion_fmri._errors import DataDirNotSetError
from laion_fmri.config import dataset_initialize, get_data_dir


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Isolate config by pointing XDG_CONFIG_HOME to tmp."""
    config_home = tmp_path / "config_home"
    config_home.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    return config_home


def test_get_data_dir_raises_when_not_set(isolated_config):
    with pytest.raises(DataDirNotSetError):
        get_data_dir()


def test_set_and_get_data_dir_roundtrip(isolated_config, tmp_path):
    data_path = tmp_path / "my_data"
    data_path.mkdir()
    dataset_initialize(str(data_path))
    assert get_data_dir() == str(data_path)


def test_dataset_initialize_creates_config_file(isolated_config, tmp_path):
    data_path = tmp_path / "my_data"
    data_path.mkdir()
    dataset_initialize(str(data_path))

    config_file = isolated_config / "laion_fmri" / "config.json"
    assert config_file.exists()

    config = json.loads(config_file.read_text())
    assert config["data_dir"] == str(data_path)


def test_dataset_initialize_creates_metadata_dir(isolated_config, tmp_path):
    data_path = tmp_path / "my_data"
    data_path.mkdir()
    dataset_initialize(str(data_path))

    meta_dir = data_path / ".laion_fmri"
    assert meta_dir.is_dir()


def test_dataset_initialize_validates_string_type(isolated_config):
    with pytest.raises(TypeError):
        dataset_initialize(123)
    with pytest.raises(TypeError):
        dataset_initialize(None)


def test_dataset_initialize_validates_directory_exists(
    isolated_config, tmp_path,
):
    nonexistent = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        dataset_initialize(str(nonexistent))


def test_dataset_initialize_overwrites_previous(isolated_config, tmp_path):
    path1 = tmp_path / "data1"
    path1.mkdir()
    path2 = tmp_path / "data2"
    path2.mkdir()

    dataset_initialize(str(path1))
    assert get_data_dir() == str(path1)

    dataset_initialize(str(path2))
    assert get_data_dir() == str(path2)


def test_config_respects_xdg_config_home(tmp_path, monkeypatch):
    custom_config = tmp_path / "custom_xdg"
    custom_config.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(custom_config))

    data_path = tmp_path / "data"
    data_path.mkdir()
    dataset_initialize(str(data_path))

    config_file = custom_config / "laion_fmri" / "config.json"
    assert config_file.exists()
