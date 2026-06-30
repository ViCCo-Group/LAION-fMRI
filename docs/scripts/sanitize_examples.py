"""Replace local-machine paths in the executed-gallery output.

Sphinx-gallery captures stdout from each example. Some scripts
(``plot_01_quickstart.py`` etc.) print local data-dir paths, so
the committed ``auto_examples/`` would otherwise embed the build
machine's filesystem layout. This script rewrites those paths to
generic placeholders so the rendered docs look the same on every
machine.

Run after the local rebuild:

    LAION_FMRI_BUILD_EXAMPLES=1 cd docs && uv run make html
    uv run python docs/scripts/sanitize_examples.py
"""

import os
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent.parent
SOURCE = DOCS_DIR / "source" / "auto_examples"
BUILD_HTML = DOCS_DIR / "build" / "html"
REPO_ROOT = DOCS_DIR.parent


def _build_replacements():
    """Assemble the path-replacement table.

    Order matters: longest / most specific paths first, so a more
    general match doesn't partially eat a more specific one.
    """
    replacements = []

    # If the local build pointed at a custom cached data dir via
    # ``LAION_FMRI_EXAMPLE_DATA_DIR`` (e.g. plot_01's cache
    # location), scrub that path too. Skipped if the env var
    # isn't set OR points at the build sandbox (already handled
    # by the next replacement).
    env_dir = os.environ.get("LAION_FMRI_EXAMPLE_DATA_DIR")
    if env_dir:
        env_abs = os.path.abspath(env_dir)
        sandbox_abs = os.path.abspath(
            DOCS_DIR / "build" / "_examples_data" / "laion_fmri_quickstart"
        )
        if env_abs != sandbox_abs:
            replacements.append((env_abs, "/path/to/laion-fmri-data"))

    # Build-managed sandbox path (used when LAION_FMRI_EXAMPLE_DATA_DIR
    # isn't set; see docs/source/conf.py).
    replacements.append(
        (
            os.path.abspath(
                DOCS_DIR / "build" / "_examples_data" / "laion_fmri_quickstart"
            ),
            "/path/to/laion-fmri-data",
        )
    )

    # Repo root → generic placeholder for any in-tree paths
    # (sphinx-gallery captures e.g. the gallery script path).
    replacements.append(
        (os.path.abspath(REPO_ROOT), "/path/to/laion-fmri")
    )

    # Home dir → ``$HOME`` placeholder. Last so longer matches
    # above take precedence on paths that live under ``~``.
    replacements.append((os.path.expanduser("~"), "$HOME"))

    return tuple(replacements)


_REPLACEMENTS = _build_replacements()


def sanitize(text):
    """Return ``text`` with every host-specific path replaced."""
    for src, dst in _REPLACEMENTS:
        text = text.replace(src, dst)
    return text


def _scrub(root, extensions):
    """Walk ``root`` and rewrite every file with a matching suffix."""
    if not root.is_dir():
        return 0
    n = 0
    for ext in extensions:
        for path in root.rglob(ext):
            text = path.read_text()
            new = sanitize(text)
            if new != text:
                path.write_text(new)
                rel = path.relative_to(DOCS_DIR.parent)
                print(f"sanitized {rel}")
                n += 1
    return n


def main():
    if not SOURCE.is_dir():
        raise SystemExit(
            f"{SOURCE} not found; run `make html` with "
            "LAION_FMRI_BUILD_EXAMPLES=1 first."
        )

    # Source gallery (RST/IPYNB committed) and the rendered HTML
    # under build/html (local browse copy). Both can leak host
    # paths through captured stdout / Out-blocks.
    n_changed = _scrub(SOURCE, ("*.rst", "*.ipynb", "*.html"))
    n_changed += _scrub(BUILD_HTML, ("*.html",))

    if n_changed == 0:
        print("nothing to sanitize (no host paths matched)")
    else:
        print(f"sanitized {n_changed} file(s)")


if __name__ == "__main__":
    main()
