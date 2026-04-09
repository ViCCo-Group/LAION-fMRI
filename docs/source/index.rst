.. image:: _static/laion_fmri_logo_mosaic.png
   :align: center
   :width: 800px
   :alt: LAION-fMRI Logo


.. warning::

   **Draft documentation.** This documentation is a work in progress and is not
   yet complete. Sections may be incomplete, inaccurate, or subject to change
   before the dataset's official release. Please treat all content as
   provisional.


What is LAION-fMRI?
===================

.. todo::

   Introductory description of the dataset (1 paragraph). Cover:

   - What it is (large-scale open fMRI dataset for visual neuroscience)
   - Key numbers (N participants, N stimuli, N sessions)
   - What's included at a high level
   - Who it's for

Key Features
============

.. todo::

   Bullet list of 4-6 headline features. Keep each to one line + a brief
   clarification. These should be the things that make someone want to use
   the dataset.

Getting Started
===============

.. grid:: 1 1 3 3
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
   :caption: Core Data

   anatomical_data
   fmri_data
   diffusion
   rois
   retinotopy
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
   technical_notes
   example_methods_text
   contributing
   release-history


Latest Updates
==============

.. todo::

   Keep this short — 3-5 most recent updates, one line each. Move older
   entries to :doc:`release-history` when the list gets long.

* **YYYY-MM-DD** — (placeholder)
