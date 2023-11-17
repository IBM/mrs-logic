PACKAGE:= mrs_logic
DOCS_SRC:= docs_src
DOCS_TGT:= docs

.PHONY: all
all:
	@echo 'Usage: make <target>'
	@echo
	@echo '  check         Run testsuite'
	@echo '  clean         Remove generated files'
	@echo '  docs          Build docs in ${DOCS_SRC}'
	@echo '  docs-publish  Copy docs from ${DOCS_SRC} to ${DOCS_TGT}'
	@echo '  install       Install package'
	@echo '  install-deps  Install doc-build and testsuite dependencies'
	@echo

.PHONY: check
check:
	-killall ukb_wsd
	pytest

.PHONY: clean
clean: docs-clean
	-rm -rf ./build ./${PACKAGE}.egg-info

.PHONY: docs
docs:
	${MAKE} -C ./${DOCS_SRC} html
	@echo 'Index: file://${PWD}/docs_src/_build/html/index.html'

.PHONY: docs-clean
docs-clean:
	${MAKE} -C ./${DOCS_SRC} clean
	-rm -rf ./${DOCS_SRC}/generated

.PHONY: docs-publish
docs-publish: docs-clean docs
	${MAKE} -C ./${DOCS_SRC} publish

.PHONY: install
install:
	pip install -e .

.PHONY: install-deps
install-deps:
	pip install -e '.[docs]'
	pip install -e '.[tests]'
