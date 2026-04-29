"""Configuration management for laion_fmri."""

import json
import os
from pathlib import Path

from laion_fmri._errors import DataDirNotSetError
from laion_fmri._sources import LAION_FMRI_REGION


def _get_config_path():
    """Return the path to the config JSON file."""
    config_home = os.environ.get(
        "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
    )
    return Path(config_home) / "laion_fmri" / "config.json"


def dataset_initialize(path):
    """Initialize the dataset by setting and persisting the data directory.

    Parameters
    ----------
    path : str
        Path to the data directory. Must exist on disk.

    Raises
    ------
    TypeError
        If path is not a string.
    FileNotFoundError
        If the directory does not exist.
    """
    if not isinstance(path, str):
        raise TypeError(
            f"path must be a string, got {type(path).__name__}"
        )

    data_path = Path(path)
    if not data_path.is_dir():
        raise FileNotFoundError(
            f"Data directory does not exist: {path}"
        )

    # Create .laion_fmri metadata directory inside data dir
    meta_dir = data_path / ".laion_fmri"
    meta_dir.mkdir(exist_ok=True)

    # Persist config
    config_file = _get_config_path()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config = {"data_dir": str(data_path)}
    config_file.write_text(json.dumps(config, indent=2))


def get_data_dir():
    """Read the persisted data directory.

    Returns
    -------
    str
        The configured data directory path.

    Raises
    ------
    DataDirNotSetError
        If no data directory has been configured.
    """
    config_file = _get_config_path()
    if not config_file.exists():
        raise DataDirNotSetError(
            "Data directory is not configured. "
            "Run: from laion_fmri.config import dataset_initialize; "
            "dataset_initialize('/path/to/data')"
        )

    config = json.loads(config_file.read_text())
    return config["data_dir"]


def set_aws_credentials(
    access_key_id,
    secret_access_key,
    region=None,
    session_token=None,
):
    """Set AWS credentials for the current Python process.

    Exports ``AWS_ACCESS_KEY_ID``, ``AWS_SECRET_ACCESS_KEY``, and
    ``AWS_DEFAULT_REGION`` so that the AWS CLI resolves them on
    subsequent S3 operations. No ``aws configure`` step or
    ``~/.aws/credentials`` file is required.

    Credentials are kept only in this process's environment and are
    not written to disk.

    Parameters
    ----------
    access_key_id : str
        AWS access key ID.
    secret_access_key : str
        AWS secret access key.
    region : str or None
        AWS region. Defaults to the LAION-fMRI bucket region.
    session_token : str or None
        Optional AWS session token (for temporary credentials).
    """
    os.environ["AWS_ACCESS_KEY_ID"] = access_key_id
    os.environ["AWS_SECRET_ACCESS_KEY"] = secret_access_key
    os.environ["AWS_DEFAULT_REGION"] = region or LAION_FMRI_REGION
    if session_token is not None:
        os.environ["AWS_SESSION_TOKEN"] = session_token
