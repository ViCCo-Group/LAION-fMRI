:og:title: LAION-fMRI - a 7T fMRI dataset of human vision
:og:description: LAION-fMRI (LfMRI / LAION MRI dataset): 5 subjects, 25,052 launch-release natural images, 165 acquired 7T fMRI sessions with single-trial GLMsingle betas, retinotopy, localizers, and diffusion.

.. meta::
   :description: LAION-fMRI (also known as LfMRI or the LAION MRI dataset) is a deeply-sampled 7T fMRI dataset of brain responses to 25,052 launch-release natural images across 150 main image-viewing sessions, with 165 fMRI sessions acquired overall. Used by the re:vision replication initiative.
   :keywords: LAION-fMRI, LAION fMRI, LfMRI, LAION MRI dataset, 7T fMRI, visual neuroscience, GLMsingle, NSD, THINGS, revision initiative, re:vision

.. raw:: html

   <script type="application/ld+json">
   {
     "@context": "https://schema.org",
     "@type": "Dataset",
     "name": "LAION-fMRI",
     "alternateName": ["LfMRI", "LAION fMRI", "LAION MRI dataset"],
     "description": "A deeply-sampled 7T fMRI dataset of brain responses to natural visual images. Five participants viewed 25,052 launch-release images across 150 main image-viewing sessions at 1.8 mm resolution; 165 fMRI sessions were acquired overall, with single-trial GLMsingle betas, retinotopic mapping, functional localizers, and diffusion MRI.",
     "url": "https://laion-fmri.hebartlab.com/",
     "sameAs": "https://re-vision-initiative.org/dataset",
     "keywords": ["fMRI", "7T", "visual neuroscience", "natural images", "GLMsingle", "neuroimaging", "LAION"],
     "measurementTechnique": "Ultra-high-field 7T functional magnetic resonance imaging (BOLD)",
     "variableMeasured": "BOLD signal (single-trial beta estimates)",
     "spatialCoverage": "Whole brain (1.8 mm isotropic)",
     "license": "https://creativecommons.org/publicdomain/zero/1.0/",
     "conditionsOfAccess": "The fMRI data, metadata, and derived stimulus annotations are public. Raw stimulus images require acceptance of the LAION-fMRI Data Use Agreement.",
     "creator": {
       "@type": "Organization",
       "name": "ViCCo-Group (Hebart Lab)",
       "url": "https://hebartlab.com"
     }
   }
   </script>

   <link rel="stylesheet" href="_static/hero/hero.css">
   <div id="lf-hero-root">
     <noscript>
       <p style="text-align:center;margin:1.5em 0;">
         <img src="_static/laion_fmri_logo_mosaic.png"
              alt="LAION-fMRI"
              style="max-width:800px;width:100%;">
       </p>
       <p style="text-align:center;">
         A deeply-sampled 7T fMRI dataset of human vision.
         <a href="quickstart.html">Get started</a>
       </p>
     </noscript>
   </div>
   <script src="_static/hero/hero.js" defer></script>
   <script>
     window.addEventListener("DOMContentLoaded", function () {
       if (!window.LaionFmriHero) return;
       window.LaionFmriHero.init({
         logoSrc: "_static/laion_fmri_logo_mosaic.png",
         title: "A deeply-sampled fMRI dataset of <em>human vision</em>",
         lede: "Five participants. 25,052 launch-release images. 165 acquired 7T BOLD sessions with single-trial GLMsingle betas, retinotopy, localizers, and diffusion.",
         primaryHref: "quickstart.html",
         primaryLabel: "Get started",
         meta: ["5 subjects", "25K+ stimuli", "7T multi-echo", "Open access"]
       });
     });
   </script>

**LAION-fMRI** is a deeply-sampled 7T fMRI dataset of brain responses to visual
images, built to uncover how the human brain sees and understands the world.
Five participants viewed 25,052 unique natural images across the launch
release's 150 main image-viewing sessions, capturing hundreds of thousands of
brain responses at 1.8 mm resolution with an ultra-high-field 7T MRI scanner.
Across all acquired fMRI protocols, the dataset contains 165 fMRI sessions;
the supplemental image sessions and their additional shared images will be
released later.

The images span everything from everyday photographs - drawn from a 120M
image-text corpus (Roth & Hebart, 2025) - to abstract shapes and visual
illusions, ensuring the dataset covers the full breadth of human visual
experience. Every image was measured multiple times, delivering exceptional
signal quality and setting new standards for the field.

Beyond functional brain scans, the dataset includes rich complementary data:
retinotopic mapping, functional localizers, precision diffusion MRI, and
behavioral responses - making it one of the most deeply characterized
neuroimaging resources assembled to date.

* **Scale** - thousands of unique images per participant (including 1,492
  shared images in the launch release), 30 main image-viewing sessions each,
  up to 12 repeats for shared images
* **Acquisition** - multi-echo 7T fMRI at 1.8 mm isotropic, 1.9 s TR
* **Broad sampling** - natural photographs, prior benchmark images (NSD,
  THINGS), plus out-of-distribution test stimuli
* **Single-trial betas** - GLMsingle-derived response estimates with strong
  noise ceilings
* **Complementary data** - retinotopy, functional localizers, diffusion MRI,
  behavioral responses
* **Open** - freely available for research

Getting Started
===============

.. grid:: 1 2 2 2
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

    .. grid-item-card:: Brain Viewer
        :link: https://laion-fmri.hebartlab.com/brain/
        :class-card: sd-border-0
        :shadow: sm

        Interactive 3D brain explorer

        +++
        Browse responses in-browser


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
   :caption: Python Package

   laion_fmri_package/index
   auto_examples/index

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Core Data

   anatomical_data
   fmri_data
   rois
   localizers
   glmsingle_betas

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Stimuli & Splits

   stimulus_data
   stimulus_derivatives
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
   example_methods_text
   contributing


Citation
========

Until the dataset paper is available, please cite the VSS 2026
conference presentation:

   Zerbe, J., Roth, J., Mell, M. M., Herholz, P., Knapen, T., &
   Hebart, M. N. (2026). *LAION-fMRI: A densely sampled 7T-fMRI
   dataset providing broad coverage of natural image diversity*. Talk
   25.11, Scene Perception Talk Session, Vision Sciences Society
   Annual Meeting, May 16, 2026. `VSS abstract
   <https://www.visionsciences.org/talk-sessions?id=642>`__.

If you use the provided GLMsingle beta estimates, also cite
GLMsingle. See :doc:`example_methods_text` for BibTeX and suggested
methods wording.


Contributors
============

.. raw:: html

   <div class="lf-contributors" aria-label="LAION-fMRI contributors">
     <a class="lf-contributor-card" href="https://www.cbs.mpg.de/mitarbeitende/zerbe" target="_blank" rel="noopener noreferrer" aria-label="Josefine Zerbe website">
       <img src="_static/contributors/josefine-zerbe.jpg" alt="Josefine Zerbe" class="lf-contributor-photo">
       <h2>Josefine Zerbe</h2>
     </a>
     <a class="lf-contributor-card" href="https://jroth.space/" target="_blank" rel="noopener noreferrer" aria-label="Johannes Roth website">
       <img src="_static/contributors/johannes-roth.jpg" alt="Johannes Roth" class="lf-contributor-photo">
       <h2>Johannes Roth</h2>
     </a>
     <a class="lf-contributor-card" href="https://www.cbs.mpg.de/publication-search/1730732?person=%2Fpersons%2Fresource%2Fpersons305549" target="_blank" rel="noopener noreferrer" aria-label="Robert Satzger website">
       <img src="_static/contributors/robert-satzger.jpg" alt="Robert Satzger" class="lf-contributor-photo">
       <h2>Robert Satzger</h2>
     </a>
     <a class="lf-contributor-card" href="https://peerherholz.github.io/" target="_blank" rel="noopener noreferrer" aria-label="Peer Herholz website">
       <img src="_static/contributors/peer-herholz.jpg" alt="Peer Herholz" class="lf-contributor-photo">
       <h2>Peer Herholz</h2>
     </a>
     <a class="lf-contributor-card" href="https://lucakaemmer.github.io" target="_blank" rel="noopener noreferrer" aria-label="Luca Kämmer website">
       <img src="_static/contributors/luca-kaemmer.jpg" alt="Luca Kämmer" class="lf-contributor-photo">
       <h2>Luca Kämmer</h2>
     </a>
     <a class="lf-contributor-card" href="https://hebartlab.com/" target="_blank" rel="noopener noreferrer" aria-label="Vinzent Jakob website">
       <img src="_static/contributors/vinzent-jakob.jpg" alt="Vinzent Jakob" class="lf-contributor-photo">
       <h2>Vinzent Jakob</h2>
     </a>
     <a class="lf-contributor-card" href="http://martin-hebart.de/" target="_blank" rel="noopener noreferrer" aria-label="Martin Hebart website">
       <img src="_static/contributors/martin-hebart.jpg" alt="Martin Hebart" class="lf-contributor-photo">
       <h2>Martin Hebart</h2>
     </a>
   </div>
