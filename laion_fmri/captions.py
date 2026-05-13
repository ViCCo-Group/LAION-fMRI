"""Access per-stimulus captions for the LAION-fMRI images.

Each stimulus carries a small set of short *human* captions (collected on
CloudResearch Connect). Shared non-OOD stimuli additionally carry one
*AI* caption (a GPT-generated description). The target is:

* **shared** images (seen by every participant) get **5 human captions**
  and, for non-OOD images, **1 AI caption**
* **unique** images (one participant only) get **3 human captions** and
  no AI caption
* **OOD** images get their target human captions and no AI caption

Together they give you a small set of independent natural-language
descriptions per image, useful for caption-conditioned modelling,
retrieval, or quick qualitative checks.

Files on disk:

.. code-block:: text

   stimuli/
     task-images_desc-captions.csv

The CSV is long-form (one row per caption) with columns:

=======================  =====================================================
``image_name``           Stimulus filename. Join key against
                         ``task-images_metadata.csv``.
``caption_idx``          Position within the image. Rank ``1`` is the
                         highest-quality human caption; ranks go up to ``3``
                         for unique images and up to ``5`` for shared images.
                         The AI caption (if any) gets ``0``.
``source``               ``"human"`` or ``"ai"``.
``caption``              The caption text.
``origin_collection``    Which collection the caption came from
                         (CloudResearch Connect batch labels for humans,
                         model name like ``"gpt-5.1"`` for AI).
``participant_id``       CloudResearch Connect participant identifier
                         (NaN for AI).
``ai_model``             Model name (NaN for human captions).
=======================  =====================================================

All images have their target human-caption count. AI captions are
provided for shared non-OOD images only.

You normally reach :class:`Captions` through the :class:`~laion_fmri.Stimuli`
hub:

>>> import laion_fmri
>>> stim = laion_fmri.load_stimuli()
>>> stim.captions.human("shared_12rep_LAION_cluster_1003_i0.jpg")
['a hand with light pink painted nails with flower designs',
 'A hand with finger painted nails with flowers in them',
 ...]
>>> stim.captions.ai("shared_12rep_LAION_cluster_1003_i0.jpg")
'A hand with short, pale pink polished nails features delicate floral nail art on two fingers.'

For a single row-level DataFrame of every caption attached to an image:

>>> stim.captions.get("shared_12rep_LAION_cluster_1003_i0.jpg")
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from laion_fmri._paths import captions_path
from laion_fmri.config import get_data_dir


class Captions:
    """Lazy reader for the per-stimulus captions CSV.

    Loads the CSV on first access and caches a per-image lookup.

    Parameters
    ----------
    data_dir : str or Path, optional
        Override the configured data directory. Defaults to
        :func:`laion_fmri.config.get_data_dir`.

    Raises
    ------
    FileNotFoundError
        If ``stimuli/task-images_desc-captions.csv`` is not present.
        Captions are a public stimulus-side metadata file; run
        ``laion-fmri download-captions`` (or
        :func:`laion_fmri.download.download_captions`) to fetch them.
    """

    def __init__(self, data_dir=None):
        self.data_dir = (
            Path(data_dir) if data_dir is not None else Path(get_data_dir())
        )
        self._csv_path = captions_path(self.data_dir)
        if not self._csv_path.exists():
            raise FileNotFoundError(
                f"Captions not found at {self._csv_path}. "
                "Run `laion-fmri download-captions` first."
            )
        self._meta: pd.DataFrame | None = None
        self._by_image: dict[str, pd.DataFrame] | None = None

    # ── shape / inventory ─────────────────────────────────────

    @property
    def metadata(self) -> pd.DataFrame:
        """The captions CSV as a DataFrame (one row per caption).

        Columns: ``image_name``, ``caption_idx``, ``source``,
        ``caption``, ``origin_collection``, ``participant_id``,
        ``ai_model``.
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

    def images(self) -> list[str]:
        """Image names that have at least one caption."""
        _ = self.metadata
        return list((self._by_image or {}).keys())

    def __contains__(self, image_name: str) -> bool:
        _ = self.metadata
        return image_name in (self._by_image or {})

    # ── per-image access ──────────────────────────────────────

    def get(self, image_name: str) -> pd.DataFrame:
        """Return all captions for one image as a DataFrame.

        Returns an **empty DataFrame** (not an error) when the image has
        no captions. Rows are ordered by ``caption_idx``: AI first
        (``idx=0``), then humans in rank order.
        """
        rows = self._rows_for(image_name)
        return rows.sort_values("caption_idx").reset_index(drop=True)

    def human(
        self,
        image_name: str,
        limit: int | None = None,
    ) -> list[str]:
        """Human captions for ``image_name`` in rank order.

        Parameters
        ----------
        image_name : str
        limit : int, optional
            Cap to the top-``limit`` captions. ``None`` (default) returns
            all available (currently up to five).

        Returns an **empty list** if the image has no human captions.
        """
        rows = self._rows_for(image_name)
        if rows.empty:
            return []
        humans = rows[rows["source"] == "human"].sort_values("caption_idx")
        if limit is not None:
            humans = humans.head(limit)
        return humans["caption"].tolist()

    def list(
        self,
        image_name: str,
        source: str | None = None,
    ) -> list[str]:
        """Captions for ``image_name`` as a list of strings.

        Parameters
        ----------
        image_name : str
        source : {"human", "ai"}, optional
            Restrict to one source. ``None`` (default) returns all
            available captions in ``caption_idx`` order.
        """
        rows = self.get(image_name)
        if source is not None:
            if source not in {"human", "ai"}:
                raise ValueError("source must be 'human', 'ai', or None")
            rows = rows[rows["source"] == source]
        return rows["caption"].tolist()

    def ai(self, image_name: str) -> str | None:
        """AI caption for ``image_name``, or ``None`` if not available.

        AI captions are present for shared non-OOD images only.
        """
        rows = self._rows_for(image_name)
        if rows.empty:
            return None
        ai_rows = rows[rows["source"] == "ai"]
        if ai_rows.empty:
            return None
        return str(ai_rows.iloc[0]["caption"])

    # ── internals ─────────────────────────────────────────────

    def _rows_for(self, image_name: str) -> pd.DataFrame:
        _ = self.metadata
        return (self._by_image or {}).get(image_name, self.metadata.iloc[0:0])
