============
Contributing
============

.. todo::

   Review and finalize this page before the dataset release.

We welcome contributions to the LAION-fMRI documentation and tooling.

Ways to Contribute
==================

- **Improve documentation** — fix typos, add examples, clarify explanations
- **Report issues** — found something unclear or incorrect? Open a
  `GitHub issue <https://github.com/ViCCo-Group/LAION-fMRI/issues>`_
- **Share analysis examples** — scripts, notebooks, or visualizations that
  might help other researchers

Setting Up
==========

1. Fork and clone the repository:

   .. code-block:: bash

      git clone https://github.com/YOUR-USERNAME/LAION-fMRI.git
      cd LAION-fMRI

2. Create the development environment:

   .. code-block:: bash

      conda env create -f environment.yml
      conda activate laion-fmri-dev

3. Build the docs:

   .. code-block:: bash

      cd docs
      make html
      # Open docs/build/html/index.html in your browser

Making Changes
==============

1. Create a branch: ``git checkout -b your-branch-name``
2. Edit files in ``docs/source/`` (reStructuredText format)
3. Build and preview: ``make html``
4. Commit, push, and open a Pull Request on GitHub

Style Guide
===========

- Clear, concise language
- Include code examples where helpful
- Follow existing structure and formatting
- Ensure code examples are correct and runnable

Questions?
==========

Open an issue on `GitHub <https://github.com/ViCCo-Group/LAION-fMRI/issues>`_.
