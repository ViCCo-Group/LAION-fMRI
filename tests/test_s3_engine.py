"""Tests for the S3 engine wrapping the AWS CLI."""

import json
import subprocess
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from laion_fmri._s3_engine import (
    download_key,
    list_common_prefixes,
    list_prefix_keys,
    list_prefix_objects,
    sync_prefix,
)


def _completed(stdout="", stderr="", returncode=0):
    """Build a CompletedProcess-like object for mocks."""
    return SimpleNamespace(
        stdout=stdout, stderr=stderr, returncode=returncode,
    )


# ── _aws subprocess shape ───────────────────────────────────────


@patch("laion_fmri._s3_engine.subprocess.run")
def test_cli_always_includes_region_and_no_sign_request(mock_run):
    """The bucket is public; every aws call goes anonymous."""
    mock_run.return_value = _completed(stdout='{"Contents":[]}')

    list_prefix_keys("laion-fmri", "x/")

    cmd = mock_run.call_args.args[0]
    assert cmd[0] == "aws"
    assert "--region" in cmd
    assert "us-west-2" in cmd
    assert "--no-sign-request" in cmd


# ── list_prefix_keys ────────────────────────────────────────────


@patch("laion_fmri._s3_engine.subprocess.run")
def test_list_prefix_keys_parses_contents(mock_run):
    payload = {
        "Contents": [
            {"Key": "a/1.txt"},
            {"Key": "a/2.txt"},
        ],
    }
    mock_run.return_value = _completed(stdout=json.dumps(payload))

    assert list_prefix_keys("laion-fmri", "a/") == [
        "a/1.txt",
        "a/2.txt",
    ]


@patch("laion_fmri._s3_engine.subprocess.run")
def test_list_prefix_keys_empty_response(mock_run):
    mock_run.return_value = _completed(stdout="")
    assert list_prefix_keys("laion-fmri", "x/") == []


@patch("laion_fmri._s3_engine.subprocess.run")
def test_list_prefix_keys_uses_list_objects_v2(mock_run):
    mock_run.return_value = _completed(stdout="")
    list_prefix_keys("laion-fmri", "a/")
    cmd = mock_run.call_args.args[0]
    assert cmd[:3] == ["aws", "s3api", "list-objects-v2"]
    assert "--bucket" in cmd
    assert "laion-fmri" in cmd
    assert "--prefix" in cmd
    assert "a/" in cmd


# ── list_prefix_objects (key + size) ────────────────────────────


@patch("laion_fmri._s3_engine.subprocess.run")
def test_list_prefix_objects_parses_size(mock_run):
    payload = {
        "Contents": [
            {"Key": "a/1.txt", "Size": 100},
            {"Key": "a/2.txt", "Size": 250},
        ],
    }
    mock_run.return_value = _completed(stdout=json.dumps(payload))

    objs = list_prefix_objects("laion-fmri", "a/")
    assert objs == [
        {"Key": "a/1.txt", "Size": 100},
        {"Key": "a/2.txt", "Size": 250},
    ]


@patch("laion_fmri._s3_engine.subprocess.run")
def test_list_prefix_objects_empty(mock_run):
    mock_run.return_value = _completed(stdout="")
    assert list_prefix_objects("laion-fmri", "x/") == []


# ── list_common_prefixes ────────────────────────────────────────


@patch("laion_fmri._s3_engine.subprocess.run")
def test_list_common_prefixes_parses_names(mock_run):
    payload = {
        "CommonPrefixes": [
            {"Prefix": "derivatives/glmsingle-tedana/sub-01/"},
            {"Prefix": "derivatives/glmsingle-tedana/sub-03/"},
        ],
    }
    mock_run.return_value = _completed(stdout=json.dumps(payload))

    names = list_common_prefixes(
        "laion-fmri", "derivatives/glmsingle-tedana/",
    )
    assert names == ["sub-01", "sub-03"]


@patch("laion_fmri._s3_engine.subprocess.run")
def test_list_common_prefixes_uses_delimiter(mock_run):
    mock_run.return_value = _completed(stdout="")
    list_common_prefixes("laion-fmri", "a/")
    cmd = mock_run.call_args.args[0]
    assert "--delimiter" in cmd
    idx = cmd.index("--delimiter")
    assert cmd[idx + 1] == "/"


# ── download_key ────────────────────────────────────────────────


@patch("laion_fmri._s3_engine.subprocess.run")
def test_download_key_runs_s3_cp(mock_run, tmp_path):
    mock_run.return_value = _completed()
    dest = tmp_path / "out" / "file.bin"

    download_key("laion-fmri", "a/file.bin", dest)

    cmd = mock_run.call_args.args[0]
    assert cmd[:3] == ["aws", "s3", "cp"]
    assert "s3://laion-fmri/a/file.bin" in cmd
    assert str(dest) in cmd


@patch("laion_fmri._s3_engine.subprocess.run")
def test_download_key_creates_parent_dirs(mock_run, tmp_path):
    mock_run.return_value = _completed()
    dest = tmp_path / "deep" / "nested" / "x.bin"

    download_key("bucket", "key", dest)

    assert dest.parent.exists()


# ── sync_prefix ─────────────────────────────────────────────────


@patch("laion_fmri._s3_engine.subprocess.run")
def test_sync_prefix_runs_s3_sync(mock_run, tmp_path):
    mock_run.return_value = _completed(stdout="")
    sync_prefix("laion-fmri", "a/", tmp_path)

    cmd = mock_run.call_args.args[0]
    assert cmd[:3] == ["aws", "s3", "sync"]
    assert "s3://laion-fmri/a/" in cmd
    assert str(tmp_path / "a") in cmd


@patch("laion_fmri._s3_engine.subprocess.run")
def test_sync_prefix_parses_downloaded_keys(mock_run, tmp_path):
    stdout = (
        "download: s3://laion-fmri/a/1.txt to /tmp/a/1.txt\n"
        "download: s3://laion-fmri/a/2.txt to /tmp/a/2.txt\n"
    )
    mock_run.return_value = _completed(stdout=stdout)

    downloaded = sync_prefix("laion-fmri", "a/", tmp_path)
    assert downloaded == ["a/1.txt", "a/2.txt"]


@patch("laion_fmri._s3_engine.subprocess.run")
def test_sync_prefix_returns_empty_when_nothing_to_download(
    mock_run, tmp_path,
):
    mock_run.return_value = _completed(stdout="")
    assert sync_prefix("laion-fmri", "a/", tmp_path) == []


@patch("laion_fmri._s3_engine.subprocess.run")
def test_sync_prefix_ignores_non_download_lines(mock_run, tmp_path):
    stdout = (
        "Completed 1.0 MiB/1.0 MiB (500 KiB/s)\n"
        "download: s3://laion-fmri/a/1.txt to /tmp/a/1.txt\n"
        "upload: x (should never happen but guard against it)\n"
    )
    mock_run.return_value = _completed(stdout=stdout)

    downloaded = sync_prefix("laion-fmri", "a/", tmp_path)
    assert downloaded == ["a/1.txt"]


# ── error propagation ───────────────────────────────────────────


@patch("laion_fmri._s3_engine.subprocess.run")
def test_cli_failure_propagates_as_called_process_error(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=["aws"], stderr="denied",
    )
    with pytest.raises(subprocess.CalledProcessError):
        list_prefix_keys("laion-fmri", "x/")
