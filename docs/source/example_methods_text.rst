====================
Example Methods Text
====================

Ready-to-use text for the methods section of papers using the LAION-fMRI
dataset. Adapt as needed for your specific analyses.

Short Version (~2 sentences)
============================

.. todo::

   Fill in the blanks below once dataset parameters are finalized.

    We used data from the LAION-fMRI dataset (CITATION, YEAR), an open fMRI
    dataset comprising [N] participants who viewed [N] unique natural images
    during event-related fMRI scanning at [X]T. Single-trial response estimates
    were obtained using GLMsingle (Prince et al., 2022).

Standard Version
================

.. todo::

   Fill in the blanks below once dataset parameters are finalized.

    We used functional and anatomical MRI data from the LAION-fMRI dataset
    (CITATION, YEAR; freely available at [URL]). The dataset includes [N]
    healthy adult participants ([N] female, mean age [X] +/- [X] years), each
    of whom completed [N] scanning sessions. In each session, participants
    viewed [N] unique natural images presented for [X] ms each in an
    event-related design while performing a [task description]. Functional
    images were acquired on a [manufacturer] [field strength] [model] scanner
    using a [sequence] (TR = [X] s, TE = [X] ms, [X] mm isotropic voxels,
    multiband factor = [X]). High-resolution T1-weighted anatomical images
    ([X] mm isotropic) were also acquired for each participant.

    Functional data were preprocessed using [pipeline] ([version]; CITATION),
    including [list key steps]. Single-trial beta estimates were computed using
    GLMsingle (Prince et al., 2022), which optimizes the hemodynamic response
    function per voxel, applies data-driven denoising (GLMdenoise), and
    regularizes estimates via ridge regression.

Citation
========

.. todo::

   Add the full citation once the paper is published.

.. code-block:: text

    (placeholder — add full citation)

BibTeX:

.. code-block:: bibtex

    @dataset{laion_fmri,
      title={LAION-fMRI: ...},
      author={...},
      year={...},
      url={...}
    }

If you use the GLMsingle beta estimates, also cite:

.. code-block:: bibtex

    @article{prince2022glmsingle,
      title={Improving the accuracy of single-trial fMRI response estimates using GLMsingle},
      author={Prince, Jacob S and Charest, Ian and Bhatt, Prapti and others},
      journal={eLife},
      volume={11},
      pages={e77599},
      year={2022}
    }

.. todo::

   Add citations for other tools used (fMRIPrep, FreeSurfer, pRF software,
   etc.) that users should cite depending on which data products they use.

Acknowledgment
==============

We suggest including the following acknowledgment:

    This work used data from the LAION-fMRI dataset
    (https://github.com/ViCCo-Group/LAION-fMRI), provided by the ViCCo Group.
