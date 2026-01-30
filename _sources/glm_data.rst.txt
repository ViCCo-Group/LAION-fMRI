========
GLM Data
========

Statistical analysis results from General Linear Model (GLM) analyses of the LAION-fMRI dataset.

Overview
========

The GLM derivatives contain first-level (subject-level) and group-level statistical maps 
derived from analyzing the functional data.

File Organization
=================

GLM results are stored in the derivatives folder:

.. code-block:: text

    derivatives/
    └── glm/
        ├── first_level/
        │   └── sub-01/
        │       ├── sub-01_task-experiment_contrast-faceVsBaseline_stat-t.nii.gz
        │       ├── sub-01_task-experiment_contrast-faceVsBaseline_stat-z.nii.gz
        │       ├── sub-01_task-experiment_contrast-faceVsScene_stat-t.nii.gz
        │       ├── sub-01_task-experiment_contrast-faceVsScene_stat-z.nii.gz
        │       ├── sub-01_task-experiment_contrast-sceneVsBaseline_stat-t.nii.gz
        │       ├── sub-01_task-experiment_contrast-sceneVsBaseline_stat-z.nii.gz
        │       └── sub-01_task-experiment_design-matrix.png
        └── group_level/
            ├── group_contrast-faceVsBaseline_stat-t.nii.gz
            ├── group_contrast-faceVsBaseline_stat-z.nii.gz
            ├── group_contrast-faceVsBaseline_fdr-corrected.nii.gz
            ├── group_contrast-faceVsScene_stat-t.nii.gz
            ├── group_contrast-faceVsScene_stat-z.nii.gz
            └── group_contrast-faceVsScene_fdr-corrected.nii.gz

First-Level Results
===================

Subject-Level Maps
------------------

Individual subject statistical maps for each contrast:

**File Naming Convention:**

.. code-block:: text

    sub-<label>_task-<label>_contrast-<label>_stat-<type>.nii.gz

Where:

* **sub-<label>**: Subject identifier (e.g., sub-01)
* **task-<label>**: Task name (e.g., task-experiment)
* **contrast-<label>**: Contrast name (e.g., faceVsBaseline)
* **stat-<type>**: Statistic type (t, z, effect)

Available Contrasts
-------------------

Standard contrasts computed for each subject:

**Single Category Contrasts:**

* **faceVsBaseline**: Face stimuli vs. baseline
* **sceneVsBaseline**: Scene stimuli vs. baseline
* **objectVsBaseline**: Object stimuli vs. baseline

**Differential Contrasts:**

* **faceVsScene**: Faces vs. scenes
* **faceVsObject**: Faces vs. objects
* **sceneVsObject**: Scenes vs. objects

Design Matrix Visualization
----------------------------

Each subject includes a design matrix visualization:

.. code-block:: text

    sub-01_task-experiment_design-matrix.png

This shows:

* Task regressors (experimental conditions)
* Confound regressors (motion, signals)
* Temporal structure of the experiment

Loading First-Level Data
-------------------------

Using the Python package:

.. code-block:: python

    from laion_fmri_dataloader import LAIONfMRIDataset
    from nilearn import plotting
    import matplotlib.pyplot as plt
    
    # Initialize dataset
    dataset = LAIONfMRIDataset(data_dir='./laion-fmri-data')
    
    # Load first-level contrast map
    contrast_img = dataset.load_first_level_contrast(
        subject='sub-01',
        task='experiment',
        contrast='faceVsBaseline',
        stat_type='z'
    )
    
    # Display the statistical map
    plotting.plot_stat_map(
        contrast_img,
        threshold=3.1,  # p < 0.001 uncorrected
        title='Face > Baseline (sub-01)',
        display_mode='ortho',
        cut_coords=(0, 0, 0)
    )
    plt.show()
    
    # Load all contrasts for a subject
    all_contrasts = dataset.load_all_contrasts(
        subject='sub-01',
        task='experiment',
        stat_type='z'
    )
    
    print(f"Available contrasts: {list(all_contrasts.keys())}")

Group-Level Results
===================

Group Statistical Maps
-----------------------

Second-level analyses combining data across subjects:

**File Naming Convention:**

.. code-block:: text

    group_contrast-<label>_stat-<type>.nii.gz
    group_contrast-<label>_<correction>-corrected.nii.gz

Where:

* **contrast-<label>**: Contrast name
* **stat-<type>**: Statistic type (t, z)
* **<correction>**: Multiple comparison correction method (fdr, fwe)

Multiple Comparisons Correction
--------------------------------

Statistical maps are provided with different correction methods:

**Uncorrected:**

* Raw t-statistics and z-scores
* Useful for ROI analyses or hypothesis-driven research

**FDR Corrected:**

* False Discovery Rate correction
* Controls proportion of false positives
* More lenient than FWE

**FWE Corrected:**

* Family-Wise Error correction (when available)
* Controls probability of any false positive
* More conservative

Loading Group-Level Data
-------------------------

.. code-block:: python

    # Load group-level contrast
    group_contrast = dataset.load_group_level_contrast(
        contrast='faceVsBaseline',
        stat_type='z'
    )
    
    # Load FDR-corrected map
    group_fdr = dataset.load_group_level_contrast(
        contrast='faceVsBaseline',
        correction='fdr'
    )
    
    # Display both
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    
    plotting.plot_stat_map(
        group_contrast,
        threshold=3.1,
        title='Uncorrected (z > 3.1)',
        axes=axes[0],
        cut_coords=(0, 0, 0)
    )
    
    plotting.plot_stat_map(
        group_fdr,
        threshold=0.05,
        title='FDR Corrected (q < 0.05)',
        axes=axes[1],
        cut_coords=(0, 0, 0)
    )
    
    plt.tight_layout()
    plt.show()

Statistical Metadata
====================

Analysis Parameters
-------------------

Each GLM analysis includes metadata documenting the analysis parameters:

.. code-block:: json

    {
        "AnalysisLevel": "first_level",
        "Model": {
            "Type": "GLM",
            "HRF": "spm",
            "DriftModel": "cosine",
            "HighPassFilter": 0.01,
            "NoiseModel": "ar1"
        },
        "Contrasts": {
            "faceVsBaseline": {
                "Description": "Face stimuli versus baseline",
                "Weights": [1, 0, 0, -1]
            },
            "faceVsScene": {
                "Description": "Face stimuli versus scene stimuli",
                "Weights": [1, -1, 0, 0]
            }
        },
        "Software": {
            "Name": "Nilearn",
            "Version": "0.10.0",
            "Container": "nilearn/nilearn:0.10.0"
        },
        "Confounds": [
            "trans_x", "trans_y", "trans_z",
            "rot_x", "rot_y", "rot_z",
            "global_signal", "csf", "white_matter"
        ]
    }
