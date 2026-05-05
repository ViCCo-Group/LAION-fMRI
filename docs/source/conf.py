#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# LAION-fMRI documentation build configuration file

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

# -- General configuration ------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_tabs.tabs",
    "sphinx.ext.todo",
    "sphinx_gallery.gen_gallery",
]

# -- Sphinx-gallery configuration -----------------------------------------
#
# Examples live under <repo>/examples and are rendered as a gallery at
# docs/source/auto_examples. We deliberately do NOT execute them at build
# time -- they call download() / load_subject(), which would require AWS
# credentials and several GB of bandwidth. ``plot_gallery=False`` keeps
# the source narratives + code blocks but skips execution.

sphinx_gallery_conf = {
    "examples_dirs": ["../../examples"],
    "gallery_dirs": ["auto_examples"],
    "filename_pattern": r"plot_",
    "plot_gallery": False,
    "remove_config_comments": True,
    "doc_module": ("laion_fmri",),
}

# Configuration for sphinx-copybutton
copybutton_prompt_text = (
    r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
)
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = False
copybutton_remove_prompts = True
copybutton_line_continuation_character = "\\"

autodoc_mock_imports = []
autosummary_generate = True
templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"

project = "LAION-fMRI"
copyright = "2025, ViCCo-Group"
author = "ViCCo-Group"

_version = "0.1.0"
version = _version
release = _version

language = "en"
exclude_patterns = []
pygments_style = "tango"
pygments_dark_style = "monokai"
todo_include_todos = True


# -- Options for HTML output ----------------------------------------------

html_theme = "furo"

html_theme_options = {
    "dark_css_variables": {
        # re:vision color palette
        "color-brand-primary": "#00d4ff",
        "color-brand-content": "#00d4ff",
        "color-background-primary": "#0a0e1a",
        "color-background-secondary": "#111729",
        "color-background-hover": "#1a2140",
        "color-background-hover--transparent": "#1a214000",
        "color-background-border": "#2a3050",
        "color-foreground-primary": "#e8eaf0",
        "color-foreground-secondary": "#a0a8c0",
        "color-foreground-muted": "#6a7090",
        "color-foreground-border": "#2a3050",
        "color-announcement-background": "#111729",
        "color-announcement-text": "#e8eaf0",
        "color-admonition-background": "#111729",
        "color-card-background": "#111729",
        "color-card-border": "#2a3050",
        "color-highlight-on-target": "#1a2140",
        "color-sidebar-background": "#0a0e1a",
        "color-sidebar-background-border": "#2a3050",
        "color-sidebar-brand-text": "#e8eaf0",
        "color-sidebar-caption-text": "#00d4ff",
        "color-sidebar-link-text": "#a0a8c0",
        "color-sidebar-link-text--top-level": "#e8eaf0",
        "color-sidebar-item-background--current": "#1a2140",
        "color-sidebar-item-background--hover": "#1a2140",
        "color-sidebar-item-expander-background": "transparent",
        "color-sidebar-item-expander-background--hover": "#1a2140",
        "color-sidebar-search-background": "#111729",
        "color-sidebar-search-border": "#2a3050",
        "color-toc-background": "#0a0e1a",
        "color-toc-title-text": "#00d4ff",
        "color-toc-item-text": "#a0a8c0",
        "color-toc-item-text--hover": "#00d4ff",
        "color-toc-item-text--active": "#00d4ff",
        "color-api-background": "#111729",
        "color-api-overall": "#e8eaf0",
        "color-inline-code-background": "#1a2140",
        "color-code-background": "#0d1117",
        "color-code-foreground": "#e8eaf0",
        # Fonts
        "font-stack": "Outfit, -apple-system, BlinkMacSystemFont, sans-serif",
        "font-stack--monospace": "Fira Code, SFMono-Regular, Menlo, Consolas, monospace",
        "font-stack--headings": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif",
    },
    "light_css_variables": {
        # Light mode — clean white with re:vision accent colors
        "color-brand-primary": "#0090b0",
        "color-brand-content": "#0090b0",
        "color-background-primary": "#ffffff",
        "color-background-secondary": "#f5f7fa",
        "color-background-hover": "#eef1f6",
        "color-background-hover--transparent": "#eef1f600",
        "color-background-border": "#d8dde6",
        "color-foreground-primary": "#1a1e2e",
        "color-foreground-secondary": "#4a5068",
        "color-foreground-muted": "#8890a8",
        "color-foreground-border": "#d8dde6",
        "color-announcement-background": "#0090b0",
        "color-announcement-text": "#ffffff",
        "color-admonition-background": "#f5f7fa",
        "color-card-background": "#ffffff",
        "color-card-border": "#d8dde6",
        "color-highlight-on-target": "#e6f7fb",
        "color-sidebar-background": "#f5f7fa",
        "color-sidebar-background-border": "#d8dde6",
        "color-sidebar-brand-text": "#1a1e2e",
        "color-sidebar-caption-text": "#0090b0",
        "color-sidebar-link-text": "#4a5068",
        "color-sidebar-link-text--top-level": "#1a1e2e",
        "color-sidebar-item-background--current": "#e6f7fb",
        "color-sidebar-item-background--hover": "#eef1f6",
        "color-sidebar-item-expander-background": "transparent",
        "color-sidebar-item-expander-background--hover": "#eef1f6",
        "color-sidebar-search-background": "#ffffff",
        "color-sidebar-search-border": "#d8dde6",
        "color-toc-background": "#ffffff",
        "color-toc-title-text": "#0090b0",
        "color-toc-item-text": "#4a5068",
        "color-toc-item-text--hover": "#0090b0",
        "color-toc-item-text--active": "#0090b0",
        "color-api-background": "#f5f7fa",
        "color-api-overall": "#1a1e2e",
        "color-inline-code-background": "#eef1f6",
        "color-code-background": "#f5f7fa",
        "color-code-foreground": "#1a1e2e",
        # Fonts
        "font-stack": "Outfit, -apple-system, BlinkMacSystemFont, sans-serif",
        "font-stack--monospace": "Fira Code, SFMono-Regular, Menlo, Consolas, monospace",
        "font-stack--headings": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif",
    },
    "source_repository": "https://github.com/ViCCo-Group/LAION-fMRI",
    "source_branch": "main",
    "source_directory": "docs/source/",
    "navigation_with_keys": True,
}

html_title = "LAION-fMRI | Documentation"
html_short_title = "LAION-fMRI"

html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_favicon = "_static/favicon.ico"
html_show_sourcelink = True
html_show_sphinx = False
htmlhelp_basename = "laion-fmri"

# -- Other output formats -------------------------------------------------

latex_elements = {}
latex_documents = [
    (master_doc, "laion-fmri.tex", "LAION-fMRI Documentation", "ViCCo-Group", "manual"),
]
man_pages = [
    (master_doc, "laion-fmri", "LAION-fMRI Documentation", [author], 1)
]
texinfo_documents = [
    (master_doc, "laion-fmri", "LAION-fMRI Documentation", author,
     "laion-fmri", "Open fMRI dataset from ViCCo-Group.", "Miscellaneous"),
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
}

suppress_warnings = ["config.cache"]
