==============
Template space
==============

.. code-block:: python

   from laion_fmri.subject import load_subject

   sub = load_subject("sub-03")
   mni305 = sub.to_template(per_voxel_array, "MNI305")
   fsavg_L = sub.to_template(per_voxel_array, "fsaverage", hemi="L")

``Subject.to_template`` projects subject-T1w-space values into
volume or surface template spaces using the FreeSurfer recon
that ships with each subject. Two parallel chains cover all
supported targets, both pure-Python:

* **Volume chain** -- T1w volume to MNI305 via
  ``mri/transforms/talairach.lta`` (FreeSurfer's linear T1w to
  MNI305 affine; the ``talairach`` filename is historical and
  refers to MNI305, not true Talairach space). Optional second
  hop to MNI152 / MNIColin27 via published affine + resample.
* **Surface chain** -- T1w volume to fsnative surface via
  ``nilearn.surface.vol_to_surf`` on the recon's white / pial
  meshes, then fsnative to fsaverage via
  ``nitransforms.surface.SurfaceResampler`` on the recon's
  ``sphere.reg``.

Setup
=====

The template-space module needs an opt-in extra:

.. code-block:: bash

   uv sync --extra template      # or: pip install laion-fmri[template]

This pulls ``nilearn``, ``nitransforms``, ``neuromaps``, and
``templateflow``. TemplateFlow caches reference images at
``~/.cache/templateflow/`` on first use.

The per-subject FreeSurfer recon is *not* fetched by default
because it adds several hundred megabytes per subject. Pull it
explicitly with ``include_freesurfer=True``:

.. code-block:: python

   from laion_fmri.download import download

   download(subject="sub-03", include_freesurfer=True, n_jobs=4)

You can check whether the recon is on disk with
``sub.has_freesurfer()``.

Supported targets
=================

Pass a target name as the second argument to ``to_template``:

==========================  ========  ===========================================================
Target                      Type      Mechanism
==========================  ========  ===========================================================
``"fsaverage"``             surface   T1w to fsnative (``nilearn.surface.vol_to_surf``) then
                                      fsnative to fsaverage
                                      (``nitransforms.surface.SurfaceResampler``).
                                      Densities via ``fsaverage_density``:
                                      ``fsaverage5`` (10k/hemi, default),
                                      ``fsaverage6`` (41k), ``fsaverage7`` (164k).
``"MNI305"``                volume    Direct affine from the recon's ``talairach.lta``.
                                      Full brain including subcortex.
``"MNI152NLin6Asym"``       volume    MNI305 first, then the Brett 1999 affine.
``"MNI152NLin2009cAsym"``   volume    MNI305 to MNI152NLin6Asym (Brett affine), then to
                                      2009cAsym via the templateflow nonlinear ``.h5`` warp.
                                      This is fmriprep's default target.
==========================  ========  ===========================================================

Other MNI152 variants (``MNI152Lin``, ``MNI152NLin6Sym``, the
2009a/b families, ``MNI152NLin2009cSym``) and ``MNIColin27`` are
out of scope: templateflow ships no transform from MNI305 or
MNI152NLin6Asym to them as of templateflow 24. Run ``fmriprep``
externally if you need one of those.

Return shapes
=============

* **Surface target, single hemi**: 1-D ``ndarray`` over the
  vertices of the requested density.
* **Surface target, no hemi**: ``{"L": ndarray, "R": ndarray}``.
* **Volume target**: ``nibabel.Nifti1Image`` on the templateflow
  reference grid for that target.

Worked example
==============

.. code-block:: python

   from laion_fmri.download import download
   from laion_fmri.subject import load_subject

   download(subject="sub-03", ses="ses-01",
            include_freesurfer=True, n_jobs=4)

   sub = load_subject("sub-03")
   betas = sub.get_betas(session="ses-01", roi="visual")
   mean_b = betas.mean(axis=0)                              # (n_voxels,)

   # Surface: per-hemi fsaverage5 (10k vertices) array.
   fsavg_L = sub.to_template(mean_b, "fsaverage", hemi="L")
   fsavg_R = sub.to_template(mean_b, "fsaverage", hemi="R")
   fsavg_both = sub.to_template(mean_b, "fsaverage")  # {"L": ..., "R": ...}

   # Volume: MNI305 (includes subcortex).
   mni305 = sub.to_template(mean_b, "MNI305")

   # Volume: MNI152NLin6Asym via MNI305 + Brett affine.
   mni152_fsl = sub.to_template(mean_b, "MNI152NLin6Asym")

   # Volume: MNI152NLin2009cAsym (fmriprep's default), via the
   # extra MNI152NLin6Asym -> 2009cAsym templateflow warp.
   mni152_fmriprep = sub.to_template(mean_b, "MNI152NLin2009cAsym")

Explicit per-direction entry points
===================================

``Subject.to_template`` accepts any volume input and dispatches
on the target name. Three more specific methods make the
input → output direction explicit and refuse mismatched targets
up front:

.. code-block:: python

   # Volume input -> volume target (MNI*).
   sub.volume_to_template(mean_b, "MNI305")
   sub.volume_to_template(mean_b, "MNI152NLin2009cAsym")

   # Volume input -> surface target (fsaverage).
   sub.volume_to_surface(mean_b, hemi="L")
   sub.volume_to_surface(mean_b)                # dict of L+R

   # fsnative-surface input -> fsaverage.
   roi_L = sub.get_roi_data("FFA1",
                            format="func.gii", hemi="L")
   sub.surface_to_template(roi_L["FFA1"]["gii"]["hemi-L"]["func.gii"],
                           hemi="L")
   sub.surface_to_template({"L": lh_array, "R": rh_array})

``surface_to_template`` accepts either a single hemisphere
array (with ``hemi="L"`` or ``"R"``) or a ``{"L": ..., "R": ...}``
dict; the return shape matches the input shape. The input
array's length must equal the recon's fsnative vertex count
for that hemisphere -- a ``ValueError`` is raised otherwise.

Writing BIDS-conformant files
=============================

Pass ``output_dir=`` to also persist the result to disk under a
BIDS filename. Optional ``desc`` and ``session`` kwargs fill
the corresponding tokens:

.. code-block:: python

   sub.to_template(
       mean_b, "MNI305",
       output_dir="./out",
       desc="MeanBeta",
       session="ses-01",
   )

The filename pattern is::

   sub-{ID}[_ses-{S}]_space-{SPACE}[_den-{D}][_hemi-{L|R}][_desc-{DESC}]_statmap.{ext}

``.nii.gz`` for volume targets, ``.func.gii`` for surface
targets (one file per hemisphere). The density token (``den-``)
uses BIDS-recommended labels (``10k`` for fsaverage5,
``41k`` for fsaverage6, ``164k`` for fsaverage7).

Concrete examples for the call above:

* ``sub-03_ses-01_space-MNI305_desc-MeanBeta_statmap.nii.gz``
* ``sub-03_ses-01_space-fsaverage_den-10k_hemi-L_desc-MeanBeta_statmap.func.gii``

When ``hemi=None`` on a surface target, two files are written
(one per hemisphere) and ``to_template`` returns the matching
``{"L": ..., "R": ...}`` dict.

Out of scope
============

The following targets are *not* supported in this release:

* **fsLR** and **CIVET** -- their fsaverage hand-off in
  ``neuromaps`` calls Connectome Workbench's ``wb_command``
  binary, which falls outside the pure-Python install.
* **MNI152 via the surface chain** -- ``neuromaps`` ships
  ``mni152_to_fsaverage`` (volume to surface) but no
  surface-to-MNI152 transform without ``wb_command``. Use
  the volume route to reach MNI152 from T1w via MNI305.
* **Other MNI152 variants and MNIColin27** --
  ``MNI152Lin``, ``MNI152NLin6Sym``,
  ``MNI152NLin2009{a,b}{Asym,Sym}``,
  ``MNI152NLin2009cSym``, and ``MNIColin27`` have no
  templateflow transform from MNI305 or from
  MNI152NLin6Asym, and no canonical published affine. Run
  ``fmriprep`` externally if you need one of these.
* **fsaverage1, fsaverage2, fsaverage3** -- not on
  templateflow. Supported densities are
  ``fsaverage5`` / ``fsaverage6`` / ``fsaverage7``.

API
===

.. currentmodule:: laion_fmri.templates

.. autofunction:: to_template
