# Vendored Preact

- Upstream: <https://github.com/preactjs/preact>
- Package: `preact@10.29.8`
- License: MIT (see `LICENSE`)
- npm tarball: <https://registry.npmjs.org/preact/-/preact-10.29.8.tgz>
- npm integrity: `sha512-ej2aVZ+vZ8WO7tvlQWRM9N63A0KzF9q4mWJfDUHgYaIofWY9hu74QdnQrjoPMmZi2/nZ5gN0bJCQF49xQqx09Q==`

The directory is an unmodified copy of the published npm package. It contains
no installed dependencies and is resolved through TypeScript `paths` and
esbuild's `NODE_PATH`, so production builds do not consult a package registry.

To update it, download and inspect the new upstream package, verify its npm
integrity and license, replace this directory with the unpacked package, update
the version and integrity above, then run `make test` and review the production
bundle diff and gzip sizes.
