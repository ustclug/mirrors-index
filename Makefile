OUTDIR := dist
STATIC_OUT := $(OUTDIR)/static
ESBUILD_FLAGS := --bundle --format=esm --target=es2020 --jsx=automatic --jsx-import-source=preact --minify
ESBUILD := env NODE_PATH=$(CURDIR)/vendor esbuild
PYTHON_FILES := gencontent.py genindex.py genmirrorz.py genservernews.py utils.py tests/render_fixture.py tests/test_example_tree.py tests/test_genindex.py tools/build_manifest.py tools/check_bundle_size.py tools/create_example_tree.py
FRONTEND_FILES := playwright.config.ts frontend/*.ts frontend/*.tsx tests/e2e/*.ts static/css/style.css

.PHONY: build dev example typecheck format lint test install clean

build: clean typecheck
	mkdir -p $(STATIC_OUT)/js $(STATIC_OUT)/css $(OUTDIR)/status
	$(ESBUILD) frontend/index.tsx frontend/status.tsx $(ESBUILD_FLAGS) --outdir=$(STATIC_OUT)/js --entry-names=[name]-[hash] --metafile=$(OUTDIR)/esbuild-meta.json
	cp -a static/fonts $(STATIC_OUT)/
	cp -a static/img $(STATIC_OUT)/
	cp -a static/css/fonts.css static/css/style.css $(STATIC_OUT)/css/
	python3 tools/build_manifest.py

dev: clean typecheck
	mkdir -p $(STATIC_OUT)/js $(STATIC_OUT)/css $(OUTDIR)/status
	cp -a static/fonts $(STATIC_OUT)/
	cp -a static/img $(STATIC_OUT)/
	cp -a static/css/fonts.css static/css/style.css $(STATIC_OUT)/css/
	$(ESBUILD) frontend/index.tsx frontend/status.tsx --bundle --outdir=$(STATIC_OUT)/js --format=esm --target=es2020 --jsx=automatic --jsx-import-source=preact --sourcemap --metafile=$(OUTDIR)/esbuild-meta.json
	python3 tools/build_manifest.py
	$(ESBUILD) frontend/index.tsx frontend/status.tsx --bundle --outdir=$(STATIC_OUT)/js --format=esm --target=es2020 --jsx=automatic --jsx-import-source=preact --sourcemap --watch

example:
	python3 tools/create_example_tree.py

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

install: build
	test -n "$(WEBROOT)"
	install -d "$(WEBROOT)/static" "$(WEBROOT)/status"
	cp -a $(STATIC_OUT)/. "$(WEBROOT)/static/"
	install -m 0644 $(OUTDIR)/status/index.html "$(WEBROOT)/status/.index.html.new"
	mv "$(WEBROOT)/status/.index.html.new" "$(WEBROOT)/status/index.html"

clean:
	rm -rf $(OUTDIR)
