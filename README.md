# LAION-fMRI

**Data loading package and documentation for the LAION-fMRI dataset**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD--3--Clause-yellow.svg)](https://opensource.org/licenses/BSD-3-Clause)

LAION-fMRI is a deeply sampled 7T fMRI dataset of brain responses to
natural images, collected and curated by ViCCo-Group. This repository
contains the Python package and documentation for dataset access,
structure, specifications, and usage guidelines.

## 📚 Documentation

Full documentation is available at https://laion-fmri.hebartlab.com/ and includes:

- Dataset specifications and structure
- Access and usage guidelines
- Technical details and metadata
- Contributing guidelines

## 📖 Documentation Development

This repository uses Sphinx for documentation. To set up a development environment:

```bash
# Create a conda environment from the development environment file
conda env create -f environment-dev.yml
conda activate laion-fmri-dev

# Build the documentation
cd docs
make html
```

The built documentation will be available in `docs/build/html/`.

## 📄 License

The package code is licensed under BSD-3-Clause. The fMRI data and
public derivatives are released under CC0 1.0. Raw stimulus images
require the LAION-fMRI Data Use Agreement.

## 🤝 Contributing

Contributions are welcome! Please see the Contributing Guidelines in the documentation for details.

## 📞 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/ViCCo-Group/LAION-fMRI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ViCCo-Group/LAION-fMRI/discussions)

## 🙏 Acknowledgments
