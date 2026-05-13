"""Access pretrained image embeddings for the LAION-fMRI stimuli.

Use after the embeddings have been downloaded via
:func:`laion_fmri.download.download_embeddings` (or
``laion-fmri download-embeddings``).

The embeddings live as one HDF5 file per model, sitting next to the
stimulus images:

.. code-block:: text

   stimuli/
     task-images_stimuli.h5
     task-images_metadata.csv
     task-images_desc-CLIP_embeddings.h5
     task-images_desc-DINOv2_embeddings.h5
     task-images_desc-PEcore_embeddings.h5
     task-images_desc-SigLIP2_embeddings.h5

Each file has three datasets of length 25,052: ``embedding`` (the
``(N, feature_dim)`` float16 matrix), ``image_ids`` (image filenames),
and ``valid`` (per-row validity flag). All four files share the same
``image_ids`` order.

You normally do not construct :class:`Embeddings` directly. Reach it
through the :class:`~laion_fmri.Stimuli` hub:

>>> import laion_fmri
>>> stim = laion_fmri.load_stimuli()
>>> stim.embeddings["CLIP"].shape          # (25052, 1024)
>>> stim.embeddings.get("CLIP", "shared_12rep_LAION_cluster_1003_i0.jpg")

For subject-aligned arrays, use the Subject namespace:

>>> sub = laion_fmri.load_subject("sub-01")
>>> features = sub.embeddings.all("CLIP")  # (n_trials, D)
"""

from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from laion_fmri._paths import embeddings_h5_path, stimuli_metadata_path
from laion_fmri.config import get_data_dir


#: Models shipped with the LAION-fMRI release. The label is the BIDS
#: ``desc-`` token used in the filename.
AVAILABLE_MODELS = ("CLIP", "DINOv2", "PEcore", "SigLIP2")


class Embeddings:
    """Lazy reader for one or more model embedding files.

    Opens each model's HDF5 on first access and keeps the handle open
    for the lifetime of the instance. Use as a context manager to
    explicitly release the handles::

        with Stimuli() as stim:
            v = stim.embeddings.get("CLIP", "img.jpg")

    Parameters
    ----------
    models : str or iterable[str]
        Model labels this handle covers (subset of
        :data:`AVAILABLE_MODELS`). A single string such as
        ``"CLIP"`` is accepted.
    data_dir : str or Path, optional
        Override the configured data directory.
    """

    def __init__(self, models, data_dir=None):
        self.data_dir = (
            Path(data_dir) if data_dir is not None else Path(get_data_dir())
        )
        if isinstance(models, str):
            self._models = (models,)
        else:
            self._models = tuple(models)
        for m in self._models:
            if m not in AVAILABLE_MODELS:
                raise ValueError(
                    f"Unknown embedding model {m!r}. "
                    f"Available: {list(AVAILABLE_MODELS)}."
                )
            if not embeddings_h5_path(self.data_dir, m).exists():
                raise FileNotFoundError(
                    f"Embeddings for {m!r} not found at "
                    f"{embeddings_h5_path(self.data_dir, m)}. "
                    "Run `laion-fmri download-embeddings` first."
                )
        self._h5s: dict[str, h5py.File] = {}
        self._image_ids: np.ndarray | None = None
        self._name_to_idx: dict[str, int] | None = None
        self._meta: pd.DataFrame | None = None

    # ── lifecycle ──────────────────────────────────────────────

    def __enter__(self) -> "Embeddings":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        """Release every open HDF5 handle."""
        for h in self._h5s.values():
            h.close()
        self._h5s.clear()

    # ── shape / inventory ─────────────────────────────────────

    @property
    def models(self) -> list[str]:
        """Model labels this handle covers, in user-supplied order."""
        return list(self._models)

    @property
    def image_ids(self) -> np.ndarray:
        """Image filenames in embedding row order (shared across models)."""
        if self._image_ids is None:
            h = self._handle(self._models[0])
            raw = h["image_ids"][:]
            # h5py returns bytes for variable-length strings; decode once.
            self._image_ids = np.array(
                [x.decode() if isinstance(x, bytes) else x for x in raw]
            )
            self._name_to_idx = {n: i for i, n in enumerate(self._image_ids)}
        return self._image_ids

    def __len__(self) -> int:
        return len(self.image_ids)

    def __contains__(self, model_or_pair) -> bool:
        if isinstance(model_or_pair, str):
            return model_or_pair in self._models
        if isinstance(model_or_pair, tuple) and len(model_or_pair) == 2:
            model, name = model_or_pair
            if model not in self._models:
                return False
            _ = self.image_ids
            return name in (self._name_to_idx or {})
        return False

    # ── data access ───────────────────────────────────────────

    def __getitem__(self, model: str) -> h5py.Dataset:
        """Return the full ``(N, feature_dim)`` embedding dataset for ``model``.

        This is the raw h5py Dataset — read into memory with
        ``emb["CLIP"][:]`` or slice it directly to stream a subset.
        """
        self._require_model(model)
        return self._handle(model)["embedding"]

    def get(self, model: str, image_name) -> np.ndarray:
        """Return embedding row(s) for one or many image names.

        Parameters
        ----------
        model : str
            One of :data:`AVAILABLE_MODELS`.
        image_name : str or sequence of str
            One image filename or a list/array of filenames.

        Returns
        -------
        np.ndarray
            ``(feature_dim,)`` if a single name was passed, otherwise
            ``(n, feature_dim)`` in the requested order.
        """
        self._require_model(model)
        if isinstance(image_name, str):
            idx = self._index_of(image_name)
            return self[model][idx]
        names = list(image_name)
        indices = np.array([self._index_of(n) for n in names])
        # h5py doesn't accept arbitrary integer arrays; need sorted unique.
        order = np.argsort(indices)
        sorted_idx = indices[order]
        sorted_rows = self[model][sorted_idx, :]
        # Undo the sort to preserve caller order.
        inverse = np.empty_like(order)
        inverse[order] = np.arange(len(order))
        return sorted_rows[inverse]

    # ── internals ─────────────────────────────────────────────

    def _handle(self, model: str) -> h5py.File:
        h = self._h5s.get(model)
        if h is None:
            h = h5py.File(embeddings_h5_path(self.data_dir, model), "r")
            self._h5s[model] = h
        return h

    def _require_model(self, model: str) -> None:
        if model not in self._models:
            raise KeyError(
                f"Model {model!r} not loaded by this handle. "
                f"Loaded: {self._models}."
            )

    def _index_of(self, name: str) -> int:
        _ = self.image_ids
        idx = (self._name_to_idx or {}).get(name)
        if idx is None:
            raise KeyError(f"Unknown image name: {name!r}")
        return idx

    def _metadata(self) -> pd.DataFrame:
        if self._meta is None:
            csv_path = stimuli_metadata_path(self.data_dir)
            if not csv_path.exists():
                raise FileNotFoundError(
                    f"Stimulus metadata not found at {csv_path}. "
                    "Run `laion-fmri download-stimuli` first."
                )
            self._meta = pd.read_csv(csv_path)
        return self._meta


def load_embeddings(models="all", data_dir=None) -> Embeddings:
    """Return a lazy embedding reader for one or more models.

    Parameters
    ----------
    models : "all", str, or iterable[str]
        ``"all"`` loads every available embedding model. A single
        model label such as ``"CLIP"`` or an iterable of labels
        narrows the reader.
    data_dir : str or Path, optional
        Override the configured data directory.
    """
    selected = AVAILABLE_MODELS if models == "all" else models
    return Embeddings(selected, data_dir=data_dir)
