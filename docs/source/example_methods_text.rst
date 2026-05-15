====================
Example Methods Text
====================

Ready-to-use text for the methods section of papers using the LAION-fMRI
dataset. Adapt as needed for your specific analyses.

Interim Methods Text
====================

We used data from LAION-fMRI, a densely sampled 7T fMRI dataset of
human visual responses to natural images (Zerbe et al., 2026). In the
launch release, five participants viewed 25,052 distinct images across
150 main image-viewing sessions. Images were presented in an
event-related design while participants performed a continuous
recognition task, and single-trial response estimates were derived
with GLMsingle (Prince et al., 2022) from preprocessed multi-echo 7T
BOLD data.

For analyses using the package loaders, it is useful to report the
exact subject IDs, sessions, ROI or noise-ceiling filters, and
train/test split names used in your analysis.

Citation
========

Until the dataset paper is available, cite the VSS 2026 conference
presentation:

   Zerbe, J., Roth, J., Mell, M. M., Herholz, P., Knapen, T., &
   Hebart, M. N. (2026). *LAION-fMRI: A densely sampled 7T-fMRI
   dataset providing broad coverage of natural image diversity*. Talk
   25.11, Scene Perception Talk Session, Vision Sciences Society
   Annual Meeting, May 16, 2026. `VSS abstract
   <https://www.visionsciences.org/talk-sessions?id=642>`__.

BibTeX:

.. code-block:: bibtex

   @misc{zerbe2026laionfmri,
     title = {LAION-fMRI: A densely sampled 7T-fMRI dataset providing broad coverage of natural image diversity},
     author = {Zerbe, Josefine and Roth, Johannes and Mell, Maggie Mae and Herholz, Peer and Knapen, Tomas and Hebart, Martin N.},
     year = {2026},
     note = {Talk 25.11, Scene Perception Talk Session, Vision Sciences Society Annual Meeting, May 16, 2026},
     url = {https://www.visionsciences.org/talk-sessions?id=642}
   }

If you use the GLMsingle beta estimates, also cite:

.. code-block:: bibtex

   @article{prince2022glmsingle,
     title = {Improving the accuracy of single-trial fMRI response estimates using GLMsingle},
     author = {Prince, Jacob S. and Charest, Ian and Kurzawski, Jan W. and Pyles, John A. and Tarr, Michael J. and Kay, Kendrick N.},
     journal = {eLife},
     volume = {11},
     pages = {e77599},
     year = {2022},
     doi = {10.7554/eLife.77599}
   }

Acknowledgment
==============

We suggest including the following acknowledgment:

    This work used data from the LAION-fMRI dataset
    (https://github.com/ViCCo-Group/LAION-fMRI), provided by the ViCCo Group.
