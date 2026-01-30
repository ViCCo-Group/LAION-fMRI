================
Dataset Overview
================

The LAION-fMRI dataset provides ... It includes functional MRI scans, 
structural images, behavioral measurements, and detailed stimulus information.

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Modalities

   stimulus_data
   experiments
   behavioral_data
   structural_data
   functional_data
   glm_data

Quick Overview
==============

.. grid:: 1 1 2 2
    :gutter: 3

    .. grid-item-card:: 🎨 Stimulus Data
        :link: stimulus_data
        :link-type: doc
        :class-card: sd-border-0
        :shadow: sm

        Visual stimuli and metadata
        
        +++
        Images, categories, and properties

    .. grid-item-card:: 🧪 Experiments
        :link: experiments
        :link-type: doc
        :class-card: sd-border-0
        :shadow: sm

        Experimental design and tasks
        
        +++
        Trial structure and conditions

    .. grid-item-card:: 📊 Behavioral Data
        :link: behavioral_data
        :link-type: doc
        :class-card: sd-border-0
        :shadow: sm

        Response data and metrics
        
        +++
        Reaction times and accuracy

    .. grid-item-card:: 🧠 Structural Data
        :link: structural_data
        :link-type: doc
        :class-card: sd-border-0
        :shadow: sm

        Anatomical MRI scans
        
        +++
        T1-weighted images and segmentation

    .. grid-item-card:: 🧠 Functional Data
        :link: functional_data
        :link-type: doc
        :class-card: sd-border-0
        :shadow: sm

        fMRI acquisitions
        
        +++
        BOLD data and time series

    .. grid-item-card:: 📈 GLM Data
        :link: glm_data
        :link-type: doc
        :class-card: sd-border-0
        :shadow: sm

        Statistical analysis results
        
        +++
        Contrast maps and effect sizes

Dataset Structure
=================

The dataset follows BIDS-like conventions:

.. code-block:: text

    LAION-fMRI/
    ├── dataset_description.json
    ├── participants.tsv
    ├── README
    ├── stimuli/                   # Stimulus images and metadata
    ├── sub-01/
    │   ├── anat/                  # Structural scans
    │   ├── func/                  # Functional scans
    │   └── beh/                   # Behavioral data
    ├── sub-02/
    └── derivatives/
        ├── preprocessed/          # Preprocessed data
        ├── glm/                   # Statistical results
        └── quality_control/       # QC reports

Data Formats
============

**Neuroimaging Data:**

* NIfTI format (.nii.gz) for MRI data
* JSON sidecar files for metadata

**Behavioral Data:**

* TSV format for events and responses
* JSON for metadata

**Stimulus Data:**

* PNG/JPEG for images
* TSV/JSON for metadata
