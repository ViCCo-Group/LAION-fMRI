from laion_fmri._sources import LAION_FMRI_BUCKET, LAION_FMRI_REGION


def test_laion_fmri_bucket_name():
    assert LAION_FMRI_BUCKET == "laion-fmri"


def test_laion_fmri_region():
    assert LAION_FMRI_REGION == "us-west-2"
