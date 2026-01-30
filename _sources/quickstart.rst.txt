==========
Quickstart
==========

This guide will help you get started with the LAION-fMRI dataset quickly.

Getting Access
==============

The LAION-fMRI dataset can be accessed in two ways:

**1. Direct AWS Access**

* Direct download from AWS S3 buckets
* Suitable for downloading entire dataset or specific subjects
* Provides full control over data storage and management
* Requires AWS CLI or similar tools

**2. Python Package (laion_fmri_dataloader)**

* Streamlined Python interface for data access
* Built-in data validation and integrity checks
* Automatic handling of file paths and metadata
* Convenient for programmatic access and integration into analysis pipelines

.. note::
   
   Some parts of the dataset require a **Data Use Agreement (DUA)**. Please review 
   the :doc:`data_access` section for details on accessing restricted data components.

Access Methods
--------------

Choose your preferred method for accessing the LAION-fMRI dataset:

.. tab-set::

    .. tab-item:: AWS S3 Access

        **Prerequisites:**
        
        * AWS CLI installed: ``pip install awscli``
        * AWS credentials (for restricted data only)

        **Download entire dataset:**

        .. code-block:: bash

           aws s3 sync s3://laion-fmri/ ./laion-fmri-data/ --no-sign-request

        **Download specific subject:**

        .. code-block:: bash

           aws s3 sync s3://laion-fmri/sub-01/ ./laion-fmri-data/sub-01/ --no-sign-request

        **Download derivatives only:**

        .. code-block:: bash

           aws s3 sync s3://laion-fmri/derivatives/ ./laion-fmri-data/derivatives/ --no-sign-request

        .. note::
           
           For restricted data requiring DUA, remove ``--no-sign-request`` and 
           configure AWS credentials with appropriate access permissions.

    .. tab-item:: Python Package

        **Installation:**

        .. code-block:: bash

           pip install laion-fmri-dataloader

        **Basic Usage:**

        .. code-block:: python

           from laion_fmri_dataloader import LAIONfMRIDataset
           
           # Initialize dataset
           dataset = LAIONfMRIDataset(data_dir='./laion-fmri-data')
           
           # Download specific subject
           dataset.download_subject('sub-01')
           
           # Load functional data
           func_data = dataset.load_functional('sub-01', task='experiment', run=1)
           
           # Load stimulus metadata
           stimuli = dataset.load_stimuli()
           
           print(f"Functional data shape: {func_data.shape}")
           print(f"Number of stimuli: {len(stimuli)}")

        **With authentication (restricted data):**

        .. code-block:: python

           # Configure credentials
           dataset = LAIONfMRIDataset(
               data_dir='./laion-fmri-data',
               aws_access_key='YOUR_ACCESS_KEY',
               aws_secret_key='YOUR_SECRET_KEY'
           )
           
           # Download restricted components
           dataset.download_subject('sub-01', include_restricted=True)



Quick Example
=============

Loading fMRI Data
-----------------

.. code-block:: python

    import nibabel as nib
    
    # Load a functional MRI scan
    fmri_img = nib.load('path/to/sub-01/func/sub-01_task-experiment_bold.nii.gz')
    fmri_data = fmri_img.get_fdata()
    
    print(f"Data shape: {fmri_data.shape}")

Working with Stimulus Data
---------------------------

.. code-block:: python

    import pandas as pd
    
    # Load stimulus information
    stimuli = pd.read_csv('path/to/stimuli/stimulus_metadata.csv')
    print(stimuli.head())

Next Steps
==========

* Explore the :doc:`dataset_overview` to understand the complete dataset structure
* Review the :doc:`processing_pipeline` for analysis workflows
* Check the :doc:`faq` for common questions
