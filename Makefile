OUTDIR := dist
STATIC_OUT := $(OUTDIR)/static
ESBUILD_ENTRIES := frontend/index.tsx frontend/status.tsx static/css/style.css static/css/status.css
ESBUILD_FLAGS := --bundle --format=esm --target=es2020 --jsx=automatic --jsx-import-source=preact --alias:preact=$(CURDIR)/vendor/preact '--external:/static/fonts/*'
ESBUILD := env NODE_PATH=$(CURDIR)/vendor esbuild
PYTHON_FILES := gencontent.py genindex.py genmirrorz.py genservernews.py utils.py tests/render_fixture.py tests/test_example_tree.py tests/test_genindex.py tests/test_genmirrorz.py tools/build_manifest.py tools/check_bundle_size.py tools/create_example_tree.py
FRONTEND_FILES := playwright.config.ts frontend/*.ts frontend/*.tsx tests/e2e/*.ts static/css/*.css

.PHONY: build dev example typecheck format lint test install clean

build: clean typecheck
	mkdir -p $(STATIC_OUT)/js $(STATIC_OUT)/css $(OUTDIR)/status
	$(ESBUILD) $(ESBUILD_ENTRIES) $(ESBUILD_FLAGS) --minify --outdir=$(STATIC_OUT) --entry-names=[ext]/[name]-[hash] --metafile=$(OUTDIR)/esbuild-meta.json
	cp -a static/fonts $(STATIC_OUT)/
	cp -a static/img $(STATIC_OUT)/
	python3 tools/build_manifest.py

dev: clean typecheck
	mkdir -p $(STATIC_OUT)/js $(STATIC_OUT)/css $(OUTDIR)/status
	cp -a static/fonts $(STATIC_OUT)/
	cp -a static/img $(STATIC_OUT)/
	$(ESBUILD) $(ESBUILD_ENTRIES) $(ESBUILD_FLAGS) --outdir=$(STATIC_OUT) --entry-names=[ext]/[name] --sourcemap --metafile=$(OUTDIR)/esbuild-meta.json
	python3 tools/build_manifest.py
	$(ESBUILD) $(ESBUILD_ENTRIES) $(ESBUILD_FLAGS) --outdir=$(STATIC_OUT) --entry-names=[ext]/[name] --sourcemap --watch

example:
	python3 tools/create_example_tree.py --status-output $(OUTDIR)/status/json

typecheck:
	tsc -p tsconfig.json --noEmit

format:
	ruff format $(PYTHON_FILES)
	prettier --write $(FRONTEND_FILES)

lint:
	ruff format --check $(PYTHON_FILES)
	ruff check $(PYTHON_FILES)
	prettier --check $(FRONTEND_FILES)

test: build lint
	python3 tools/check_bundle_size.py
	python3 -m unittest discover -s tests -p 'test_*.py'
	python3 tests/render_fixture.py
	pnpm exec playwright test

install:
	test -n "$(WEBROOT)"
	install -d "$(WEBROOT)/static" "$(WEBROOT)/status"
	cp -a $(STATIC_OUT)/. "$(WEBROOT)/static/"
	install -m 0644 $(OUTDIR)/index.html "$(WEBROOT)/.index.html.new"
	mv "$(WEBROOT)/.index.html.new" "$(WEBROOT)/index.html"
	install -m 0644 $(OUTDIR)/status/index.html "$(WEBROOT)/status/.index.html.new"
	mv "$(WEBROOT)/status/.index.html.new" "$(WEBROOT)/status/index.html"

clean:
	rm -rf $(OUTDIR)
