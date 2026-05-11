.. raw:: html

   <link rel="stylesheet" href="_static/hero/hero.css">
   <div id="lf-hero-root">
     <noscript>
       <p style="text-align:center;margin:1.5em 0;">
         <img src="_static/laion_fmri_logo_mosaic.png"
              alt="LAION-fMRI"
              style="max-width:800px;width:100%;">
       </p>
       <p style="text-align:center;">
         A deeply-sampled 7T fMRI dataset of human vision.
         <a href="quickstart.html">Get started</a> &middot;
         <a href="https://laion-fmri.hebartlab.com/brain/">Brain viewer</a>
       </p>
     </noscript>
   </div>
   <script src="_static/hero/hero.js" defer></script>
   <script>
     window.addEventListener("DOMContentLoaded", function () {
       if (!window.LaionFmriHero) return;
       window.LaionFmriHero.init({
         logoSrc: "_static/laion_fmri_logo_mosaic.png",
         title: "A deeply-sampled fMRI dataset of <em>human vision</em>",
         lede: "Five participants. 25,000+ natural images. 165 sessions of 7T BOLD with single-trial GLMsingle betas, retinotopy, localizers, and diffusion.",
         primaryHref: "quickstart.html",
         primaryLabel: "Get started",
         secondaryHref: "https://laion-fmri.hebartlab.com/brain/",
         secondaryLabel: "Brain viewer",
         meta: ["5 subjects", "25K+ stimuli", "7T multi-echo", "Open access"]
       });
     });
   </script>


.. warning::

   **Draft documentation.** This documentation is a work in progress and is not
   yet complete. Sections may be incomplete, inaccurate, or subject to change
   before the dataset's official release. Please treat all content as
   provisional.


Getting Started
===============

.. grid:: 1 2 2 2
    :gutter: 2

    .. grid-item-card:: Quickstart
        :link: quickstart
        :link-type: doc
        :class-card: sd-border-0
        :shadow: sm

        Get started quickly with basic examples

        +++
        Load and explore the data in minutes

    .. grid-item-card:: Dataset at a Glance
        :link: dataset_at_a_glance
        :link-type: doc
        :class-card: sd-border-0
        :shadow: sm

        Overview of all data, spaces, and ROIs

        +++
        What's in the dataset and what you need

    .. grid-item-card:: Data Access
        :link: data_access
        :link-type: doc
        :class-card: sd-border-0
        :shadow: sm

        Download and access instructions

        +++
        AWS S3, Python package, and more

    .. grid-item-card:: Brain Viewer
        :link: https://laion-fmri.hebartlab.com/brain/
        :class-card: sd-border-0
        :shadow: sm

        Interactive 3D voxel explorer

        +++
        Browse responses and concept maps in-browser


.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Getting Started

   Home <self>
   quickstart
   dataset_at_a_glance
   data_access

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Python Package

   laion_fmri_package/index
   auto_examples/index

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Core Data

   anatomical_data
   fmri_data
   rois
   localizers
   glmsingle_betas

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Stimuli & Splits

   stimulus_data
   train_test_splits

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Methods

   experimental_design
   mri_acquisition
   preprocessing
   quality_control
   stimulus_selection
   metadata_acquisition

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Reference

   faq
   example_methods_text
   contributing
   release-history


Latest Updates
==============

.. todo::

   Keep this short — 3-5 most recent updates, one line each. Move older
   entries to :doc:`release-history` when the list gets long.

* **YYYY-MM-DD** — (placeholder)
