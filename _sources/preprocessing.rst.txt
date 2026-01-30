==============
Preprocessing
==============

Preprocessing pipeline for the LAION-fMRI dataset.

Overview
========

Preprocessing transforms raw fMRI data into a form suitable for statistical analysis. The 
LAION-fMRI dataset includes both raw and preprocessed data.

The preprocessing pipeline uses ...



Preprocessing Steps
===================


Preprocessing Parameters
========================

Standard Parameters
-------------------

The preprocessing pipeline uses these standard parameters:

.. code-block:: json

    {
        "slice_timing": "ascending",
        "slice_timing_ref": 0.5,
        "motion_correction": "MCFLIRT",
        "motion_reference": "middle",
        "sdc_method": "fieldmap",
        "registration": "bbr",
        "normalization_template": "MNI152NLin2009cAsym",
        "normalization_resolution": [2, 2, 2],
        "smoothing_fwhm": 5.0,
        "highpass_filter": 0.01,
        "detrend": true,
        "standardize": false
    }

Subject-Specific Variations
----------------------------

Some parameters may vary by subject (check individual preprocessing logs):

* SDC method (if fieldmaps unavailable)
* Smoothing kernel (for different analyses)
* Filtering parameters

Output Structure
================

Preprocessed Data Organization
-------------------------------

.. code-block:: text

    derivatives/preprocessing/
    └── sub-01/
        ├── anat/
        │   ├── sub-01_space-MNI152_desc-preproc_T1w.nii.gz
        │   ├── sub-01_space-T1w_desc-brain_mask.nii.gz
        │   ├── sub-01_space-T1w_label-GM_probseg.nii.gz
        │   ├── sub-01_space-T1w_label-WM_probseg.nii.gz
        │   ├── sub-01_space-T1w_label-CSF_probseg.nii.gz
        │   └── sub-01_from-T1w_to-MNI152_mode-image_xfm.h5
        └── func/
            ├── sub-01_task-experiment_run-01_space-MNI152_desc-preproc_bold.nii.gz
            ├── sub-01_task-experiment_run-01_desc-confounds_timeseries.tsv
            ├── sub-01_task-experiment_run-01_desc-brain_mask.nii.gz
            └── ...

Confounds File
--------------

The confounds file contains nuisance regressors. Example excerpt from 
``sub-01_task-experiment_run-01_desc-confounds_timeseries.tsv``:

.. code-block:: tsv

    trans_x	trans_y	trans_z	rot_x	rot_y	rot_z	trans_x_derivative1	trans_y_derivative1	trans_z_derivative1	rot_x_derivative1	rot_y_derivative1	rot_z_derivative1	global_signal	csf	white_matter	framewise_displacement	dvars
    0.0234	-0.0156	0.0089	0.0012	-0.0008	0.0015	n/a	n/a	n/a	n/a	n/a	n/a	582.34	489.12	523.67	n/a	n/a
    0.0241	-0.0163	0.0095	0.0014	-0.0006	0.0018	0.0007	-0.0007	0.0006	0.0002	0.0002	0.0003	581.89	488.76	523.21	0.0234	12.456
    0.0238	-0.0159	0.0091	0.0011	-0.0009	0.0016	-0.0003	0.0004	-0.0004	-0.0003	-0.0003	-0.0002	582.15	489.34	523.89	0.0156	8.234
    0.0245	-0.0167	0.0098	0.0016	-0.0004	0.0021	0.0007	-0.0008	0.0007	0.0005	0.0005	0.0005	581.56	488.45	522.98	0.0298	15.123
    0.0242	-0.0161	0.0093	0.0013	-0.0007	0.0017	-0.0003	0.0006	-0.0005	-0.0003	-0.0003	-0.0004	582.01	489.01	523.45	0.0187	9.876

Common confounds to include in analyses:

* **Motion parameters**: trans_x, trans_y, trans_z, rot_x, rot_y, rot_z
* **Motion derivatives**: trans_x_derivative1, trans_y_derivative1, trans_z_derivative1, rot_x_derivative1, rot_y_derivative1, rot_z_derivative1
* **Global signals**: global_signal, csf, white_matter
* **Quality metrics**: framewise_displacement, dvars

Using Preprocessed Data
========================

Loading for Analysis
--------------------

.. code-block:: python

    from nilearn.glm.first_level import FirstLevelModel
    
    # Load preprocessed functional data
    preproc_img = load_img(
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
    
    # Select confounds
    selected_confounds = confounds[confound_vars]
    
    # Set up GLM
    fmri_glm = FirstLevelModel(
        t_r=2.0,
        noise_model='ar1',
        standardize=False,
        hrf_model='spm',
        drift_model='cosine',
        high_pass=0.01
    )
    
    # Fit model
    fmri_glm = fmri_glm.fit(
        preproc_img,
        events=events,
        confounds=selected_confounds
    )

Quality Checks
==============

Post-Preprocessing QC
----------------------

After preprocessing, verify:

1. **Registration quality**: Check anatomical-functional alignment
2. **Normalization**: Verify proper alignment to template
3. **Coverage**: Ensure no signal dropout
4. **Artifacts**: Check for residual artifacts

.. code-block:: python

    # Check normalization
    from nilearn import datasets, plotting
    
    # Load MNI template
    mni_template = datasets.load_mni152_template()
    
    # Overlay normalized functional on template
    mean_preproc = image.mean_img(preproc_img)
    
    plotting.plot_stat_map(
        mean_preproc,
        bg_img=mni_template,
        title='Normalized Functional on MNI Template',
        threshold=100,
        display_mode='ortho'
    )
    plt.show()
