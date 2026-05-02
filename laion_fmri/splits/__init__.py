"""Predefined train / test splits for the re:vision generalization framework.

LAION-fMRI ships with **11 train/test splits per pool**, designed to test
generalization across the per-subject ``shared + unique`` stimulus pool
or, alternatively, across just the cross-subject shared pool.

Pools
-----

* ``"shared"`` — the 1,121 LAION images shared across every subject
  (non-OOD subset of the shared block). Use this when the original study
  you're replicating relied on cross-subject shared images only (e.g.
  Conwell et al., 2024).
* ``"sub-01"``, ``"sub-03"``, ``"sub-05"``, ``"sub-06"``, ``"sub-07"`` —
  the 5,833-image per-subject pools (1,121 shared + 4,712 unique). Use
  these when each subject's full pool is the unit of analysis.

Splits
------

The same 11 split names exist in every pool:

* ``random_0`` … ``random_4`` — five seeded uniform-random partitions.
  The natural baseline for any generalization metric.
* ``cluster_k5_0`` … ``cluster_k5_4`` — five hold-out-cluster partitions
  (CLIP-feature k-means; one cluster held out as test). re:vision
  *Method 2* (out-of-distribution clusters): average across all 5 folds.
* ``tau`` — the MMD-matched 80/20 nearest-neighbour-distance split.
  re:vision *Method 1* (independent within-distribution).

Sizes:

* ``random_*`` and ``tau`` are fixed at 80/20 of the pool (897/224
  for the shared pool; 4666/1167 for per-subject pools).
* ``cluster_k5_*`` test sizes vary with cluster population; train+test
  always sum to the pool.

Loading
-------

The natural entry point is the :class:`~laion_fmri.subject.Subject` you
already use for betas:

>>> import laion_fmri
>>> sub = laion_fmri.load_subject("sub-01")
>>> train_ids, test_ids = sub.get_train_test_ids("tau")          # own pool
>>> train_ids, test_ids = sub.get_train_test_ids("tau",
...                                              pool="shared")  # shared pool

Or via the module-level functions:

>>> from laion_fmri.splits import list_splits, load_split, get_train_test_ids
>>> list_splits()
['cluster_k5_0', ..., 'tau']
>>> sp = load_split("tau", pool="shared")
>>> sp.pool, sp.n_train, sp.n_test
('shared', 897, 224)

The returned image_ids match the ``label`` column of every session's
events TSV. Slice betas with the existing ``get_betas`` filter system —
see :doc:`/laion_fmri_package/load` for details.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# Per-subject pools follow the BIDS subject IDs already used elsewhere in
# the package (sub-01, sub-03, sub-05, sub-06, sub-07). The "shared" pool
# is cross-subject. No internal participant-code abstraction is exposed.
_SUBJECT_POOLS: Tuple[str, ...] = (
    "sub-01", "sub-03", "sub-05", "sub-06", "sub-07",
)
_SHARED_POOL = "shared"

# All split names available in every pool. 11 names × 6 pools = 66 JSONs.
_SPLIT_NAMES: Tuple[str, ...] = (
    "random_0", "random_1", "random_2", "random_3", "random_4",
    "cluster_k5_0", "cluster_k5_1", "cluster_k5_2", "cluster_k5_3", "cluster_k5_4",
    "tau",
)


@dataclass
class SplitVariant:
    """A single train/test image-id partition within a Split."""
    variant_id: int
    train_ids: List[str]
    test_ids: List[str]

    def all_ids(self) -> List[str]:
        return list(self.train_ids) + list(self.test_ids)


@dataclass
class Split:
    """One named split (e.g. ``"tau"``) for one pool (e.g. ``"sub-01"``)."""
    name: str
    pool: str
    splitter: str
    params: Dict
    n_train: int
    n_test: int
    variants: List[SplitVariant] = field(default_factory=list)

    @property
    def split_family(self) -> str:
        """Coarse family: ``"random"``, ``"cluster_k5"``, or ``"tau"``."""
        if self.name.startswith("random_"):
            return "random"
        if self.name.startswith("cluster_k5_"):
            return "cluster_k5"
        if self.name == "tau":
            return "tau"
        return "other"


# ── Locator ────────────────────────────────────────────────────


def _data_dir() -> Path:
    """Path to the bundled split JSONs (under the installed package)."""
    return Path(__file__).resolve().parent / "data"


def _validate_pool(pool: str) -> str:
    if pool == _SHARED_POOL or pool in _SUBJECT_POOLS:
        return pool
    raise ValueError(
        f"Unknown pool {pool!r}. Valid: "
        f"{[_SHARED_POOL] + list(_SUBJECT_POOLS)}."
    )


def _validate_split_name(name: str) -> str:
    if name not in _SPLIT_NAMES:
        raise ValueError(
            f"Unknown split {name!r}. Valid: {list(_SPLIT_NAMES)}."
        )
    return name


# ── Public API ─────────────────────────────────────────────────


def list_pools() -> List[str]:
    """Return every pool that has bundled splits."""
    return [_SHARED_POOL] + list(_SUBJECT_POOLS)


def list_splits() -> List[str]:
    """Return the 11 split names available in every pool."""
    return list(_SPLIT_NAMES)


def load_split(name: str, pool: str) -> Split:
    """Load one bundled split.

    Parameters
    ----------
    name : str
        One of the 11 split names (see :func:`list_splits`).
    pool : str
        ``"shared"`` or a subject id like ``"sub-01"`` (see
        :func:`list_pools`).

    Returns
    -------
    Split
    """
    _validate_split_name(name)
    _validate_pool(pool)
    path = _data_dir() / pool / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"Split {name!r} for pool {pool!r} not found at {path}. "
            f"Available pools: {list_pools()}."
        )
    raw = json.loads(path.read_text())
    variants = [
        SplitVariant(
            variant_id=int(v["variant_id"]),
            train_ids=list(v["train_ids"]),
            test_ids=list(v["test_ids"]),
        )
        for v in raw["variants"]
    ]
    return Split(
        name=raw["name"],
        pool=pool,
        splitter=raw.get("splitter", ""),
        params=raw.get("params", {}),
        n_train=int(raw["n_train"]),
        n_test=int(raw["n_test"]),
        variants=variants,
    )


def load_all_splits(pool: str) -> Dict[str, Split]:
    """Load every split for ``pool`` → ``{name: Split}``."""
    return {name: load_split(name, pool) for name in _SPLIT_NAMES}


def get_train_test_ids(
    name: str,
    pool: str,
    variant_id: int = 0,
) -> Tuple[List[str], List[str]]:
    """Convenience: return ``(train_ids, test_ids)`` for one variant.

    Most splits have a single ``variant_id=0``. The five ``random_*``
    and the five ``cluster_k5_*`` splits each ARE the variants — pick
    the split name; ``variant_id`` stays 0.
    """
    sp = load_split(name, pool)
    for v in sp.variants:
        if v.variant_id == variant_id:
            return list(v.train_ids), list(v.test_ids)
    raise ValueError(
        f"variant_id={variant_id} not in split {name!r} (pool {pool}). "
        f"Available variants: {[v.variant_id for v in sp.variants]}"
    )


def get_split_masks(
    trials,
    name: str,
    pool: str,
    variant_id: int = 0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Build ``(train_mask, test_mask)`` over rows of a trial table.

    The masks are derived by matching ``trials["label"]`` against the
    train/test image-id lists of the requested split. They line up
    one-to-one with the trials passed in, so you can apply them to
    *any* trial-aligned array (betas, features, decoded labels, …).

    Parameters
    ----------
    trials : pandas.DataFrame, pandas.Series, np.ndarray or list
        Trial-level labels. If a ``DataFrame``, the ``"label"`` column
        is used; otherwise the input is treated as label values
        directly.
    name : str
        One of the 11 split names (see :func:`list_splits`).
    pool : str
        ``"shared"`` or a subject id like ``"sub-01"`` (see
        :func:`list_pools`).
    variant_id : int, default 0
        Variant within the split. Almost always 0.

    Returns
    -------
    (train_mask, test_mask) : tuple of np.ndarray
        Boolean arrays, both of length ``len(trials)``.

    Examples
    --------
    >>> sub = laion_fmri.load_subject("sub-01")
    >>> trials = pd.concat(
    ...     sub.get_trial_info(session=sub.get_sessions()).values(),
    ...     ignore_index=True,
    ... )
    >>> train_mask, test_mask = get_split_masks(
    ...     trials, "tau", pool="shared",
    ... )
    >>> betas[train_mask], betas[test_mask]   # doctest: +SKIP
    """
    train_ids, test_ids = get_train_test_ids(name, pool, variant_id=variant_id)
    train_set = set(train_ids)
    test_set = set(test_ids)

    if hasattr(trials, "columns") and "label" in getattr(trials, "columns", ()):
        labels = trials["label"].to_numpy()
    elif hasattr(trials, "to_numpy"):
        labels = trials.to_numpy()
    else:
        labels = np.asarray(trials)

    train_mask = np.array([lab in train_set for lab in labels], dtype=bool)
    test_mask = np.array([lab in test_set for lab in labels], dtype=bool)
    return train_mask, test_mask


__all__ = [
    "Split",
    "SplitVariant",
    "list_pools",
    "list_splits",
    "load_split",
    "load_all_splits",
    "get_train_test_ids",
    "get_split_masks",
]
