===============
Behavioral Data
===============

Behavioral measurements collected during the LAION-fMRI scanning sessions.

Overview
========

Behavioral data includes participant responses, reaction times, and task performance metrics 
collected during fMRI acquisition.

Response Data
=============

Data Collection
---------------

Behavioral responses were recorded using:

* **Input device**: MRI-compatible button box
* **Response mapping**: Documented in task description
* **Recording software**: Synchronized with stimulus presentation
* **Sampling rate**: Millisecond precision

Response Metrics
----------------

**Collected Measures:**

* **Reaction time (RT)**: Time from stimulus onset to response
* **Accuracy**: Correct vs. incorrect responses
* **Response type**: Which button was pressed
* **Miss rate**: Trials with no response
* **False alarms**: Responses on non-target trials (if applicable)

File Organization
=================

Behavioral data is stored alongside functional data:

.. code-block:: text

    sub-01/
    └── func/
        ├── sub-01_task-nback_run-01_events.tsv
        ├── sub-01_task-nback_run-01_events.json
        ├── sub-01_task-nback_run-01_beh.json
        └── sub-01_task-nback_run-01_beh.tsv

File Formats
------------

**Events File (*_events.tsv):**

Contains trial-by-trial information including onset times, durations, and conditions.

**Behavioral Data File (*_beh.tsv):**

Contains detailed response information:

.. code-block:: text

    trial    onset    stimulus_id    trial_type    response    RT    correct
    1        2.0      stim_0001      face          1           823   1
    2        6.5      stim_0045      scene         2           912   1
    3        11.2     stim_0123      object        0           0     0
    4        15.8     stim_0002      face          1           756   1

**Metadata File (*_beh.json):**

.. code-block:: json

    {
        "TaskName": "visual_categorization",
        "Instructions": "Press button 1 for faces, button 2 for other categories",
        "ResponseDevice": "Current Designs 932 Button Box",
        "ResponseMapping": {
            "1": "face",
            "2": "non-face"
        }
    }

Loading Behavioral Data
=======================

Using the Python Package
-------------------------

The ``laion-fmri-dataloader`` package provides convenient functions for loading and analyzing behavioral data:

.. code-block:: python

    from laion_fmri_dataloader import LAIONfMRIDataset
    import matplotlib.pyplot as plt
    
    # Initialize dataset
    dataset = LAIONfMRIDataset(data_dir='./laion-fmri-data')
    
    # Load behavioral data for a specific subject and run
    beh_data = dataset.load_behavioral(
        subject='sub-01',
        task='nback',
        run=1
    )
    
    print(f"Total trials: {len(beh_data)}")
    print(f"Columns: {beh_data.columns.tolist()}")
    

Eye Tracking Data
=================

If Available
------------

Some sessions may include eye tracking data:

.. code-block:: text

    sub-01/
    └── func/
        ├── sub-01_task-nback_run-01_recording-eyetrack_physio.tsv.gz
        └── sub-01_task-nback_run-01_recording-eyetrack_physio.json

Eye Tracking Metrics
--------------------

When available, eye tracking data includes:

* **Gaze position**: X, Y coordinates
* **Pupil size**: Diameter in arbitrary units
* **Blinks**: Blink events and duration
* **Fixations**: Fixation locations and durations
* **Saccades**: Saccade metrics


Summary Statistics
==================

Aggregating Across Runs
------------------------

Combine data from multiple runs:

.. code-block:: python

    import glob
    
    # Load all runs for a subject
    beh_files = glob.glob('sub-01/func/*_beh.tsv')
    all_runs = pd.concat([pd.read_csv(f, sep='\t') for f in beh_files])
    
    # Overall statistics
    print(f"Total trials: {len(all_runs)}")
    print(f"Overall accuracy: {all_runs['correct'].mean():.2%}")
    print(f"Overall mean RT: {all_runs[all_runs['RT'] > 0]['RT'].mean():.0f} ms")
