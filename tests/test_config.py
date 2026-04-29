import json
import os

import pytest

from laion_fmri._errors import DataDirNotSetError
from laion_fmri.config import (
    dataset_initialize,
    get_data_dir,
    set_aws_credentials,
)


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


# ── set_aws_credentials ─────────────────────────────────────────


def test_set_aws_credentials_sets_env_vars(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)

    set_aws_credentials(
        access_key_id="AKIAEXAMPLE",
        secret_access_key="secret-example",
        region="us-west-2",
    )

    assert os.environ["AWS_ACCESS_KEY_ID"] == "AKIAEXAMPLE"
    assert os.environ["AWS_SECRET_ACCESS_KEY"] == "secret-example"
    assert os.environ["AWS_DEFAULT_REGION"] == "us-west-2"


def test_set_aws_credentials_region_defaults_to_bucket_region(
    monkeypatch,
):
    from laion_fmri._sources import LAION_FMRI_REGION

    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)

    set_aws_credentials(
        access_key_id="AKIAEXAMPLE",
        secret_access_key="secret-example",
    )

    assert os.environ["AWS_DEFAULT_REGION"] == LAION_FMRI_REGION


def test_set_aws_credentials_accepts_optional_session_token(
    monkeypatch,
):
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)

    set_aws_credentials(
        access_key_id="AKIAEXAMPLE",
        secret_access_key="secret-example",
        session_token="session-token-example",
    )

    assert os.environ["AWS_SESSION_TOKEN"] == "session-token-example"


def test_set_aws_credentials_does_not_set_session_token_by_default(
    monkeypatch,
):
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)

    set_aws_credentials(
        access_key_id="AKIAEXAMPLE",
        secret_access_key="secret-example",
    )

    assert "AWS_SESSION_TOKEN" not in os.environ


def test_set_aws_credentials_makes_aws_cli_detect_them(monkeypatch):
    """After set_aws_credentials, has_aws_credentials() returns True."""
    from laion_fmri._s3_engine import has_aws_credentials

    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    set_aws_credentials(
        access_key_id="AKIAEXAMPLE",
        secret_access_key="secret-example",
    )

    assert has_aws_credentials() is True


def test_set_aws_credentials_validates_required_args():
    with pytest.raises(TypeError):
        set_aws_credentials(access_key_id="x")  # missing secret
    with pytest.raises(TypeError):
        set_aws_credentials(secret_access_key="y")  # missing key
