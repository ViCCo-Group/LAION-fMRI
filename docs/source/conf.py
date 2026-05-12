#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# LAION-fMRI documentation build configuration file

import os
import pathlib
import sys

sys.path.insert(0, os.path.abspath("../.."))


# -- Sphinx-gallery is opt-in -------------------------------------------
#
# Executing the example scripts on every build is brittle: it
# downloads ~GB of data, depends on AWS reachability, and can OOM
# on small CI hosts. We commit the executed-gallery output instead.
#
# To regenerate the committed gallery locally:
#
#     LAION_FMRI_BUILD_EXAMPLES=1 cd docs && uv run make html
#     uv run python docs/scripts/sanitize_examples.py
#     git add docs/source/auto_examples/
#
# Without the env var, sphinx-gallery is not loaded; sphinx renders
# whatever rst lives under ``docs/source/auto_examples/``.

_BUILD_EXAMPLES = bool(os.environ.get("LAION_FMRI_BUILD_EXAMPLES"))


# -- General configuration ------------------------------------------------
#
# sphinx-gallery is loaded unconditionally so the ``image-sg``
# directive in committed gallery RST is always recognized when CI
# runs ``make html``. Whether the example scripts themselves get
# *executed* is gated by ``plot_gallery`` below: only set when
# LAION_FMRI_BUILD_EXAMPLES is in the environment.

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
    # SEO: canonical URLs + sitemap.xml + Open Graph / Twitter cards
    "sphinx_sitemap",
    "sphinxext.opengraph",
]

if _BUILD_EXAMPLES:
    # Pre-write license markers under a build-controlled data dir so
    # the example scripts run non-interactively. End users running
    # the example scripts directly still see the real prompts the
    # first time.
    _BUILD_DATA_ROOT = pathlib.Path(
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "build")
        )
    )
    _EXAMPLE_DATA_DIR = (
        _BUILD_DATA_ROOT / "_examples_data" / "laion_fmri_quickstart"
    )
    (_EXAMPLE_DATA_DIR / ".laion_fmri").mkdir(
        parents=True, exist_ok=True,
    )
    (_EXAMPLE_DATA_DIR / ".laion_fmri" / "license_accepted").touch()
    (
        _EXAMPLE_DATA_DIR / ".laion_fmri" / "stimuli_terms_accepted"
    ).touch()
    os.environ["LAION_FMRI_EXAMPLE_DATA_DIR"] = str(_EXAMPLE_DATA_DIR)

from sphinx_gallery.sorting import FileNameSortKey  # noqa: E402

sphinx_gallery_conf = {
    "examples_dirs": ["../../examples"],
    "gallery_dirs": ["auto_examples"],
    "filename_pattern": r"plot_",
    # Execution gated by env var: True locally for a full rebuild,
    # False on CI so the committed gallery is consumed as-is.
    "plot_gallery": _BUILD_EXAMPLES,
    "remove_config_comments": True,
    "doc_module": ("laion_fmri",),
    # Render in plot_01, plot_02, ... order rather than the
    # default by-line-count.
    "within_subsection_order": FileNameSortKey,
    # Branded fallback for examples that don't render figures
    # (plot_02 prints license text, plot_03 prints discovery
    # output) -- avoids sphinx-gallery's stock pinwheel.
    "default_thumb_file": os.path.join(
        os.path.dirname(__file__),
        "_static",
        "laion_fmri_logo_mosaic.png",
    ),
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
copyright = "2026, Hebart Lab (hebartlab.com)"
author = "ViCCo-Group"

_version = "0.1.0"
version = _version
release = _version

language = "en"
exclude_patterns = []
pygments_style = "tango"
pygments_dark_style = "monokai"
# Two-mode build: pass ``-t dev`` (or ``make html-dev``) to render the
# in-progress TODO planning blocks and any content guarded by
# ``.. only:: dev``. The default build is the public-facing "live" view
# that hides both.
todo_include_todos = tags.has("dev")
if not tags.has("dev"):
    tags.add("live")


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
    # Funding acknowledgements — rendered in the bottom-of-page right slot
    # so they sit inline with the copyright line. The empty ``html`` is
    # intentional: each link is given a background-image via custom.css
    # (using a class), so paths stay relative to the CSS file and resolve
    # correctly regardless of page depth.
    "footer_icons": [
        {
            "name": "Funded by the European Research Council (European Union)",
            "url": "https://erc.europa.eu/",
            "html": "",
            "class": "funding-link funding-erc",
        },
        {
            "name": "Funded by the LOEWE programme (State of Hesse)",
            "url": "https://wissenschaft.hessen.de/forschen/landesprogramm-loewe",
            "html": "",
            "class": "funding-link funding-loewe",
        },
        {
            "name": "Funded by the Max Planck Society",
            "url": "https://www.mpg.de/en",
            "html": "",
            "class": "funding-link funding-mpg",
        },
    ],
}

html_title = "LAION-fMRI"
html_short_title = "LAION-fMRI"

html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_favicon = "_static/favicon.ico"
html_show_sourcelink = True
html_show_sphinx = False
htmlhelp_basename = "laion-fmri"

# Anything under html_extra_path is copied verbatim to the build root —
# we use it to ship robots.txt so search engines can discover sitemap.xml.
html_extra_path = ["_extra"]

# -- SEO ------------------------------------------------------------------
#
# Canonical site root. Trailing slash is required by sphinx-sitemap, and
# Sphinx's githubpages extension reuses it to emit per-page canonical
# <link rel="canonical"> tags.
html_baseurl = "https://laion-fmri.hebartlab.com/"

# sphinx-sitemap: write a sitemap.xml at the build root with absolute URLs.
sitemap_url_scheme = "{link}"

# Default <meta name="description"> applied site-wide. Per-page meta in
# rst files (`.. meta::`) overrides this.
html_meta = {
    "description": (
        "LAION-fMRI (LfMRI / LAION MRI dataset): a deeply-sampled 7T fMRI "
        "dataset of brain responses to 25,000+ natural images. Five subjects, "
        "165 sessions, single-trial GLMsingle betas, retinotopy, localizers, "
        "diffusion MRI. Used by the re:vision replication initiative."
    ),
    "keywords": (
        "LAION-fMRI, LAION fMRI, LfMRI, LAION MRI dataset, fMRI dataset, "
        "7T fMRI, visual neuroscience, GLMsingle, NSD, THINGS, "
        "revision initiative, re:vision, neuroimaging"
    ),
}

# sphinxext-opengraph: Open Graph + Twitter card tags on every page.
ogp_site_url = html_baseurl
ogp_site_name = "LAION-fMRI"
ogp_image = f"{html_baseurl}_static/laion_fmri_logo_mosaic.png"
ogp_image_alt = "LAION-fMRI — a 7T fMRI dataset of human vision"
ogp_description_length = 300
ogp_type = "website"
ogp_enable_meta_description = True
ogp_social_cards = {
    # The opengraph extension can auto-generate per-page social cards.
    # Disabled by default to keep builds cheap; flip to True locally to
    # render PNGs once and commit them.
    "enable": False,
}

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
