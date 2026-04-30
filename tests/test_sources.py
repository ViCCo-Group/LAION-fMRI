from laion_fmri._sources import (
    HELD_OUT_SESSIONS,
    LAION_FMRI_BUCKET,
    LAION_FMRI_REGION,
)


def test_laion_fmri_bucket_name():
    assert LAION_FMRI_BUCKET == "laion-fmri"


def test_laion_fmri_region():
    assert LAION_FMRI_REGION == "us-west-2"


def test_held_out_sessions_match_bucket_policy():
    """The package's exclusion list must mirror the bucket's deny rule.

    If these drift apart, the package will either crash on protected
    GETs (constant missing a session) or silently withhold public data
    (constant naming a session that's actually public).
    """
    assert HELD_OUT_SESSIONS == ("ses-31", "ses-32", "ses-33", "ses-34")
