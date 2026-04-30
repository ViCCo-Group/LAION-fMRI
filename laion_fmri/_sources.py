"""Source configuration for the LAION-fMRI S3 bucket."""

LAION_FMRI_BUCKET = "laion-fmri"
LAION_FMRI_REGION = "us-west-2"

#: Sessions whose objects are protected by a deny rule on the S3
#: bucket. Public callers receive 403 on GET, so the package excludes
#: them from every download to spare callers a hard crash on the first
#: protected key.
HELD_OUT_SESSIONS = ("ses-31", "ses-32", "ses-33", "ses-34")
