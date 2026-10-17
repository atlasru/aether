# Aether

A real Chromium/Helium browser project. Active implementation is on [dev](https://github.com/atlasru/aether/tree/dev).

**No Aether executable has been compiled. This is not a usable alpha.**

- [Source and build instructions](https://github.com/atlasru/aether/blob/dev/README.md)
- [Verified checks and limitations](https://github.com/atlasru/aether/blob/dev/VALIDATION.md)
- [Implementation status](https://github.com/atlasru/aether/blob/dev/ROADMAP.md)

The manual [self-hosted build workflow](https://github.com/atlasru/aether/actions/workflows/build.yml) defaults to `source_ref=dev`. It requires a prepared Windows x64 runner with Visual Studio/Windows SDK and a persistent `AETHER_WORK_DIR`. Linux builds are experimental. No untested binary is published as stable.

`main` contains the project entry point, license and build workflow. Browser source stays on `dev` until native validation. GPL-3.0; third-party licenses remain applicable.
