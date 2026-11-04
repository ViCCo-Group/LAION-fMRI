"""Tests for the one-line download progress."""

import io
from unittest.mock import patch

from laion_fmri._laion_fmri_fetch import _filtered_download
from laion_fmri._progress import DownloadProgress


def test_progress_reports_files_and_bytes():
    out = io.StringIO()
    progress = DownloadProgress("prefix/", 2, 2000, stream=out)
    progress.advance(1000)
    progress.advance(1000)
    progress.close()
    assert "prefix/: 2/2 files, 2.0 KB / 2.0 KB (100.0%)" in out.getvalue()
    assert out.getvalue().endswith("\n")


class _Terminal(io.StringIO):
    def isatty(self):
        return True


def test_progress_off_a_terminal_writes_only_the_final_line():
    """A log file, CI or the docs gallery would turn every \\r redraw
    into a line of its own."""
    out = io.StringIO()
    progress = DownloadProgress("prefix/", 3, 3000, stream=out)
    for _ in range(3):
        progress.advance(1000)
    progress.close()
    assert out.getvalue() == (
        "  prefix/: 3/3 files, 3.0 KB / 3.0 KB (100.0%)\n"
    )


def test_progress_on_a_terminal_redraws_in_place():
    out = _Terminal()
    progress = DownloadProgress("prefix/", 2, 2000, stream=out)
    progress.advance(1000)              # first redraw is never throttled
    progress.close()
    text = out.getvalue()
    assert text.count("\r") == 2
    assert "\r  prefix/: 1/2 files" in text
    assert text.endswith("(50.0%)   \n")


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


def test_sizes_are_decimal_like_s3():
    """17,002,104 bytes (the aperture libraries) read 17.0 MB, as in
    ``aws s3 ls --summarize``, not 16.2."""
    from laion_fmri._stimulus_access import _format_bytes

    assert _format_bytes(17_002_104) == "17.0 MB"
    assert _format_bytes(999) == "999.0 B"
    assert _format_bytes(1000) == "1.0 KB"
