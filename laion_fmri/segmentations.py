"""Access per-stimulus object-segmentation masks for the LAION-fMRI stimuli.

The segmentations describe *what objects appear in each stimulus* and
*where*: every stimulus has zero or more nouns associated with it, and
every noun has one or more spatial masks (one per detected instance of
that noun in the image). For example, an image of a person playing
piano might carry masks for ``"hand"`` (4 instances), ``"piano"`` (1
instance), and ``"sheet music"`` (1 instance).

Files on disk:

.. code-block:: text

   stimuli/
     task-images_desc-segmentations.h5            (N, H, W) uint8, gzip+shuffle
     task-images_desc-segmentations_metadata.csv  one row per mask

The HDF5 holds a single ``masks`` dataset of shape ``(N, 1000, 1000)``
binary uint8. The CSV columns are ``mask_row``, ``image_name``,
``noun``, ``instance_id``, ``score``, ``box_x0``, ``box_y0``,
``box_x1``, ``box_y1``, ``localized``, ``mask_file``. ``localized`` is
``1`` when the detector returned a bounding box and the mask covers
less than 99% of the image; otherwise ``0`` (use this to filter out
"concept present but not localised" entries).

Quick start
-----------

>>> import laion_fmri
>>> stim = laion_fmri.load_stimuli()
>>> stim.segmentations.nouns("shared_12rep_LAION_cluster_1003_i0.jpg")
['fingers', 'hand', 'pullover', ...]
>>> mask = stim.segmentations.get(
...     "shared_12rep_LAION_cluster_1003_i0.jpg", "fingers", instance=0
... )
>>> mask.shape, mask.dtype
((1000, 1000), dtype('uint8'))
"""

from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from laion_fmri._paths import (
    segmentations_h5_path,
    segmentations_metadata_path,
)
from laion_fmri.config import get_data_dir


class Segmentations:
    """Lazy reader for the per-stimulus segmentation masks.

    Opens the HDF5 file once on first access and keeps the handle open
    for the lifetime of the instance. Use as a context manager to
    release the handle explicitly::

        with Segmentations() as seg:
            arr = seg.get("img.jpg", "hand")

    Parameters
    ----------
    data_dir : str or Path, optional
        Override the configured data directory. Defaults to
        :func:`laion_fmri.config.get_data_dir`.
    """

    def __init__(self, data_dir=None):
        self.data_dir = (
            Path(data_dir) if data_dir is not None else Path(get_data_dir())
        )
        self._h5_path = segmentations_h5_path(self.data_dir)
        self._csv_path = segmentations_metadata_path(self.data_dir)
        if not self._h5_path.exists() or not self._csv_path.exists():
            raise FileNotFoundError(
                f"Segmentations not found under {self.data_dir / 'stimuli'}. "
                "Run `laion-fmri download-segmentations` first."
            )
        self._h5: h5py.File | None = None
        self._meta: pd.DataFrame | None = None
        self._by_image: dict[str, pd.DataFrame] | None = None

    # ── lifecycle ──────────────────────────────────────────────

    def __enter__(self) -> "Segmentations":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        """Release the HDF5 handle."""
        if self._h5 is not None:
            self._h5.close()
            self._h5 = None

    # ── shape / inventory ─────────────────────────────────────

    @property
    def metadata(self) -> pd.DataFrame:
        """One row per mask.

        Columns: ``mask_row``, ``image_name``, ``noun``,
        ``instance_id``, ``score``, ``box_x0``, ``box_y0``,
        ``box_x1``, ``box_y1``, ``localized``, ``mask_file``.
        """
        if self._meta is None:
            self._meta = pd.read_csv(self._csv_path)
            self._by_image = {
                name: g.reset_index(drop=True)
                for name, g in self._meta.groupby("image_name")
            }
        return self._meta

    def __len__(self) -> int:
        return len(self.metadata)

    # ── data access ───────────────────────────────────────────

    def __getitem__(self, mask_row: int) -> np.ndarray:
        """Return one mask by its raw row index in the HDF5 dataset."""
        return self._dataset()[int(mask_row), :, :]

    def get(
        self,
        image_name: str,
        noun: str,
        instance: int = 0,
    ) -> np.ndarray:
        """Return the mask for ``(image, noun, instance)``.

        Parameters
        ----------
        image_name : str
            Stimulus filename (e.g. ``"shared_..._1003_i0.jpg"``).
        noun : str
            One of the nouns associated with ``image_name`` (see
            :meth:`nouns`).
        instance : int, default 0
            Which detected instance of ``noun``. ``0`` is the highest-
            scored detection.

        Returns
        -------
        np.ndarray
            ``(H, W)`` uint8 binary mask.

        Raises
        ------
        KeyError
            If the image has no segmentations (e.g. it's a
            subject-unique image; only shared stimuli are covered) or
            the requested ``(noun, instance)`` doesn't exist.
        """
        rows = self._rows_for(image_name)
        if rows.empty:
            raise KeyError(
                f"No segmentations available for image {image_name!r}. "
                "Masks are provided for the shared stimulus set only "
                "(see Segmentations.images() for the covered set)."
            )
        match = rows[(rows["noun"] == noun) & (rows["instance_id"] == instance)]
        if match.empty:
            available = rows["noun"].unique().tolist()
            raise KeyError(
                f"No mask for noun={noun!r} instance={instance} in "
                f"image {image_name!r}. Available nouns: {available}."
            )
        return self[int(match.iloc[0]["mask_row"])]

    def for_image(self, image_name: str) -> pd.DataFrame:
        """Metadata slice (all masks) for one image.

        Returns an **empty DataFrame** (not an error) when the image
        has no segmentations -- which is the case for all
        subject-unique stimuli, since masks ship only for the shared
        set.
        """
        return self._rows_for(image_name).copy()

    def nouns(self, image_name: str, localized_only: bool = True) -> list[str]:
        """Nouns detected in ``image_name``.

        Returns an **empty list** (not an error) when the image has no
        segmentations -- the case for all subject-unique stimuli,
        since masks ship only for the shared set.

        Parameters
        ----------
        image_name : str
        localized_only : bool, default True
            If ``True``, drop nouns whose only detections weren't
            localised (no bounding box / full-image mask). Set
            ``False`` to include them.
        """
        rows = self._rows_for(image_name)
        if rows.empty:
            return []
        if localized_only:
            rows = rows[rows["localized"] == 1]
        # Stable de-duplication preserving first appearance order.
        seen: set[str] = set()
        out: list[str] = []
        for n in rows["noun"]:
            if n not in seen:
                seen.add(n)
                out.append(n)
        return out

    def has_image(self, image_name: str) -> bool:
        """True if ``image_name`` has at least one segmentation mask.

        Masks ship only for the shared stimulus set, so this returns
        ``False`` for any subject-unique image.
        """
        _ = self.metadata
        return image_name in (self._by_image or {})

    def images(self) -> list[str]:
        """All image names that have at least one mask, in metadata order."""
        _ = self.metadata
        return list(self._by_image or {})

    # ── internals ─────────────────────────────────────────────

    def _dataset(self) -> h5py.Dataset:
        if self._h5 is None:
            self._h5 = h5py.File(self._h5_path, "r")
        return self._h5["masks"]

    _EMPTY: pd.DataFrame | None = None

    def _rows_for(self, image_name: str) -> pd.DataFrame:
        """Rows for ``image_name``, or an empty DataFrame if none.

        Non-raising on purpose -- callers decide whether emptiness is
        an error (``get``) or just absence (``nouns``, ``for_image``).
        """
        _ = self.metadata
        rows = (self._by_image or {}).get(image_name)
        if rows is None:
            if Segmentations._EMPTY is None and self._meta is not None:
                Segmentations._EMPTY = self._meta.iloc[0:0].copy()
            return Segmentations._EMPTY if Segmentations._EMPTY is not None else pd.DataFrame()
        return rows
