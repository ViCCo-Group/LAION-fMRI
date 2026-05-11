"""Subject class for accessing per-subject data files.

Every accessor maps to exactly one file in the bucket layout:
no averaging, concatenation, or rebinning across sessions.
"""

import warnings

import numpy as np

from laion_fmri._constants import resolve_subject_id
from laion_fmri._errors import (
    DataNotDownloadedError,
    StimuliNotDownloadedError,
)
from laion_fmri._paths import (
    betas_path,
    glmsingle_subject_dir,
    parse_roi_label,
    r2mean_path,
    roi_freesurfer_label_path,
    roi_mask_path,
    roi_surface_path,
    rois_subject_dir,
    session_noise_ceiling_path,
    stimuli_dir_path,
    stimuli_metadata_path,
    subject_noise_ceiling_path,
    trialinfo_path,
)
from laion_fmri.config import get_data_dir
from laion_fmri.io import (
    load_freesurfer_label,
    load_gifti_mask,
    load_nifti_4d,
    load_nifti_data,
    load_nifti_mask,
    load_nifti_with_affine,
    load_tsv,
)


_VALID_FORMATS = {
    "all", "volume", "nii.gz", "gii", "func.gii", "label",
}
_VALID_HEMIS = {"all", "L", "R"}


def load_subject(subject):
    """Load a subject by BIDS ID or integer index.

    Parameters
    ----------
    subject : int or str

    Returns
    -------
    Subject

    Raises
    ------
    SubjectNotFoundError
        If the subject identifier is invalid.
    DataNotDownloadedError
        If the subject's data has not been downloaded.
    """
    subject_id = resolve_subject_id(subject)
    data_dir = get_data_dir()

    glm_dir = glmsingle_subject_dir(data_dir, subject_id)
    if not glm_dir.is_dir():
        raise DataNotDownloadedError(
            f"Data for {subject_id} not found at {glm_dir}. "
            "Run: from laion_fmri.download import download; "
            f"download(subject='{subject_id}')"
        )

    return Subject(subject_id, data_dir)


class Subject:
    """Access loaded data files for a single subject.

    Parameters
    ----------
    subject_id : str
        BIDS subject ID.
    data_dir : str
        Path to the local data directory.
    """

    def __init__(self, subject_id, data_dir):
        self._subject_id = subject_id
        self._data_dir = data_dir

    @property
    def subject_id(self):
        """Return the BIDS subject ID (e.g. ``"sub-03"``)."""
        return self._subject_id

    # ── Discovery ───────────────────────────────────────────────

    def get_sessions(self):
        """Return sorted list of available session IDs."""
        glm_dir = glmsingle_subject_dir(
            self._data_dir, self._subject_id,
        )
        sessions = []
        for d in sorted(glm_dir.iterdir()):
            if d.is_dir() and d.name.startswith("ses-"):
                sessions.append(d.name)
        return sessions

    def get_available_rois(self, category=None):
        """Return sorted list of ROI names available on disk.

        Parameters
        ----------
        category : str or None
            Restrict to ROIs in this category subdirectory.

        Returns
        -------
        list[str]
            Sorted ROI names (BIDS-clean form).
        """
        by_cat = self._rois_by_category()
        if category is not None:
            return sorted(by_cat.get(category, []))
        all_rois = set()
        for rois in by_cat.values():
            all_rois.update(rois)
        return sorted(all_rois)

    def get_available_categories(self):
        """Return sorted list of ROI category directory names."""
        return sorted(self._rois_by_category().keys())

    def _rois_by_category(self):
        """Walk local rois tree -> dict[category, list[roi]]."""
        root = rois_subject_dir(self._data_dir, self._subject_id)
        if not root.is_dir():
            return {}
        out = {}
        for cat_dir in sorted(root.iterdir()):
            if not cat_dir.is_dir():
                continue
            rois = [
                roi for f in sorted(cat_dir.iterdir())
                if (roi := parse_roi_label(
                    f.name, self._subject_id,
                )) is not None
            ]
            if rois:
                out[cat_dir.name] = rois
        return out

    def _resolve_rois_query(self, query):
        """Expand specific / category / "all" / list into flat ROI names.

        See ``get_roi_mask`` for the user-visible grammar.
        """
        if isinstance(query, str):
            query = [query]

        by_cat = self._rois_by_category()
        all_rois = sorted({r for rs in by_cat.values() for r in rs})
        all_categories = sorted(by_cat.keys())

        resolved = []
        for item in query:
            if item == "all":
                resolved.extend(all_rois)
            elif item in by_cat:
                resolved.extend(by_cat[item])
            elif item in all_rois:
                resolved.append(item)
            else:
                raise ValueError(
                    f"Unknown ROI/category: {item!r}. "
                    f"Available ROIs: {all_rois}. "
                    f"Available categories: {all_categories}."
                )

        seen = set()
        deduped = []
        for r in resolved:
            if r not in seen:
                seen.add(r)
                deduped.append(r)
        return deduped

    def get_n_stimuli(self, stimuli=None):
        """Return number of stimuli described in ``stimuli.tsv``.

        Parameters
        ----------
        stimuli : "shared", "unique", or None
        """
        meta = self.get_stimulus_metadata()
        if stimuli == "shared":
            return int(meta["shared"].sum())
        if stimuli == "unique":
            return int((~meta["shared"]).sum())
        return len(meta)

    def get_n_voxels(self):
        """Number of voxels in the subject's brain mask."""
        return int(self.get_brain_mask().sum())

    # ── Brain mask ──────────────────────────────────────────────

    def get_brain_mask(self):
        """Load the subject's brain mask as a flat boolean array.

        Derived from the subject-level mean-R^2 map: every voxel
        where the GLMsingle model has any non-zero fit. The
        bucket ships R2mean as ``..._stat-rsquare_desc-R2mean_
        statmap.nii.gz`` rather than a pre-computed mask file.

        Returns
        -------
        np.ndarray
            1-D boolean array over the full image grid.
        """
        return load_nifti_mask(
            r2mean_path(self._data_dir, self._subject_id),
        )

    # ── Betas (single-trial NIfTI per session) ─────────────────

    def get_betas(
        self,
        session,
        roi=None,
        mask=None,
        nc_threshold=None,
        stimuli=None,
        streaming=False,
    ):
        """Load single-trial betas for one or more sessions.

        Parameters
        ----------
        session : str, list of str
            BIDS session ID. A list returns a dict keyed by
            session ID, since trial counts may differ per session.
            Single-trial betas live per session in the bucket, so
            the caller must pick which sessions to load.
        roi : str, list[str], or None
            Named ROI(s) for voxel selection (union if list).
        mask : np.ndarray[bool] or None
            Custom boolean mask over brain-mask voxels.
        nc_threshold : float or None
            Minimum per-session noise ceiling to keep a voxel.
        stimuli : "shared", "unique", or None
            Trial-level filter using the stimulus-metadata
            ``shared`` flag.
        streaming : bool
            If False (default), the full 4-D NIfTI is
            materialized in RAM and then masked. Decompresses
            any ``.nii.gz`` once; peak memory is the full file
            (~12 GB for a real session) plus the masked output.
            Best when you have plenty of RAM. If True, the file
            is streamed volume-by-volume and the combined
            brain + ROI + NC mask is applied inline: peak
            memory is one volume (~10-50 MB) plus the masked
            output. Use this on memory-constrained machines
            like Colab. Works on both ``.nii`` (nibabel-managed
            per-volume reads) and ``.nii.gz`` (a custom gzip
            pipeline that never re-decompresses).

        Returns
        -------
        np.ndarray or dict[str, np.ndarray]
            ``(n_trials, n_selected_voxels)`` for a single
            session; a ``{session: array}`` dict for a list.
        """
        if isinstance(session, (list, tuple)):
            return {
                s: self.get_betas(
                    session=s, roi=roi, mask=mask,
                    nc_threshold=nc_threshold, stimuli=stimuli,
                    streaming=streaming,
                )
                for s in session
            }
        if not session:
            raise ValueError(
                "session is required: only single-trial betas are "
                "available, and they live per session in the bucket."
            )
        if roi is not None and mask is not None:
            raise ValueError(
                "roi and mask are mutually exclusive."
            )

        path = betas_path(
            self._data_dir, self._subject_id, session,
        )
        mask_path = r2mean_path(
            self._data_dir, self._subject_id,
        )

        # Build a single full-volume voxel mask before reading the
        # betas: the streaming path then applies brain + ROI + NC
        # inline, avoiding a brain-only intermediate (~1 GB on a
        # real session).
        brain_mask = load_nifti_mask(mask_path)
        voxel_filter = self._build_voxel_mask(
            roi, mask, nc_threshold, session,
        )
        if voxel_filter is None:
            combined_mask = brain_mask
        else:
            combined_mask = brain_mask.copy()
            combined_mask[brain_mask] = voxel_filter

        betas = load_nifti_4d(
            path, combined_mask, streaming=streaming,
        )

        if stimuli is not None:
            trial_mask = self._stimulus_trial_filter(stimuli, session)
            betas = betas[trial_mask]

        return betas

    def _build_voxel_mask(self, roi, mask, nc_threshold, session):
        """Combine ROI/custom-mask/NC-threshold into one boolean mask."""
        combined = None

        if roi is not None:
            combined = self.get_roi_mask(roi)

        if mask is not None:
            combined = mask

        if nc_threshold is not None:
            nc = self.get_noise_ceiling(session=session)
            nc_mask = nc >= nc_threshold
            combined = (
                nc_mask if combined is None else combined & nc_mask
            )

        return combined

    def _stimulus_trial_filter(self, stimuli, session):
        """Boolean trial mask for ``shared`` / ``unique`` subsets.

        Two events.tsv schemas are supported:

        * Real bucket: a ``label`` column whose values start with
          ``shared_`` or ``unique_``. The prefix is parsed
          directly -- no stimulus-metadata table required.
        * Synthetic / future schema: a ``stimulus_id`` column,
          joined against ``stimuli/stimuli.tsv``'s ``shared``
          flag.
        """
        if stimuli not in ("shared", "unique"):
            raise ValueError(
                f"stimuli must be 'shared' or 'unique', "
                f"got {stimuli!r}"
            )
        trials = self.get_trial_info(session=session)
        if "label" in trials.columns:
            flags = (
                trials["label"].str.startswith("shared_").to_numpy()
            )
        elif "stimulus_id" in trials.columns:
            meta = self.get_stimulus_metadata()
            is_shared = dict(zip(meta["stimulus_id"], meta["shared"]))
            flags = np.array([
                bool(is_shared[sid]) for sid in trials["stimulus_id"]
            ])
        else:
            raise ValueError(
                "Events TSV has neither 'label' nor "
                "'stimulus_id' -- cannot derive shared/unique."
            )
        return flags if stimuli == "shared" else ~flags

    # ── ROI masks ───────────────────────────────────────────────

    def get_roi_mask(self, query):
        """Load one or more ROI masks, restricted to brain-mask voxels.

        ``query`` accepts the multi-level grammar:

        * a specific ROI name (``"FFA1"``);
        * a category name (``"face"``) -- expands to every ROI
          in that category;
        * ``"all"`` -- expands to every ROI on disk;
        * a list mixing any of the above.

        Multi-element resolutions are unioned voxel-wise. Always
        returns one 1-D bool array within the brain mask.
        """
        rois = self._resolve_rois_query(query)
        union = np.zeros(self.get_n_voxels(), dtype=bool)
        for roi in rois:
            union |= self._load_roi_volume_mask(roi)
        return union

    def get_roi_masks(self, queries):
        """Load several ROI masks at once.

        ``queries`` is a list (or single string). Each element is
        passed verbatim to ``get_roi_mask``; the returned dict is
        keyed by the user's strings, so categories and "all" appear
        as their original keys with a union mask as value.
        """
        if isinstance(queries, str):
            queries = [queries]
        return {q: self.get_roi_mask(q) for q in queries}

    def get_roi_data(self, query, format=None, hemi=None):
        """Load multi-format ROI data: volume, surface, FreeSurfer label.

        Parameters
        ----------
        query : str or list[str]
            Multi-level ROI query (see ``get_roi_mask``).
        format : str or None
            One of ``"all"``, ``"volume"`` / ``"nii.gz"`` (synonyms),
            ``"gii"`` (per-hemi func.gii + label), ``"func.gii"``
            (per-hemi surface mask only), ``"label"`` (per-hemi
            FreeSurfer label only). ``None`` means ``"all"``.
        hemi : str or None
            One of ``"L"``, ``"R"``, or ``"all"`` (default).
            Ignored when ``format`` resolves to volume only.

        Returns
        -------
        dict
            Top-level dict keyed by ROI name. Each value is a
            nested dict shaped::

                {
                    "volume": <1-D bool ndarray>,
                    "gii": {
                        "hemi-L": {"func.gii": ..., "label": ...},
                        "hemi-R": {...},
                    },
                }

            Format/hemi filters prune this tree.
        """
        format = format or "all"
        hemi = hemi or "all"
        if format not in _VALID_FORMATS:
            raise ValueError(
                f"format must be one of {sorted(_VALID_FORMATS)}, "
                f"got {format!r}"
            )
        if hemi not in _VALID_HEMIS:
            raise ValueError(
                f"hemi must be one of {sorted(_VALID_HEMIS)}, "
                f"got {hemi!r}"
            )

        rois = self._resolve_rois_query(query)
        return {roi: self._build_roi_data(roi, format, hemi)
                for roi in rois}

    def _load_roi_volume_mask(self, roi):
        """Load a single volumetric ROI mask within the brain mask."""
        roi_vol = load_nifti_mask(
            roi_mask_path(self._data_dir, self._subject_id, roi),
        )
        brain = self.get_brain_mask()
        return roi_vol[brain]

    def _build_roi_data(self, roi, format, hemi):
        """Assemble the nested per-ROI dict, pruned by format/hemi."""
        out = {}
        want_volume = format in ("all", "volume", "nii.gz")
        want_gii = format in ("all", "gii", "func.gii", "label")

        if want_volume:
            out["volume"] = self._load_roi_volume_mask(roi)

        if want_gii:
            hemis = ("L", "R") if hemi == "all" else (hemi,)
            gii = {}
            for h in hemis:
                hemi_data = {}
                if format in ("all", "gii", "func.gii"):
                    hemi_data["func.gii"] = load_gifti_mask(
                        roi_surface_path(
                            self._data_dir, self._subject_id, roi, h,
                        ),
                    )
                if format in ("all", "gii", "label"):
                    hemi_data["label"] = load_freesurfer_label(
                        roi_freesurfer_label_path(
                            self._data_dir, self._subject_id, roi, h,
                        ),
                    )
                gii[f"hemi-{h}"] = hemi_data
            out["gii"] = gii

        return out

    # ── Noise ceiling ───────────────────────────────────────────

    def get_noise_ceiling(
        self, session=None, desc=None, roi=None, mask=None,
    ):
        """Load a noise-ceiling map.

        Exactly one of ``session`` or ``desc`` must be set:

        * ``session="ses-01"`` -> per-session NC NIfTI.
        * ``desc="noiseceiling33ses"`` -> the subject-level
          aggregate NC NIfTI with the given ``desc-...`` token.

        Either argument also accepts a list, in which case the
        return value is a dict keyed by session ID / desc token.

        Parameters
        ----------
        session : str, list of str, or None
        desc : str, list of str, or None
        roi : str or None
        mask : np.ndarray[bool] or None

        Returns
        -------
        np.ndarray or dict[str, np.ndarray]
        """
        if isinstance(session, (list, tuple)):
            return {
                s: self.get_noise_ceiling(
                    session=s, roi=roi, mask=mask,
                )
                for s in session
            }
        if isinstance(desc, (list, tuple)):
            return {
                d: self.get_noise_ceiling(
                    desc=d, roi=roi, mask=mask,
                )
                for d in desc
            }

        if (session is None) == (desc is None):
            raise ValueError(
                "Exactly one of `session` or `desc` must be set."
            )

        if session is not None:
            nc_file = session_noise_ceiling_path(
                self._data_dir, self._subject_id, session,
            )
        else:
            nc_file = subject_noise_ceiling_path(
                self._data_dir, self._subject_id, desc,
            )

        if not nc_file.exists():
            raise FileNotFoundError(
                f"Noise-ceiling file not found: {nc_file}"
            )

        mask_file = r2mean_path(
            self._data_dir, self._subject_id,
        )
        nc = load_nifti_data(nc_file, mask_file)

        if roi is not None:
            nc = nc[self.get_roi_mask(roi)]
        elif mask is not None:
            nc = nc[mask]

        return nc

    # ── Trial info (events.tsv per session) ────────────────────

    def get_trial_info(self, session):
        """Load the events TSV for one or more sessions.

        Parameters
        ----------
        session : str or list of str
            Required -- events live per session in the bucket. A
            list returns a dict keyed by session ID.

        Returns
        -------
        pd.DataFrame or dict[str, pd.DataFrame]
        """
        if isinstance(session, (list, tuple)):
            return {
                s: self.get_trial_info(session=s) for s in session
            }
        if not session:
            raise ValueError(
                "session is required: events are stored per session."
            )
        return load_tsv(
            trialinfo_path(
                self._data_dir, self._subject_id, session,
            ),
        )

    # ── Stimulus images ─────────────────────────────────────────

    def get_images(self, stimuli=None, format="pil"):
        """Load stimulus images (when ``stimuli/`` is populated)."""
        stim_dir = stimuli_dir_path(self._data_dir)
        if not stim_dir.is_dir():
            raise StimuliNotDownloadedError(
                "Stimulus images not found. Download with "
                "include_stimuli=True once the bucket has them."
            )

        from PIL import Image

        meta = self.get_stimulus_metadata()
        if stimuli is not None:
            if stimuli == "shared":
                meta = meta[meta["shared"]]
            elif stimuli == "unique":
                meta = meta[~meta["shared"]]
            else:
                raise ValueError(
                    f"stimuli must be 'shared' or 'unique', "
                    f"got {stimuli!r}"
                )

        images = [
            Image.open(stim_dir / row["filename"])
            for _, row in meta.iterrows()
        ]

        if format == "pil":
            return images
        if format == "numpy":
            return np.stack(
                [np.array(img) for img in images],
            ).astype(np.uint8)
        if format == "torch":
            warnings.warn(
                "torch format yields a CHW float32 array. Use "
                "to_torch_dataset() for full torchvision support.",
                stacklevel=2,
            )
            arr = np.stack(
                [np.array(img) for img in images],
            ).astype(np.float32) / 255.0
            return arr.transpose(0, 3, 1, 2)
        raise ValueError(f"Unknown format: {format!r}")

    def get_image(self, idx):
        """Load a single stimulus image by index."""
        return self.get_images()[idx]

    # ── Stimulus metadata ───────────────────────────────────────

    def get_stimulus_metadata(self):
        """Load the dataset-wide stimulus metadata TSV."""
        path = stimuli_metadata_path(self._data_dir)
        if not path.exists():
            raise StimuliNotDownloadedError(
                f"Stimulus metadata not found at {path}. Download "
                "with include_stimuli=True once the bucket has "
                "stimuli (or check has_stimuli() first)."
            )
        return load_tsv(path)

    def has_stimuli(self):
        """Return True if stimulus metadata + images are on disk.

        Useful as a guard before calling stimulus-dependent
        methods (``get_n_stimuli``, ``get_stimulus_metadata``,
        ``get_images``, ``get_trial_stimulus_indices``,
        ``to_torch_dataset``) when the bucket's ``stimuli/``
        prefix is not yet populated.
        """
        return (
            stimuli_metadata_path(self._data_dir).exists()
            and stimuli_dir_path(self._data_dir).is_dir()
        )

    # ── Trial-to-stimulus mapping ───────────────────────────────

    def get_trial_stimulus_indices(self, session):
        """Map each trial to its stimulus-metadata row index.

        Parameters
        ----------
        session : str or list of str
            A list returns a dict keyed by session ID.

        Returns
        -------
        np.ndarray or dict[str, np.ndarray]
        """
        if isinstance(session, (list, tuple)):
            return {
                s: self.get_trial_stimulus_indices(session=s)
                for s in session
            }
        trials = self.get_trial_info(session=session)
        meta = self.get_stimulus_metadata()
        idx_map = {
            sid: i for i, sid in enumerate(meta["stimulus_id"])
        }
        # Dual schema: real bucket trial TSVs use ``label``,
        # synthetic / future trials may use ``stimulus_id``.
        if "label" in trials.columns:
            ids = trials["label"]
        elif "stimulus_id" in trials.columns:
            ids = trials["stimulus_id"]
        else:
            raise ValueError(
                "Trial info has neither 'label' nor 'stimulus_id' "
                "column; cannot map trials to stimuli."
            )
        return np.array([idx_map[sid] for sid in ids])

    # ── Brain space ─────────────────────────────────────────────

    def to_nifti(self, values, output_path, roi=None, mask=None):
        """Write a per-voxel array to a 3-D NIfTI volume."""
        from laion_fmri.brain import to_nifti

        mask_file = r2mean_path(
            self._data_dir, self._subject_id,
        )
        _, affine = load_nifti_with_affine(mask_file)

        roi_mask_arr = (
            self.get_roi_mask(roi) if roi is not None else None
        )

        to_nifti(
            values,
            output_path,
            str(mask_file),
            affine,
            roi_mask=roi_mask_arr,
            custom_mask=mask,
        )

    def get_voxel_coordinates(self, roi=None, mask=None):
        """Return MNI/T1w coordinates for the selected voxels."""
        from laion_fmri.brain import get_voxel_coordinates

        mask_file = r2mean_path(
            self._data_dir, self._subject_id,
        )
        _, affine = load_nifti_with_affine(mask_file)

        roi_mask_arr = (
            self.get_roi_mask(roi) if roi is not None else None
        )
        return get_voxel_coordinates(
            str(mask_file),
            affine,
            roi_mask=roi_mask_arr,
            custom_mask=mask,
        )

    # ── PyTorch ─────────────────────────────────────────────────

    def to_torch_dataset(self, **kwargs):
        """Wrap this subject as a ``torch.utils.data.Dataset``."""
        from laion_fmri.torch_data import LaionFMRIDataset
        return LaionFMRIDataset(self, **kwargs)
