"""Access the LAION-fMRI stimulus images from local cache.

Use after the stimulus archive has been downloaded via
:func:`laion_fmri.download.download_stimuli` (or
``laion-fmri download-stimuli``).

The archive on disk is one HDF5 file with a 1-D ``images`` dataset of
variable-length byte strings (raw JPEG bytes), aligned by index to the
metadata CSV. The :class:`Stimuli` class lazily memory-maps the HDF5
and exposes name-keyed access plus optional PIL decoding.

Quick start
-----------

>>> import laion_fmri
>>> stim = laion_fmri.load_stimuli()      # mirrors load_subject(...)
>>> stim.metadata.head()                  # pandas DataFrame: name, dataset, ...
>>> jpeg_bytes = stim["shared_12rep_LAION_cluster_1003_i0.jpg"]
>>> img = stim.image(0)                   # PIL.Image (requires Pillow)
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Iterator

import h5py
import pandas as pd

from laion_fmri._paths import (
    stimuli_h5_path,
    stimuli_metadata_csv_path,
)
from laion_fmri.config import get_data_dir


class Stimuli:
    """Lazy reader for the local stimulus archive.

    Opens the HDF5 file once on first access and keeps the handle open
    for the lifetime of the instance. Use as a context manager to
    explicitly close::

        with Stimuli() as stim:
            img = stim.image("...")

    Parameters
    ----------
    data_dir : str or Path, optional
        Override the configured data directory. Defaults to
        :func:`laion_fmri.config.get_data_dir`.
    """

    def __init__(self, data_dir: str | Path | None = None):
        self.data_dir = Path(data_dir) if data_dir is not None else Path(get_data_dir())
        self._h5_path = stimuli_h5_path(self.data_dir)
        self._csv_path = stimuli_metadata_csv_path(self.data_dir)
        if not self._h5_path.exists() or not self._csv_path.exists():
            raise FileNotFoundError(
                f"Stimulus archive not found under {self.data_dir / 'stimuli'}. "
                "Run `laion-fmri download --include-stimuli` first "
                "(see https://laion-fmri.hebartlab.com/request)."
            )
        self._h5: h5py.File | None = None
        self._meta: pd.DataFrame | None = None
        self._name_to_idx: dict[str, int] | None = None

    # ── lifecycle ──────────────────────────────────────────────

    def __enter__(self) -> "Stimuli":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        """Release the HDF5 handle."""
        if self._h5 is not None:
            self._h5.close()
            self._h5 = None

    # ── metadata ──────────────────────────────────────────────

    @property
    def metadata(self) -> pd.DataFrame:
        """Stimulus metadata CSV as a pandas DataFrame.

        Columns: ``image_name``, ``dataset``, ``participant``,
        ``unique_or_shared``, ``n_reps``. Row order matches the HDF5
        index.
        """
        if self._meta is None:
            self._meta = pd.read_csv(self._csv_path)
            self._name_to_idx = {
                n: i for i, n in enumerate(self._meta["image_name"])
            }
        return self._meta

    # ── HDF5 access ───────────────────────────────────────────

    def _images_ds(self) -> h5py.Dataset:
        if self._h5 is None:
            self._h5 = h5py.File(self._h5_path, "r")
        return self._h5["images"]

    def __len__(self) -> int:
        return len(self.metadata)

    def __getitem__(self, key: int | str) -> bytes:
        """Return raw JPEG bytes for one stimulus.

        ``key`` can be an integer index (0-based, matching the metadata
        row order) or a string image name from the metadata's
        ``image_name`` column.
        """
        idx = self._resolve(key)
        return bytes(self._images_ds()[idx])

    def image(self, key: int | str):
        """Decoded :class:`PIL.Image.Image` for one stimulus.

        Requires Pillow (``pip install laion_fmri[images]``).
        """
        try:
            from PIL import Image  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Decoding stimulus images requires Pillow. "
                "Install it via `pip install laion_fmri[images]`."
            ) from exc
        return Image.open(BytesIO(self[key]))

    def __contains__(self, key: int | str) -> bool:
        _ = self.metadata
        if isinstance(key, str):
            return key in (self._name_to_idx or {})
        if isinstance(key, int):
            return 0 <= key < len(self.metadata)
        return False

    def __iter__(self) -> Iterator[tuple[str, bytes]]:
        """Iterate ``(image_name, raw_jpeg_bytes)`` in metadata order."""
        names = self.metadata["image_name"].tolist()
        ds = self._images_ds()
        for i, name in enumerate(names):
            yield name, bytes(ds[i])

    def index_of(self, name: str) -> int:
        """HDF5 index for an image name."""
        _ = self.metadata
        idx = (self._name_to_idx or {}).get(name)
        if idx is None:
            raise KeyError(f"Unknown stimulus name: {name!r}")
        return idx

    def names(self) -> list[str]:
        """All image names, in metadata order."""
        return self.metadata["image_name"].tolist()

    # ── internals ─────────────────────────────────────────────

    def _resolve(self, key: int | str) -> int:
        _ = self.metadata
        if isinstance(key, int):
            n = len(self.metadata)
            if not 0 <= key < n:
                raise IndexError(
                    f"Stimulus index {key} out of range [0, {n})."
                )
            return key
        if isinstance(key, str):
            return self.index_of(key)
        raise TypeError(
            f"Stimulus key must be int or str; got {type(key).__name__}."
        )


# ── module-level loader (mirrors load_subject(...)) ──────────


def load_stimuli(data_dir: str | Path | None = None) -> Stimuli:
    """Return a :class:`Stimuli` handle to the local stimulus archive.

    The naming mirrors :func:`laion_fmri.subject.load_subject` — the
    package-level convention is ``load_X(...)`` returning a handle
    object you then call methods on.

    Parameters
    ----------
    data_dir : str or Path, optional
        Override the configured data directory.

    Returns
    -------
    Stimuli
        A handle to the on-disk HDF5 + metadata CSV.

    Raises
    ------
    FileNotFoundError
        If the archive has not been downloaded yet. Run
        :func:`laion_fmri.download.download_stimuli` first.
    """
    return Stimuli(data_dir=data_dir)
