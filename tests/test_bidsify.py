"""Tests for the local-side BIDS key normalization helper."""

from laion_fmri._bidsify import bidsify_local_key


def test_label_value_without_hyphen_unchanged():
    key = "sub-01/face/sub-01_label-OFA_mask.nii.gz"
    assert bidsify_local_key(key) == key


def test_single_hyphen_in_label_value_stripped():
    key = (
        "derivatives/rois/sub-01/face/"
        "sub-01_space-T1w_res-1pt8_label-FFA-1_mask.nii.gz"
    )
    expected = (
        "derivatives/rois/sub-01/face/"
        "sub-01_space-T1w_res-1pt8_label-FFA1_mask.nii.gz"
    )
    assert bidsify_local_key(key) == expected


def test_multiple_segments_in_label_value_stripped():
    key = (
        "derivatives/rois/sub-01/face/"
        "sub-01_label-pSTS-faces_mask.nii.gz"
    )
    expected = (
        "derivatives/rois/sub-01/face/"
        "sub-01_label-pSTSfaces_mask.nii.gz"
    )
    assert bidsify_local_key(key) == expected


def test_full_surface_key_preserves_other_entities():
    key = (
        "derivatives/rois/sub-01/face/"
        "sub-01_hemi-L_space-fsnative_label-FFA-1_mask.func.gii"
    )
    out = bidsify_local_key(key)
    assert "label-FFA1" in out
    assert "label-FFA-1" not in out
    # Other entities untouched
    assert "sub-01" in out
    assert "hemi-L" in out
    assert "space-fsnative" in out


def test_compound_label_value_laion_dorsal():
    key = (
        "derivatives/rois/sub-01/laion/"
        "sub-01_space-T1w_res-1pt8_label-laion-dorsal_mask.nii.gz"
    )
    expected = (
        "derivatives/rois/sub-01/laion/"
        "sub-01_space-T1w_res-1pt8_label-laiondorsal_mask.nii.gz"
    )
    assert bidsify_local_key(key) == expected


def test_idempotent():
    key = (
        "derivatives/rois/sub-01/face/"
        "sub-01_label-pSTS-faces_mask.nii.gz"
    )
    once = bidsify_local_key(key)
    twice = bidsify_local_key(once)
    assert once == twice


def test_non_label_hyphenated_entity_untouched():
    """Hyphens inside non-label entity values must not be stripped."""
    # Synthetic case: a hypothetical hyphenated task value.
    key = (
        "derivatives/glmsingle-tedana/sub-01/ses-04/func/"
        "sub-01_ses-04_task-foo-bar_label-FFA-1_mask.nii.gz"
    )
    out = bidsify_local_key(key)
    # task-foo-bar must survive intact
    assert "task-foo-bar" in out
    # label hyphen still stripped
    assert "label-FFA1" in out


def test_label_extension_dot_separator_recognized():
    """Value boundary respects ``.`` as well as ``_``."""
    # Hypothetical: label-VAL.json (no _mask suffix between them)
    key = "label-FFA-1.json"
    assert bidsify_local_key(key) == "label-FFA1.json"


def test_label_at_end_of_string():
    """Value boundary respects end of string."""
    key = "label-FFA-1"
    assert bidsify_local_key(key) == "label-FFA1"
