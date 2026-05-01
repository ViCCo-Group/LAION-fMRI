"""AWS S3 operations wrapping the official AWS CLI.

All S3 listing, copying, and syncing are delegated to the ``aws``
command provided by the ``awscli`` pip dependency. No other AWS
SDK is imported.

The LAION-fMRI bucket is public, so every call is made with
``--no-sign-request``. No AWS credentials are read or set.
"""

import json
import subprocess
from pathlib import Path

from laion_fmri._sources import LAION_FMRI_REGION


def _aws(subcommand_args, capture=True):
    """Run an ``aws`` subprocess with region and anonymous signing.

    Parameters
    ----------
    subcommand_args : list[str]
        Arguments after the ``aws`` command itself, e.g.
        ``["s3", "cp", ...]`` or ``["s3api", "list-objects-v2", ...]``.
    capture : bool
        If True, capture stdout/stderr. If False, let them stream
        to the user's terminal (useful for progress bars).

    Returns
    -------
    subprocess.CompletedProcess
    """
    cmd = [
        "aws", *subcommand_args,
        "--region", LAION_FMRI_REGION,
        "--no-sign-request",
    ]
    return subprocess.run(
        cmd, capture_output=capture, check=True, text=True,
    )


def list_prefix_keys(bucket, prefix):
    """List all object keys under a bucket prefix.

    Parameters
    ----------
    bucket : str
        Bucket name.
    prefix : str
        Key prefix.

    Returns
    -------
    list of str
        All object keys under the prefix.
    """
    result = _aws([
        "s3api", "list-objects-v2",
        "--bucket", bucket,
        "--prefix", prefix,
        "--output", "json",
    ])
    data = json.loads(result.stdout) if result.stdout.strip() else {}
    return [obj["Key"] for obj in data.get("Contents", [])]


def list_prefix_objects(bucket, prefix):
    """List all objects under a bucket prefix with their sizes.

    Returns
    -------
    list of dict
        Each item has ``"Key"`` (str) and ``"Size"`` (int, bytes).
    """
    result = _aws([
        "s3api", "list-objects-v2",
        "--bucket", bucket,
        "--prefix", prefix,
        "--output", "json",
    ])
    data = json.loads(result.stdout) if result.stdout.strip() else {}
    return [
        {"Key": obj["Key"], "Size": int(obj["Size"])}
        for obj in data.get("Contents", [])
    ]


def list_common_prefixes(bucket, prefix):
    """List the immediate sub-prefix names under ``prefix``.

    Parameters
    ----------
    bucket : str
        Bucket name.
    prefix : str
        Key prefix to list under (include the trailing slash).

    Returns
    -------
    list of str
        Sub-prefix names, with ``prefix`` stripped.
    """
    result = _aws([
        "s3api", "list-objects-v2",
        "--bucket", bucket,
        "--prefix", prefix,
        "--delimiter", "/",
        "--output", "json",
    ])
    data = json.loads(result.stdout) if result.stdout.strip() else {}
    names = []
    for cp in data.get("CommonPrefixes", []):
        name = cp["Prefix"][len(prefix):].rstrip("/")
        if name:
            names.append(name)
    return names


def download_key(bucket, key, dest_path):
    """Download a single S3 object via ``aws s3 cp``.

    Parameters
    ----------
    bucket : str
    key : str
    dest_path : str or Path

    Returns
    -------
    Path
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    _aws(
        ["s3", "cp", f"s3://{bucket}/{key}", str(dest_path)],
        capture=False,
    )
    return dest_path


def sync_prefix(bucket, prefix, local_root):
    """Mirror all objects under ``prefix`` into ``local_root``.

    Wraps ``aws s3 sync``. The S3 key layout is preserved under
    ``local_root``.

    Parameters
    ----------
    bucket : str
    prefix : str
        Key prefix (include trailing slash).
    local_root : str or Path
        Local root directory to mirror into.

    Returns
    -------
    list of str
        S3 keys that were actually downloaded (does not include
        files that were already up to date).
    """
    local_dest = Path(local_root) / prefix
    local_dest.mkdir(parents=True, exist_ok=True)
    result = _aws([
        "s3", "sync",
        f"s3://{bucket}/{prefix}",
        str(local_dest),
        "--no-progress",
    ])

    downloaded = []
    uri_prefix = f"s3://{bucket}/"
    for line in result.stdout.splitlines():
        if not line.startswith("download:"):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1].startswith(uri_prefix):
            downloaded.append(parts[1][len(uri_prefix):])
    return downloaded
