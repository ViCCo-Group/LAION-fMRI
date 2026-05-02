"""Tests for the bundled train/test splits subpackage.

These tests don't need any downloaded data — the splits ship as package
data under ``laion_fmri/splits/data/``.
"""

import numpy as np
import pandas as pd
import pytest

from laion_fmri.splits import (
    Split,
    SplitVariant,
    get_split_masks,
    get_train_test_ids,
    list_ood_types,
    list_pools,
    list_splits,
    load_all_splits,
    load_split,
)


_POOL_SIZE_PER_SUBJECT = 5833      # 1121 shared + 4712 unique
_POOL_SIZE_SHARED = 1121           # cross-subject shared (non-OOD)
_N_OOD = 371                        # OOD-shared images (re:vision Method 3)


# ── Catalogue ──────────────────────────────────────────────────


def test_list_pools_includes_shared_and_five_subjects():
    pools = list_pools()
    assert pools[0] == "shared"
    assert set(pools[1:]) == {"sub-01", "sub-03", "sub-05", "sub-06", "sub-07"}


def test_list_splits_returns_twelve_names():
    names = list_splits()
    assert len(names) == 12
    assert sum(n.startswith("random_") for n in names) == 5
    assert sum(n.startswith("cluster_k5_") for n in names) == 5
    assert "tau" in names
    assert "ood" in names


# ── Loading single splits ──────────────────────────────────────


@pytest.mark.parametrize("pool", list_pools())
def test_every_split_loads_for_every_pool(pool):
    for name in list_splits():
        sp = load_split(name, pool=pool)
        assert sp.name == name
        assert sp.pool == pool


@pytest.mark.parametrize("name", ["random_0", "tau"])
def test_random_and_tau_are_fixed_size(name):
    sp = load_split(name, pool="sub-01")
    assert sp.n_train == 4666
    assert sp.n_test == 1167
    assert sp.n_train + sp.n_test == _POOL_SIZE_PER_SUBJECT
    sp_shared = load_split(name, pool="shared")
    assert sp_shared.n_train + sp_shared.n_test == _POOL_SIZE_SHARED


@pytest.mark.parametrize("k", range(5))
def test_cluster_k5_sums_to_pool_size(k):
    sp = load_split(f"cluster_k5_{k}", pool="sub-01")
    assert sp.n_train + sp.n_test == _POOL_SIZE_PER_SUBJECT
    sp_shared = load_split(f"cluster_k5_{k}", pool="shared")
    assert sp_shared.n_train + sp_shared.n_test == _POOL_SIZE_SHARED


def test_split_family():
    assert load_split("random_0", pool="sub-01").split_family == "random"
    assert load_split("cluster_k5_2", pool="sub-01").split_family == "cluster_k5"
    assert load_split("tau", pool="sub-01").split_family == "tau"


def test_load_all_splits_returns_twelve():
    all_sp = load_all_splits(pool="sub-01")
    assert len(all_sp) == 12
    assert all(isinstance(sp, Split) for sp in all_sp.values())


# ── OOD split (re:vision Method 3) ─────────────────────────────


def test_list_ood_types_returns_nine_categories():
    types = list_ood_types()
    assert len(types) == 9
    assert types == sorted(types)
    assert "shape" in types and "illusion-classic" in types


@pytest.mark.parametrize("pool,expected_train", [
    ("shared", _POOL_SIZE_SHARED),
    ("sub-01", _POOL_SIZE_PER_SUBJECT),
    ("sub-07", _POOL_SIZE_PER_SUBJECT),
])
def test_ood_split_sizes(pool, expected_train):
    train, test = get_train_test_ids("ood", pool=pool)
    assert len(train) == expected_train
    assert len(test) == _N_OOD
    assert all(iid.startswith("shared_4rep_OOD_") for iid in test)
    assert load_split("ood", pool=pool).split_family == "ood"


def test_ood_test_set_is_identical_across_pools():
    """OOD images are shared-block — same 371 across every pool."""
    _, test_shared = get_train_test_ids("ood", pool="shared")
    for sub in ("sub-01", "sub-03", "sub-05", "sub-06", "sub-07"):
        _, test_sub = get_train_test_ids("ood", pool=sub)
        assert test_sub == test_shared


def test_ood_types_filter_keeps_only_requested_categories():
    train, test_shape = get_train_test_ids(
        "ood", pool="shared", ood_types=["shape"],
    )
    assert len(train) == _POOL_SIZE_SHARED
    assert len(test_shape) == 82
    assert all("_OOD_shape_" in iid for iid in test_shape)

    _, test_two = get_train_test_ids(
        "ood", pool="shared", ood_types=["shape", "unusual"],
    )
    assert len(test_two) == 82 + 64


def test_ood_types_filter_accepts_string():
    _, test = get_train_test_ids("ood", pool="shared", ood_types="gabor")
    assert len(test) == 10


def test_ood_types_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown ood_types"):
        get_train_test_ids("ood", pool="shared", ood_types=["nonsense"])


def test_ood_types_only_for_ood_split():
    with pytest.raises(ValueError, match="only valid for the 'ood' split"):
        get_train_test_ids("tau", pool="shared", ood_types=["shape"])


def test_get_split_masks_with_ood_types():
    _, test_shape = get_train_test_ids("ood", pool="shared", ood_types=["shape"])
    trials = pd.DataFrame({"label": test_shape + ["unrelated.jpg"] * 5})
    train_mask, test_mask = get_split_masks(
        trials, "ood", pool="shared", ood_types=["shape"],
    )
    assert test_mask.sum() == 82
    assert train_mask.sum() == 0  # none of the OOD test ids are in the train pool


# ── Variants ───────────────────────────────────────────────────


def test_variant_train_test_disjoint_for_random_split():
    sp = load_split("random_0", pool="sub-01")
    v = sp.variants[0]
    assert isinstance(v, SplitVariant)
    assert len(v.train_ids) == sp.n_train
    assert len(v.test_ids) == sp.n_test
    assert not (set(v.train_ids) & set(v.test_ids))


def test_get_train_test_ids_returns_tuple_of_lists():
    train, test = get_train_test_ids("random_0", pool="sub-01")
    assert isinstance(train, list) and isinstance(test, list)
    assert len(train) == 4666
    assert len(test) == 1167


# ── Validation ─────────────────────────────────────────────────


def test_load_split_rejects_unknown_name():
    with pytest.raises(ValueError, match="Unknown split"):
        load_split("nope", pool="sub-01")


def test_load_split_rejects_unknown_pool():
    with pytest.raises(ValueError, match="Unknown pool"):
        load_split("random_0", pool="sub-02")


def test_get_train_test_ids_unknown_variant_errors():
    with pytest.raises(ValueError, match="variant_id"):
        get_train_test_ids("random_0", pool="sub-01", variant_id=999)


# ── Masking helper ─────────────────────────────────────────────


def test_get_split_masks_with_dataframe():
    train_ids, test_ids = get_train_test_ids("random_0", pool="sub-01")
    noise = ["something_else.jpg"] * 5
    mock_labels = train_ids[:50] + test_ids[:50] + noise
    trials = pd.DataFrame({"label": mock_labels})
    train_mask, test_mask = get_split_masks(trials, "random_0", pool="sub-01")
    assert train_mask.dtype == bool and test_mask.dtype == bool
    assert len(train_mask) == len(trials)
    assert train_mask.sum() == 50
    assert test_mask.sum() == 50
    assert (train_mask & test_mask).sum() == 0
    assert not train_mask[-5:].any() and not test_mask[-5:].any()


def test_get_split_masks_with_array_of_labels():
    train_ids, test_ids = get_train_test_ids("tau", pool="shared")
    arr = np.array(train_ids[:10] + test_ids[:10])
    train_mask, test_mask = get_split_masks(arr, "tau", pool="shared")
    assert train_mask.sum() == 10
    assert test_mask.sum() == 10


# ── Pool consistency ───────────────────────────────────────────


def test_shared_pool_ids_are_subset_of_per_subject_pool():
    """Shared images should appear in every subject's pool too."""
    shared_train, shared_test = get_train_test_ids("random_0", pool="shared")
    shared_all = set(shared_train) | set(shared_test)
    for sub in ("sub-01", "sub-03", "sub-05", "sub-06", "sub-07"):
        sub_train, sub_test = get_train_test_ids("random_0", pool=sub)
        sub_all = set(sub_train) | set(sub_test)
        assert shared_all.issubset(sub_all), (
            f"shared pool not a subset of {sub} pool"
        )
