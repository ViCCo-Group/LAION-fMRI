"""Access the LAION-fMRI stimulus images and per-stimulus modalities.

Use after the stimuli have been downloaded via
:func:`laion_fmri.download.download_stimuli` (or
``laion-fmri download-stimuli``).

The :class:`Stimuli` object is a single entry point for everything
that is attached *per stimulus image*:

* ``stim.metadata``      -- the stimulus index (image_name, dataset, …)
* ``stim.images``        -- the JPEG images themselves
* ``stim.embeddings``    -- pretrained image embeddings (CLIP, DINOv2, …)
* ``stim.segmentations`` -- object-level segmentation masks

The auxiliary modalities (``embeddings``, ``segmentations``) are lazy:
their HDF5 files are not opened until you touch them, and they remain
optional downloads.

Quick start
-----------

>>> import laion_fmri
>>> stim = laion_fmri.load_stimuli()
>>> stim.metadata.head()
>>> img  = stim.images.get("shared_12rep_LAION_cluster_1003_i0.jpg")  # PIL.Image
>>> feat = stim.embeddings.get("CLIP", "shared_12rep_LAION_cluster_1003_i0.jpg")
>>> mask = stim.segmentations.get(
...     "shared_12rep_LAION_cluster_1003_i0.jpg", "fingers"
... )
"""

from __future__ import annotations

from functools import cached_property
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

import h5py
import pandas as pd

from laion_fmri._paths import (
    stimuli_h5_path,
    stimuli_metadata_path,
)
from laion_fmri.config import get_data_dir

if TYPE_CHECKING:
    from laion_fmri.embeddings import Embeddings
    from laion_fmri.segmentations import Segmentations


class _StimulusImages:
    """Per-image access namespace owned by :class:`Stimuli`.

    Reached via ``stim.images``. Exposes raw JPEG bytes (``stim.images[name]``)
    and decoded :class:`PIL.Image.Image` (``stim.images.get(name)``).
    """

    def __init__(self, stim: "Stimuli"):
        self._stim = stim

    @property
    def metadata(self) -> pd.DataFrame:
        """Same DataFrame as :attr:`Stimuli.metadata`."""
        return self._stim.metadata

    def __len__(self) -> int:
        return len(self._stim.metadata)

    def __getitem__(self, key) -> bytes:
        """Raw JPEG bytes for one stimulus, by integer index or image_name."""
        idx = self._stim._resolve(key)
        return bytes(self._stim._images_ds()[idx])

    def get(self, key):
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

    def __contains__(self, key) -> bool:
        if isinstance(key, str):
            return key in (self._stim._name_to_idx_dict())
        if isinstance(key, int):
            return 0 <= key < len(self._stim.metadata)
        return False

    def __iter__(self) -> Iterator[tuple[str, bytes]]:
        """Iterate ``(image_name, raw_jpeg_bytes)`` in metadata order."""
        names = self._stim.metadata["image_name"].tolist()
        ds = self._stim._images_ds()
        for i, name in enumerate(names):
            yield name, bytes(ds[i])

    def index_of(self, name: str) -> int:
        """HDF5 row index for an image name."""
        idx = self._stim._name_to_idx_dict().get(name)
        if idx is None:
            raise KeyError(f"Unknown stimulus name: {name!r}")
        return idx

    def names(self) -> list[str]:
        """All image names, in metadata order."""
        return self._stim.metadata["image_name"].tolist()


class Stimuli:
    """Hub for all per-stimulus data: images, embeddings, segmentations.

    Opens the stimuli HDF5 file lazily on first image access and keeps
    the handle open for the lifetime of the instance. Use as a context
    manager to explicitly release all open handles::

        with Stimuli() as stim:
            img = stim.images.get("...")

    Parameters
    ----------
    data_dir : str or Path, optional
        Override the configured data directory. Defaults to
        :func:`laion_fmri.config.get_data_dir`.
    """

    def __init__(self, data_dir: str | Path | None = None):
        self.data_dir = Path(data_dir) if data_dir is not None else Path(get_data_dir())
        self._h5_path = stimuli_h5_path(self.data_dir)
        self._csv_path = stimuli_metadata_path(self.data_dir)
        if not self._h5_path.exists() or not self._csv_path.exists():
            raise FileNotFoundError(
                f"stimuli not found on disk under {self.data_dir / 'stimuli'}. "
                "Run `laion-fmri download-stimuli` first "
                "(see https://laion-fmri.hebartlab.com/request)."
            )
        self._h5: h5py.File | None = None
        self._meta: pd.DataFrame | None = None
        self._name_to_idx: dict[str, int] | None = None
        self._images_ns = _StimulusImages(self)

    # ── lifecycle ──────────────────────────────────────────────

    def __enter__(self) -> "Stimuli":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        """Release every open HDF5 handle (images + lazily-loaded modalities)."""
        if self._h5 is not None:
            self._h5.close()
            self._h5 = None
        # Close sub-modalities if they were ever opened.
        for attr in ("embeddings", "segmentations"):
            ns = self.__dict__.get(attr)
            if ns is not None and hasattr(ns, "close"):
                ns.close()
                # Clear the cached_property so a future access reopens cleanly.
                self.__dict__.pop(attr, None)

    # ── metadata ──────────────────────────────────────────────

    @property
    def metadata(self) -> pd.DataFrame:
        """Stimulus metadata CSV as a pandas DataFrame.

        Columns: ``image_name``, ``dataset``, ``participant``,
        ``unique_or_shared``, ``n_reps``. Row order matches the
        stimuli HDF5 index.
        """
        if self._meta is None:
            self._meta = pd.read_csv(self._csv_path)
            self._name_to_idx = {
                n: i for i, n in enumerate(self._meta["image_name"])
            }
        return self._meta

    # ── modality namespaces ───────────────────────────────────

    @property
    def images(self) -> _StimulusImages:
        """Per-image access (raw bytes and decoded PIL)."""
        return self._images_ns

    @cached_property
    def embeddings(self) -> "Embeddings":
        """Pretrained image embeddings.

        Loads every model whose HDF5 file is present on disk. If no
        embedding files are downloaded, accessing this property raises
        :class:`FileNotFoundError` with installation guidance.
        """
        from laion_fmri.embeddings import AVAILABLE_MODELS, Embeddings
        from laion_fmri._paths import embeddings_h5_path

        present = [
            m for m in AVAILABLE_MODELS
            if embeddings_h5_path(self.data_dir, m).exists()
        ]
        if not present:
            raise FileNotFoundError(
                f"No embedding files found under {self.data_dir / 'stimuli'}. "
                "Run `laion-fmri download-embeddings` first."
            )
        return Embeddings(tuple(present), data_dir=self.data_dir)

    @cached_property
    def segmentations(self) -> "Segmentations":
        """Object-level segmentation masks (one per detected noun-instance).

        Lazily opens ``task-images_desc-segmentations.h5``. Raises
        :class:`FileNotFoundError` if not downloaded yet.
        """
        from laion_fmri.segmentations import Segmentations
        return Segmentations(data_dir=self.data_dir)

    # ── internals ─────────────────────────────────────────────

    def _images_ds(self) -> h5py.Dataset:
        if self._h5 is None:
            self._h5 = h5py.File(self._h5_path, "r")
        return self._h5["images"]

    def _name_to_idx_dict(self) -> dict[str, int]:
        _ = self.metadata
        return self._name_to_idx or {}

    def _resolve(self, key) -> int:
        if isinstance(key, int):
            n = len(self.metadata)
            if not 0 <= key < n:
                raise IndexError(
                    f"Stimulus index {key} out of range [0, {n})."
                )
            return key
        if isinstance(key, str):
            return self.images.index_of(key)
        raise TypeError(
            f"Stimulus key must be int or str; got {type(key).__name__}."
        )


# ── module-level loader ───────────────────────────────────────


def load_stimuli(data_dir: str | Path | None = None) -> Stimuli:
    """Return a :class:`Stimuli` handle to the local stimuli.

    The naming mirrors :func:`laion_fmri.subject.load_subject` -- the
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
        If the stimuli haven't been downloaded yet. Run
        :func:`laion_fmri.download.download_stimuli` first.
    """
    return Stimuli(data_dir=data_dir)
