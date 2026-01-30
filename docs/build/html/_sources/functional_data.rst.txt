===============
Functional Data
===============

Functional MRI (fMRI) data acquired during experimental tasks in the LAION-fMRI dataset.

Overview
========

The dataset includes BOLD (Blood Oxygen Level Dependent) functional MRI data acquired while 
participants performed visual perception tasks.

fMRI Acquisitions
=================

Acquisition Parameters
----------------------

**Sequence Details:**

* **Sequence type**: Gradient-echo Echo Planar Imaging (GE-EPI)
* **Field strength**: 3 Tesla
* **TR (Repetition Time)**: 2.0 seconds (or as specified in JSON)
* **TE (Echo Time)**: 30 ms (or as specified)
* **Flip angle**: 90° (or as specified)
* **Voxel size**: 2.5 x 2.5 x 2.5 mm³ (or as specified)
* **Matrix size**: 80 x 80 (or as specified)
* **Number of slices**: 36-48 (or as specified)
* **Slice orientation**: Axial
* **Phase encoding**: Anterior-Posterior (or as specified)
* **Multiband acceleration**: If applicable

**Coverage:**

* Whole brain coverage
* Optimized for visual cortex

File Organization
=================

Functional data structure:

.. code-block:: text

    sub-01/
    └── func/
        ├── sub-01_task-nback_run-01_bold.nii.gz
        ├── sub-01_task-nback_run-01_bold.json
        ├── sub-01_task-nback_run-01_events.tsv
        ├── sub-01_task-nback_run-02_bold.nii.gz
        ├── sub-01_task-nback_run-02_bold.json
        ├── sub-01_task-nback_run-02_events.tsv
        └── ...

File Components
---------------

**BOLD data (*_bold.nii.gz):**

4D NIfTI file


**Metadata (*_bold.json):**

Acquisition parameters and timing information

.. code-block:: json

    {
        "TaskName": "visual_categorization",
        "RepetitionTime": 2.0,
        "EchoTime": 0.03,
        "FlipAngle": 90,
        "SliceTiming": [0, 0.5, 1.0, 1.5],
        "PhaseEncodingDirection": "j",
        "EffectiveEchoSpacing": 0.000495,
        "TotalReadoutTime": 0.03915
    }

**Events (*_events.tsv):**

Trial timing and experimental conditions

.. code-block:: tsv

    onset	duration	trial_type	stimulus_id	response_time	accuracy
    2.0	0.5	face	stim_0001	0.823	1
    6.5	0.5	scene	stim_0045	0.912	1
    11.2	0.5	object	stim_0123	0.0	0
    15.8	0.5	face	stim_0002	0.756	1
    20.1	0.5	scene	stim_0048	0.892	1
    24.7	0.5	object	stim_0126	0.634	1
    29.3	0.5	baseline	n/a	n/a	n/a
    33.9	0.5	face	stim_0005	0.801	1

**Events metadata (*_events.json):**

Descriptions of the events file columns

.. code-block:: json

    {
        "onset": {
            "LongName": "Event onset time",
            "Description": "Time in seconds from the start of acquisition when the event begins",
            "Units": "seconds"
        },
        "duration": {
            "LongName": "Event duration",
            "Description": "Duration of the stimulus presentation",
            "Units": "seconds"
        },
        "trial_type": {
            "LongName": "Trial type",
            "Description": "Category or type of stimulus presented in this trial",
            "Levels": {
                "face": "Human face stimulus",
                "scene": "Natural or indoor scene stimulus",
                "object": "Object stimulus",
                "baseline": "Fixation or rest period"
            }
        },
        "stimulus_id": {
            "LongName": "Stimulus identifier",
            "Description": "Unique identifier for the specific stimulus image presented, references stimuli.tsv"
        },
        "response_time": {
            "LongName": "Response time",
            "Description": "Time in seconds from stimulus onset to participant response. 0 indicates no response or missed trial",
            "Units": "seconds"
        },
        "accuracy": {
            "LongName": "Response accuracy",
            "Description": "Whether the participant's response was correct",
            "Levels": {
                "1": "Correct response",
                "0": "Incorrect response or miss",
                "n/a": "No response required for this trial type"
            }
        }
    }

Loading Functional Data
=======================