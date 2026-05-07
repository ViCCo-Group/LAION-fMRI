# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =  # Removed "-W" to not treat warnings as errors
SPHINXBUILD   = uv run sphinx-build
SPHINXPROJ    = PackagingScientificPython
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile examples-rebuild

# Re-execute the example gallery and sanitize host paths from the
# captured output. Run this whenever an example script changes
# (or the bucket layout changes the prints), then commit
# ``docs/source/auto_examples/`` so deploy builds can render the
# pre-built gallery without re-executing.
#
# Single sphinx-build pass writes both the sanitizable gallery
# sources (under source/auto_examples) and the local HTML build;
# the sanitize step rewrites host paths in both, so the locally
# browseable HTML matches what readers see.
examples-rebuild:
	rm -rf "$(SOURCEDIR)/auto_examples" "$(BUILDDIR)"
	LAION_FMRI_BUILD_EXAMPLES=1 $(SPHINXBUILD) -M html \
		"$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	cd .. && uv run python docs/scripts/sanitize_examples.py

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
