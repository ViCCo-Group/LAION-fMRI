"""Tests for the one-line download progress."""

import io
from unittest.mock import patch

from laion_fmri._laion_fmri_fetch import _filtered_download
from laion_fmri._progress import DownloadProgress


def test_progress_reports_files_and_bytes():
    out = io.StringIO()
    progress = DownloadProgress("prefix/", 2, 2048, stream=out)
    progress.advance(1024)
    progress.advance(1024)
    progress.close()
    assert "prefix/: 2/2 files, 2.0 KB / 2.0 KB (100.0%)" in out.getvalue()
    assert out.getvalue().endswith("\n")


def test_progress_handles_zero_total():
    out = io.StringIO()
    DownloadProgress("empty/", 0, 0, stream=out).close()
    assert "(100.0%)" in out.getvalue()


@patch("laion_fmri._laion_fmri_fetch.download_key")
@patch("laion_fmri._laion_fmri_fetch.list_prefix_objects")
def test_filtered_download_reports_progress(
    mock_list, mock_download_key, tmp_path, capsys,
):
    mock_list.return_value = [
        {"Key": "derivatives/retinotopy/sub-03/a.nii.gz", "Size": 10},
        {"Key": "derivatives/retinotopy/sub-03/b.nii.gz", "Size": 30},
    ]
    _filtered_download(
        "bucket", "derivatives/retinotopy/sub-03/", str(tmp_path), {},
    )
    err = capsys.readouterr().err
    assert "derivatives/retinotopy/sub-03/: 2/2 files" in err


@patch("laion_fmri._laion_fmri_fetch.download_key")
@patch("laion_fmri._laion_fmri_fetch.list_prefix_objects")
def test_filtered_download_silent_when_nothing_to_fetch(
    mock_list, mock_download_key, tmp_path, capsys,
):
    mock_list.return_value = []
    _filtered_download("bucket", "empty/", str(tmp_path), {})
    assert capsys.readouterr().err == ""
