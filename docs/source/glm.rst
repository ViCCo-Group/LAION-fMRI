===
GLM
===

General Linear Model (GLM) analysis for the LAION-fMRI dataset.

Overview
========

The General Linear Model is used to identify brain responses to experimental conditions by 
modeling the BOLD signal as a linear combination of experimental regressors and confounds.
==========

Concept
-------

The GLM models each voxel's time series as:

.. math::

    Y = X\\beta + \\epsilon

Where:

* :math:`Y` = observed BOLD signal (time series)
* :math:`X` = design matrix (predictors)
* :math:`\\beta` = parameter estimates (effect sizes)
* :math:`\\epsilon` = residual error

Design Matrix Components
-------------------------

The design matrix includes:

1. **Task regressors**: Experimental conditions convolved with HRF
2. **Nuisance regressors**: Motion, physiological noise, etc.
3. **Drift terms**: Polynomial or cosine basis set

First-Level Analysis
====================

Subject-Level Modeling
----------------------

First-level GLM analyzes individual subject data.

**Setup:**

.. code-block:: python

    from nilearn.glm.first_level import FirstLevelModel, make_first_level_design_matrix
    import pandas as pd
    import nibabel as nib
    from nilearn import plotting
    import matplotlib.pyplot as plt
    
    # Load preprocessed data
    func_img = nib.load(
        'derivatives/preprocessed/sub-01/func/'
        'sub-01_task-experiment_run-01_space-MNI152_desc-preproc_bold.nii.gz'
    )
    
    # Load events
    events = pd.read_csv(
        'sub-01/func/sub-01_task-experiment_run-01_events.tsv',
        sep='\t'
    )
    
    # Load confounds
    confounds = pd.read_csv(
        'derivatives/preprocessed/sub-01/func/'
        'sub-01_task-experiment_run-01_desc-confounds_timeseries.tsv',
        sep='\t'
    )
    
    print(f"Functional data shape: {func_img.shape}")
    print(f"Number of events: {len(events)}")

**Create Design Matrix:**

.. code-block:: python

    import numpy as np
    
    # Define parameters
    tr = 2.0  # Repetition time
    n_scans = func_img.shape[3]
    frame_times = np.arange(n_scans) * tr
    
    # Select confounds
    confound_vars = ['trans_x', 'trans_y', 'trans_z', 
                     'rot_x', 'rot_y', 'rot_z',
                     'global_signal', 'csf', 'white_matter']
    selected_confounds = confounds[confound_vars]
    
    # Create design matrix
    design_matrix = make_first_level_design_matrix(
        frame_times,
        events=events,
        hrf_model='spm',  # SPM canonical HRF
        drift_model='cosine',
        high_pass=0.01,
        add_regs=selected_confounds
    )
    
    # Visualize design matrix
    from nilearn.plotting import plot_design_matrix
    
    plot_design_matrix(design_matrix)
    plt.tight_layout()
    plt.show()

**Fit GLM:**

.. code-block:: python

    # Initialize GLM
    fmri_glm = FirstLevelModel(
        t_r=tr,
        noise_model='ar1',  # AR(1) autocorrelation
        standardize=False,
        hrf_model='spm',
        drift_model='cosine',
        high_pass=0.01
    )
    
    # Fit the model
    fmri_glm = fmri_glm.fit(
        func_img,
        events=events,
        confounds=selected_confounds
    )
    
    print("GLM fitted successfully")

Contrast Definition
-------------------

Define contrasts to test specific hypotheses:

.. code-block:: python

    from nilearn.glm.first_level import compute_contrast
    
    # Simple contrast: one condition vs baseline
    contrast_face = fmri_glm.compute_contrast('face')
    
    # Differential contrast: condition A vs B
    contrast_diff = fmri_glm.compute_contrast('face - scene')
    
    # Complex contrast: average of multiple conditions
    contrast_avg = fmri_glm.compute_contrast('0.5*face + 0.5*object')
    
    # Display contrast
    plotting.plot_stat_map(
        contrast_diff,
        threshold=3.0,
        title='Face > Scene (z-score)',
        display_mode='ortho',
        cut_coords=(0, 0, 0)
    )
    plt.show()

**T-statistic Maps:**

.. code-block:: python

    # Compute contrast with t-statistic
    z_map = fmri_glm.compute_contrast('face - scene', output_type='z_score')
    t_map = fmri_glm.compute_contrast('face - scene', output_type='stat')
    effect_map = fmri_glm.compute_contrast('face - scene', output_type='effect_size')
    
    # Display all three
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    plotting.plot_stat_map(z_map, threshold=3.0, title='Z-score',
                          axes=axes[0], cut_coords=(0, 0, 0))
    plotting.plot_stat_map(t_map, threshold=3.0, title='T-statistic',
                          axes=axes[1], cut_coords=(0, 0, 0))
    plotting.plot_stat_map(effect_map, title='Effect Size',
                          axes=axes[2], cut_coords=(0, 0, 0))
    
    plt.tight_layout()
    plt.show()

Multi-Run Analysis
------------------

Combining multiple runs for one subject:

.. code-block:: python

    from nilearn.image import concat_imgs
    
    # Load multiple runs
    run_imgs = []
    run_events = []
    run_confounds = []
    
    for run in range(1, 5):  # 4 runs
        img_path = (f'derivatives/preprocessed/sub-01/func/'
                    f'sub-01_task-experiment_run-{run:02d}_space-MNI152_desc-preproc_bold.nii.gz')
        events_path = (f'sub-01/func/'
                      f'sub-01_task-experiment_run-{run:02d}_events.tsv')
        confounds_path = (f'derivatives/preprocessed/sub-01/func/'
                         f'sub-01_task-experiment_run-{run:02d}_desc-confounds_timeseries.tsv')
        
        run_imgs.append(nib.load(img_path))
        run_events.append(pd.read_csv(events_path, sep='\t'))
        run_confounds.append(pd.read_csv(confounds_path, sep='\t')[confound_vars])
    
    # Fit GLM with multiple runs
    fmri_glm = FirstLevelModel(t_r=2.0, noise_model='ar1')
    fmri_glm = fmri_glm.fit(run_imgs, events=run_events, confounds=run_confounds)
    
    # Compute contrast across all runs
    z_map = fmri_glm.compute_contrast('face - scene', output_type='z_score')

Model Diagnostics
-----------------

**Residuals Check:**

.. code-block:: python

    # Get residuals
    residuals = fmri_glm.residuals[0]  # First run
    
    # Compute residual variance
    residual_var = image.math_img('np.var(img, axis=3)', img=residuals)
    
    # Display
    plotting.plot_stat_map(
        residual_var,
        title='Residual Variance',
        colorbar=True
    )
    plt.show()

**Design Matrix Inspection:**

.. code-block:: python

    # Check for collinearity
    design_mat = fmri_glm.design_matrices_[0]
    correlation = design_mat.corr()
    
    plt.figure(figsize=(12, 10))
    plt.imshow(correlation, cmap='RdBu_r', vmin=-1, vmax=1)
    plt.colorbar(label='Correlation')
    plt.xticks(range(len(correlation.columns)), correlation.columns, rotation=90)
    plt.yticks(range(len(correlation.columns)), correlation.columns)
    plt.title('Design Matrix Correlation')
    plt.tight_layout()
    plt.show()

Group-Level Analysis
====================

Second-Level GLM
----------------

Combine first-level contrast maps across subjects:

.. code-block:: python

    from nilearn.glm.second_level import SecondLevelModel
    import glob
    
    # Collect first-level contrast maps
    contrast_imgs = glob.glob(
        'derivatives/glm/first_level/sub-*/sub-*_contrast-faceVsScene_stat-z.nii.gz'
    )
    
    print(f"Found {len(contrast_imgs)} subjects")
    
    # Set up second-level model
    second_level_model = SecondLevelModel(smoothing_fwhm=5.0)
    
    # Fit model (one-sample t-test)
    design_matrix = pd.DataFrame([1] * len(contrast_imgs), columns=['intercept'])
    second_level_model = second_level_model.fit(contrast_imgs, design_matrix=design_matrix)
    
    # Compute group contrast
    z_map = second_level_model.compute_contrast(output_type='z_score')
    
    # Display group result
    plotting.plot_stat_map(
        z_map,
        threshold=3.1,  # p < 0.001 uncorrected
        title='Group Face > Scene',
        display_mode='ortho'
    )
    plt.show()

**With Covariates:**

.. code-block:: python

    # Load participant information
    participants = pd.read_csv('participants.tsv', sep='\t')
    
    # Create design matrix with age as covariate
    design_matrix = pd.DataFrame({
        'intercept': 1,
        'age': participants['age']
    })
    
    # Fit model with covariate
    second_level_model = second_level_model.fit(
        contrast_imgs,
        design_matrix=design_matrix
    )
    
    # Test age effect
    age_effect = second_level_model.compute_contrast(
        'age',
        output_type='z_score'
    )

Multiple Comparisons Correction
================================

Family-Wise Error (FWE)
------------------------

Control for false positives across all voxels:

.. code-block:: python

    from nilearn.glm import threshold_stats_img
    
    # Apply FWE correction (permutation-based)
    from nilearn.glm.second_level import non_parametric_inference
    
    # Perform permutation test
    neg_log_pvals_permuted_ols_unmasked = non_parametric_inference(
        contrast_imgs,
        design_matrix=design_matrix,
        model_intercept=True,
        n_perm=10000,  # Number of permutations
        two_sided_test=False,
        n_jobs=4
    )
    
    # Threshold at p < 0.05 FWE-corrected
    thresholded = threshold_stats_img(
        neg_log_pvals_permuted_ols_unmasked,
        alpha=0.05,
        height_control='fwe'
    )

False Discovery Rate (FDR)
---------------------------

More lenient than FWE, controls proportion of false positives:

.. code-block:: python

    # Apply FDR correction
    thresholded_fdr, threshold = threshold_stats_img(
        z_map,
        alpha=0.05,
        height_control='fdr'
    )
    
    print(f"FDR threshold: {threshold}")
    
    # Display FDR-corrected map
    plotting.plot_stat_map(
        thresholded_fdr,
        title='Group Result (FDR p < 0.05)',
        display_mode='ortho',
        cut_coords=(0, 0, 0)
    )
    plt.show()

Cluster-Level Thresholding
---------------------------

Control for clusters rather than individual voxels:

.. code-block:: python

    # Cluster-level inference
    from nilearn.reporting import get_clusters_table
    
    # Get cluster table
    cluster_table = get_clusters_table(
        z_map,
        stat_threshold=3.1,  # Cluster-forming threshold
        cluster_threshold=20  # Minimum cluster size in voxels
    )
    
    print(cluster_table)
    
    # Display clusters
    plotting.plot_stat_map(
        z_map,
        threshold=3.1,
        title='Cluster-level Results',
        display_mode='ortho'
    )
    plt.show()

ROI Analysis
============

Region of Interest Analysis
----------------------------

Extract and analyze signals from predefined regions:

.. code-block:: python

    from nilearn import datasets
    from nilearn.maskers import NiftiLabelsMasker
    
    # Load atlas
    atlas = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')
    atlas_img = atlas.maps
    labels = atlas.labels
    
    # Create masker
    masker = NiftiLabelsMasker(
        labels_img=atlas_img,
        standardize=True,
        memory='nilearn_cache'
    )
    
    # Extract signals
    roi_signals = masker.fit_transform(func_img, confounds=selected_confounds)
    
    print(f"ROI signals shape: {roi_signals.shape}")
    print(f"Number of ROIs: {len(labels)}")

**ROI-based GLM:**

.. code-block:: python

    # Fit GLM on ROI signals
    from nilearn.glm.first_level import run_glm
    
    # Create design matrix
    design_matrix = make_first_level_design_matrix(
        frame_times,
        events=events,
        hrf_model='spm'
    )
    
    # Fit GLM for each ROI
    labels_glm = run_glm(roi_signals, design_matrix.values)
    
    # Extract betas for a contrast
    contrast_vector = np.array([1, -1] + [0] * (design_matrix.shape[1] - 2))  # face vs scene
    
    roi_betas = []
    for roi_idx in range(roi_signals.shape[1]):
        beta = np.dot(contrast_vector, labels_glm[roi_idx][0])
        roi_betas.append(beta)
    
    # Plot ROI effect sizes
    plt.figure(figsize=(12, 6))
    plt.bar(range(len(roi_betas)), roi_betas)
    plt.xlabel('ROI')
    plt.ylabel('Effect Size (face - scene)')
    plt.title('ROI-wise Effect Sizes')
    plt.xticks(range(len(labels)), labels, rotation=90)
    plt.tight_layout()
    plt.show()

Results Storage
===============

Saving GLM Results
------------------

.. code-block:: text

    derivatives/glm/
    ├── first_level/
    │   └── sub-01/
    │       ├── sub-01_contrast-faceVsBaseline_stat-t.nii.gz
    │       ├── sub-01_contrast-faceVsBaseline_stat-z.nii.gz
    │       ├── sub-01_contrast-faceVsScene_stat-t.nii.gz
    │       ├── sub-01_contrast-faceVsScene_stat-z.nii.gz
    │       └── sub-01_design_matrix.png
    └── group_level/
        ├── group_contrast-faceVsScene_stat-t.nii.gz
        ├── group_contrast-faceVsScene_stat-z.nii.gz
        └── group_contrast-faceVsScene_stat-z_fdr-corrected.nii.gz

**Save Contrast Maps:**

.. code-block:: python

    import os
    
    # Save first-level results
    output_dir = 'derivatives/glm/first_level/sub-01/'
    os.makedirs(output_dir, exist_ok=True)
    
    # Save z-map
    z_map.to_filename(
        os.path.join(output_dir, 'sub-01_contrast-faceVsScene_stat-z.nii.gz')
    )
    
    # Save t-map
    t_map.to_filename(
        os.path.join(output_dir, 'sub-01_contrast-faceVsScene_stat-t.nii.gz')
    )
    
    # Save design matrix plot
    from nilearn.plotting import plot_design_matrix
    
    fig = plot_design_matrix(design_matrix)
    fig.savefig(os.path.join(output_dir, 'sub-01_design_matrix.png'), dpi=150)
    plt.close()
