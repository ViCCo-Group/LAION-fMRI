===================
Processing Pipeline
===================

This section describes the processing pipeline used for the LAION-fMRI dataset, including 
quality control, preprocessing, and statistical analysis steps.

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Pipeline Steps

   quality_control
   preprocessing
   glm

Pipeline Overview
=================

.. grid:: 1 1 3 3
    :gutter: 2

    .. grid-item-card:: ✅ Quality Control
        :link: quality_control
        :link-type: doc
        :class-card: sd-border-0
        :shadow: sm

        Data quality assessment
        
        +++
        Motion, signal quality, artifacts

    .. grid-item-card:: 🔧 Preprocessing
        :link: preprocessing
        :link-type: doc
        :class-card: sd-border-0
        :shadow: sm

        Data preprocessing steps
        
        +++
        correction, registration, normalization

    .. grid-item-card:: 📊 GLM
        :link: glm
        :link-type: doc
        :class-card: sd-border-0
        :shadow: sm

        Statistical analysis
        
        +++
        First-level and group-level analysis

Workflow Summary
================

ADD CONCEPTUAL WORKFLOW GRAPHIC HERE.

The complete processing workflow:

1. **Quality Control**
   
   Quality control was performed using `mriqc <https://mriqc.readthedocs.io/>`_. 

   * Assess raw data quality
   * Identify motion artifacts
   * Check signal-to-noise ratio
   * Generate QC reports

2. **Preprocessing**
   
   * ....
   * ....


3. **GLM Analysis**
   
   * ....
   * ....

Processing Tools
================

The pipeline uses ...


Output Organization
===================

Processed data is organized in the derivatives folder:

.. code-block:: text

    derivatives/
    ├── preprocessing/
    │   └── sub-01/
    │       ├── anat/
    │       └── func/
    ├── mriqc/
    │   └── sub-01/
    │       └── qc_reports/
    └── glm/
        ├── first_level/
        │   └── sub-01/
        └── group_level/
