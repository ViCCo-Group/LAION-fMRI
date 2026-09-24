"""Source configuration for the LAION-fMRI S3 bucket."""

LAION_FMRI_BUCKET = "laion-fmri"
LAION_FMRI_REGION = "us-west-2"

#: Sessions whose objects are protected by a deny rule on the S3
#: bucket. Public callers receive 403 on GET, so the package excludes
#: them from every download to spare callers a hard crash on the first
#: protected key.
HELD_OUT_SESSIONS = ("ses-31", "ses-32", "ses-33", "ses-34")

#: Tasks whose *localizer derivatives* are released from inside a
#: held-out session. The object localizer was acquired in ses-31; its
#: derived maps expose none of the held-out stimuli. The exemption is
#: limited to ``HELD_OUT_EXEMPT_PREFIX``, so raw or preprocessed ses-31
#: files of the same task stay embargoed. The bucket policy carves out
#: the same keys.
HELD_OUT_EXEMPT_TASKS = ("oloc",)
HELD_OUT_EXEMPT_PREFIX = "derivatives/localizers/"
