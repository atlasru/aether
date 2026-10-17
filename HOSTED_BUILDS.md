# Real hosted browser builds

The `Compile Aether browser` workflow runs the pinned Helium preparation,
Aether patch application, GN generation and `autoninja chrome chromedriver`.
A successful source-validation workflow is separate and does not satisfy this
build. Failed preparation or linking leaves the build red.

## Configuration and resource reductions

* Windows: `windows-2025-vs2026`, a short aether directory on the measured
  C: or D: volume with most free space, with NTFS directory compression.
* Linux: `ubuntu-24.04`, build in runner temporary storage.
* Release component build, no debug symbols, no PGO or ThinLTO, four compiler jobs.
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

## Attempt 1 — Windows preparation failure (2026-10-17)

Run [39041366048](https://github.com/atlasru/aether/actions/runs/39041366048),
job 117421370226, source `2f7883f497a732b3d3d4b21a7f2e53dcece60793` failed after
1,512.609 seconds of actual preparation. Archives downloaded, unpacked and common
and Windows patches applied. Name substitution then failed in spawned Python
workers: `ModuleNotFoundError: name_substitution`. GN and the compiler had not
started. This is a build-driver import defect, not proof of an infrastructure
limit. The driver now preserves the upstream utility import path while preparing;
a regression exercises real spawn child interpreters on a small tool fixture.

Measured Windows image 20261007.264.1: 4 logical CPUs, 17,174,360,064 bytes physical
RAM, Visual Studio Enterprise 2026 18.10.12224.181. C: had 46,360,735,744 bytes free
after cleanup and 19,981,160,448 at failure. Crucially D: also existed, with
236,075,843,584 bytes free. Attempt 2 probes actual volumes and uses the one with
most free space. A blanket claim that standard Windows cannot fit Chromium would
be unsupported by these measurements. The initial SDK-list diagnostic contained
an escaped backspace; the raw-string fix is included for the retry.

Measured reports and error excerpt: [docs/builds/attempt-1-windows/](docs/builds/attempt-1-windows/).
The full streamed log/samples are in the run's build-evidence artifact. No browser
executable or runtime smoke result was produced by this failed Windows attempt.

## Attempt 2 — observed SDK mismatch

Run [39043691087](https://github.com/atlasru/aether/actions/runs/39043691087),
source `a034f6e15c1bbf4d33a5c6f0c1d1bc76f3c38b0d`, selected D:/aether and measured
236,075,773,952 free bytes. Early runner evidence confirms that SDK Include has
only `10.0.26100.0`. Pinned Chromium build/vs_toolchain.py and
build/toolchain/win/setup_toolchain.py both explicitly select `10.0.28000.0`.
This is a measured toolchain mismatch; no GN/compiler failure is invented for it.
The next requested Windows build supersedes the incompatible in-progress job.

Attempt 3 installs Microsoft SDK servicing release 10.0.28000.2526 (above the
2270 minimum), with vendor URL and SHA-256 pinned from Microsoft's winget
manifest, plus Authenticode verification. Installation logs, exit status and
required header/library/tool checks are retained. On run 39044290753 the installer
returned 0, the expected SHA-256 matched, Authenticode status was Valid with
Microsoft Corporation as signer, required files existed and dbghelp.dll reported
10.0.28000.2526. The SDK fix is verified on the actual runner; browser compilation
and runtime verification remain separate. New build requests supersede older builds per platform;
they do not cancel the other platform's independent attempt.

SDK installation evidence: [docs/builds/attempt-3-windows/](docs/builds/attempt-3-windows/).
Run 39044290753 (source `194b0c841026298f6eb81c47a32b765abfbb28bb`) continues
the full browser build after this successful installation. Its initial artifact
contains SDK installer logs; the final build-evidence artifact will contain the
actual compilation result. First Linux attempt 39041366048 remains independent.

## Attempt 3 — real C++ compilation, PCH failure

The Windows source preparation and Aether overlay completed (1,454 files).
GN succeeded: 35,610 targets from 5,000 files in 37,478 ms. The actual
`autoninja -C out/Default -j 4 chrome chromedriver` then ran the bundled Clang.
Siso completed 1,889 of 82,373 operations (1,857 local, 32 noexec), before
`base/precompile.cc` failed: missing 'export module' declaration in module
interface unit. This is a real compiler failure, not sparse patch validation.

The component configuration enabled precompiled headers by default; attempt 4
sets Chromium's supported `enable_precompiled_headers=false`. The normal
official configuration already disables PCH. No engine/security source changes
are made for this correction. Pinned declaration: build/config/pch.gni.

A second defect occurred while printing Siso's Unicode resource chart:
Python's Windows cp1252 stdout raised UnicodeEncodeError. UTF-8 is now explicit
for the hosted process and child Python environment, and a subprocess regression
forces cp1252 to exercise that failure mode. The streamed file receives each
line before console output. These new corrections await the next CI execution.

The last console sample still had 138,612,543,488 bytes free on D:. No RAM, disk
or hosted time-limit failure was demonstrated in this Windows attempt.
No browser executable was produced. Native result and exact failed target:
[docs/builds/attempt-3-windows/native-result.json](docs/builds/attempt-3-windows/native-result.json).
