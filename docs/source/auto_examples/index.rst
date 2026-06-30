:orphan:

================
Examples gallery
================

Hands-on walkthroughs of the ``laion_fmri`` Python package. Each
example is a runnable script that you can copy-paste or download
as a Jupyter notebook from the link at the bottom of its page.

Recommended reading order:

1. :doc:`plot_01_quickstart`, end-to-end: initialize, query,
   download one session, load it.
2. :doc:`plot_02_initialization`, focused walk-through of the
   one-time setup: data directory and license acceptance.
3. :doc:`plot_03_querying`, discover what is in the bucket and
   inspect per-subject data.
4. :doc:`plot_04_loading`, the full load API: betas,
   noise-ceiling maps, ROI masks, brain-space mapping, group
   loading, and PyTorch.
5. :doc:`plot_05_segmentations`, per-image object-level
   segmentation masks for the shared stimulus set.

For a complete reference of the package's public API, see
:doc:`/laion_fmri_package/index`.


.. raw:: html

  <div id='sg-tag-list' class='sphx-glr-tag-list'></div>


.. raw:: html

    <div class="sphx-glr-thumbnails">

.. thumbnail-parent-div-open

.. raw:: html

    <div class="sphx-glr-thumbcontainer" tooltip="This example is the recommended starting point for a new user. It walks through a typical LAION-fMRI workflow end-to-end and introduces the four steps that any later analysis builds on.">

.. only:: html

  .. image:: /auto_examples/images/thumb/sphx_glr_plot_01_quickstart_thumb.png
    :alt:

  :doc:`/auto_examples/plot_01_quickstart`

.. raw:: html

      <div class="sphx-glr-thumbnail-title">Quick Start</div>
    </div>


.. raw:: html

    <div class="sphx-glr-thumbcontainer" tooltip="Before any of the loaders or download helpers can do anything useful, a small amount of one-time setup is needed. This example walks through what that setup involves and why each step exists.">

.. only:: html

  .. image:: /auto_examples/images/thumb/sphx_glr_plot_02_initialization_thumb.png
    :alt:

  :doc:`/auto_examples/plot_02_initialization`

.. raw:: html

      <div class="sphx-glr-thumbnail-title">Dataset Initialization</div>
    </div>


.. raw:: html

    <div class="sphx-glr-thumbcontainer" tooltip="A dataset is much easier to work with once it is clear what is in it: which subjects exist, which ROIs ship per subject, which train/test splits are bundled, and so on. This example introduces the two discovery APIs the package exposes for that purpose, and then shows how to inspect a single subject&#x27;s on-disk data once a target has been picked.">

.. only:: html

  .. image:: /auto_examples/images/thumb/sphx_glr_plot_03_querying_thumb.png
    :alt:

  :doc:`/auto_examples/plot_03_querying`

.. raw:: html

      <div class="sphx-glr-thumbnail-title">Querying the Dataset</div>
    </div>


.. raw:: html

    <div class="sphx-glr-thumbcontainer" tooltip="This example walks through the loaders that turn a downloaded subject directory into usable arrays: single-trial betas, noise-ceiling maps, ROI masks, and stimulus images. The goal is to give a feel for what each accessor does, how its arguments interact, and which patterns to reach for in real analyses.">

.. only:: html

  .. image:: /auto_examples/images/thumb/sphx_glr_plot_04_loading_thumb.png
    :alt:

  :doc:`/auto_examples/plot_04_loading`

.. raw:: html

      <div class="sphx-glr-thumbnail-title">Loading Data</div>
    </div>


.. raw:: html

    <div class="sphx-glr-thumbcontainer" tooltip="A lot of analyses on this dataset ask questions of the form &quot;is this voxel&#x27;s response driven by the piano in the image, or by the hand on the piano?&quot;. Answering that requires knowing, for each image, exactly which pixels correspond to which object. This example introduces the segmentation masks the dataset ships to enable that kind of analysis, and shows how to retrieve them from both the stimulus side (by image name) and the subject side (by trial index).">

.. only:: html

  .. image:: /auto_examples/images/thumb/sphx_glr_plot_05_segmentations_thumb.png
    :alt:

  :doc:`/auto_examples/plot_05_segmentations`

.. raw:: html

      <div class="sphx-glr-thumbnail-title">Object Segmentations</div>
    </div>


.. raw:: html

    <div class="sphx-glr-thumbcontainer" tooltip="While data is shared in a subject&#x27;s own T1w space, it is possible to move the maps onto a shared template, making them ready for group-level comparison.">

.. only:: html

  .. image:: /auto_examples/images/thumb/sphx_glr_plot_06_templates_thumb.png
    :alt:

  :doc:`/auto_examples/plot_06_templates`

.. raw:: html

      <div class="sphx-glr-thumbnail-title">Template-Space Projection</div>
    </div>


.. thumbnail-parent-div-close

.. raw:: html

    </div>


.. toctree::
   :hidden:

   /auto_examples/plot_01_quickstart
   /auto_examples/plot_02_initialization
   /auto_examples/plot_03_querying
   /auto_examples/plot_04_loading
   /auto_examples/plot_05_segmentations
   /auto_examples/plot_06_templates


.. only:: html

  .. container:: sphx-glr-footer sphx-glr-footer-gallery

    .. container:: sphx-glr-download sphx-glr-download-python

      :download:`Download all examples in Python source code: auto_examples_python.zip </auto_examples/auto_examples_python.zip>`

    .. container:: sphx-glr-download sphx-glr-download-jupyter

      :download:`Download all examples in Jupyter notebooks: auto_examples_jupyter.zip </auto_examples/auto_examples_jupyter.zip>`


.. only:: html

 .. rst-class:: sphx-glr-signature

    `Gallery generated by Sphinx-Gallery <https://sphinx-gallery.github.io>`_
