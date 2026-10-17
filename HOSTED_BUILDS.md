# Real hosted browser builds

The `Compile Aether browser` workflow runs the pinned Helium preparation,
Aether patch application, GN generation and `autoninja chrome chromedriver`.
A successful source-validation workflow is separate and does not satisfy this
build. Failed preparation or linking leaves the build red.

## Configuration and resource reductions

* Windows: `windows-2025-vs2026`, C:/aether on NTFS with directory compression.
* Linux: `ubuntu-24.04`, build in runner temporary storage.
* Release component build, no debug symbols, no PGO or ThinLTO, two compiler jobs.
* Browser and ChromeDriver targets only; installers are deferred until a browser
  works. Component DLL/shared libraries are included in runtime archives.
* Remove listed unused image SDKs/languages; preserve the compiler/SDK and build
  tools. Record actual bytes freed rather than assuming advertised disk sizes.
* Source archives already omit Git history and many nonessential/test files.
  Inspection: imputnet/chromium-tarballs `a74ff1b1c46185744eb73eb69e7a9b587261797c`,
  scripts/prepare.py and scripts/package.py. They retain build metadata and tools.
* Disable local sccache for the low-resource configuration to avoid duplicating
  object files on an ephemeral disk. Incremental developer builds retain out/.
* Archive runtime files, excluding obj/, gen/ and PDBs. This reduces artifact size,
  not peak compiler storage. Component builds also do not reduce source size.

No sandbox/site-isolation or foreground web behavior changes are made for this
configuration. This is an experimental build configuration, not an optimized
release or an asserted performance improvement.

## Evidence

Each job records before/after cleanup disk and physical RAM, CPU count, OS image,
compiler/SDK versions, resource samples every 30 seconds, the streamed build log,
exit code, elapsed time, args.gn and available Ninja metadata. These upload as
`aether-build-evidence-<platform>-<run id>`, including failed attempts. Runtime
artifacts are separate and their smoke-test result must be checked on the run.

## Larger and persistent alternatives

GitHub documents standard public Windows/Linux x64 runners as 4 vCPU, 16 GB RAM
and 14 GB guaranteed SSD space; measured free space after image cleanup can be
larger. This guarantee is not evidence of an actual build failure.

GitHub larger runners offer 8 vCPU/32 GB/300 GB SSD and 16 vCPU/64 GB/600 GB SSD,
among other sizes. They require an organization on GitHub Team or Enterprise
Cloud, billing and an enabled spending budget, and incur charges for public
repositories too. `atlasru/aether` is owned by a personal account. The connected
account's organization listing returned empty on 2026-10-17. No eligible larger
runner has been provisioned or verified available. Merely inventing a runs-on
label does not allocate a machine. The workflow accepts an existing hosted
larger-runner label for manual dispatch when such infrastructure is configured.

A persistent Windows VM with VS 2026, the pinned SDK and 300+ GB storage can run
scripts/build.py directly and retain source/output between attempts. A managed
Windows build VM or an organization larger runner needs account access and a
paid capacity allocation. No external VM, payment or remote compiler service has
been configured or claimed tested. A 16-vCPU/64-GB/600-GB hosted runner is a
capacity candidate, not a proven minimum. A clean executable build and runtime
smoke tests remain required on whichever infrastructure is used.

References checked 2026-10-17:

* https://docs.github.com/en/actions/reference/runners/github-hosted-runners
* https://docs.github.com/en/actions/reference/runners/larger-runners
* https://docs.github.com/en/actions/concepts/runners/larger-runners
* https://github.com/actions/runner-images/blob/main/images/windows/Windows2025-VS2026-Readme.md
* https://chromium.googlesource.com/chromium/src/+/5869fe313571d75152b77813cf0a4ee26a4e6df0/docs/windows_build_instructions.md
* https://chromium.googlesource.com/chromium/src/+/5869fe313571d75152b77813cf0a4ee26a4e6df0/docs/linux/build_instructions.md
