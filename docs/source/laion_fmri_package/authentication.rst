================================
Authentication (pre-release only)
================================

The bucket is private during development and public after
release. The package wraps the official ``awscli`` (a hard
dependency) and respects its standard credential chain:

1. ``AWS_ACCESS_KEY_ID`` / ``AWS_SECRET_ACCESS_KEY`` env vars
2. ``~/.aws/credentials`` profile
3. IAM role (when running on AWS infrastructure)

If none of the above resolves, all S3 calls are made with
``--no-sign-request`` -- which is what you want once the bucket
is public.

In-process helper
=================

For dev users without an AWS CLI install or a configured
profile, the easiest path is the in-process helper:

.. code-block:: python

   from laion_fmri.config import set_aws_credentials

   set_aws_credentials(
       access_key_id="AKIA...",
       secret_access_key="...",
       # region defaults to LAION_FMRI_REGION (us-west-2)
   )

It only sets environment variables for the current Python
process; **nothing is written to disk**.

Sanity check what the AWS CLI sees:

.. code-block:: python

   from laion_fmri._s3_engine import has_aws_credentials

   has_aws_credentials()      # → True if signed requests are possible

When the bucket goes public
===========================

After release the bucket becomes anonymous-readable.
Concretely:

* ``set_aws_credentials(...)`` becomes optional.
* ``has_aws_credentials()`` may return ``False`` -- that's fine,
  the package transparently falls back to ``--no-sign-request``.
* All other code stays the same.
