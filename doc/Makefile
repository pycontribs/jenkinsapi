SPHINXBUILD   ?= uv run sphinx-build
SOURCEDIR     = .
BUILDDIR      = html

.PHONY: all clean html

all: clean html

html:
	uv sync --group dev --group docs
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)"

clean:
	rm -rf ${BUILDDIR}/*

run:
	uv run python -m http.server --directory "${BUILDDIR}"
