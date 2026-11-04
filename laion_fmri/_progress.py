"""One-line download progress on stderr, for multi-file S3 fetches."""

import sys
import time

from laion_fmri._stimulus_access import _format_bytes


class DownloadProgress:
    """Files and bytes done out of a known total, redrawn in place.

    Redraws at most every 0.25 s, like the stimulus download, and
    always once on :meth:`close`.

    Parameters
    ----------
    label : str
        What is being downloaded, e.g. an S3 prefix.
    total_files : int
    total_bytes : int
    stream : file-like, optional
        Defaults to ``sys.stderr``.
    """

    def __init__(self, label, total_files, total_bytes, stream=None):
        self.label = label
        self.total_files = total_files
        self.total_bytes = total_bytes
        self.files = 0
        self.bytes = 0
        self.stream = stream if stream is not None else sys.stderr
        self._last_draw = 0.0

    def advance(self, n_bytes):
        """Count one finished file of ``n_bytes``."""
        self.files += 1
        self.bytes += n_bytes
        if time.monotonic() - self._last_draw > 0.25:
            self._draw()

    def close(self):
        self._draw()
        self.stream.write("\n")
        self.stream.flush()

    def _draw(self):
        pct = (
            100.0 * self.bytes / self.total_bytes
            if self.total_bytes else 100.0
        )
        self.stream.write(
            f"\r  {self.label}: {self.files}/{self.total_files} files, "
            f"{_format_bytes(self.bytes)} / "
            f"{_format_bytes(self.total_bytes)} ({pct:.1f}%)   "
        )
        self.stream.flush()
        self._last_draw = time.monotonic()
