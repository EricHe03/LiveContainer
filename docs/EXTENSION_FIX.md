# LiveContainer + SideStore ExtensionFix

This branch builds one integrated LC+SS IPA from the existing LiveContainer
packaging process. It preserves `Extensions/iOSHelper.appex` in UTM; no UTM files
are removed or disabled. It does not add a separately installed SideStore app.

## Patch record (17 November 2026)

Both proposed upstream fixes were open and unmerged when inspected:

| Component | Source | Patch |
| --- | --- | --- |
| LiveContainer | `b7cfda60c39933a94d616f2a358ac2e48fd4e5cd` | Allow the existing `.github/build_github.sh` to embed a locally built SideStore IPA; fail fast; correct signature-cleanup path. |
| LC-compatible SideStore | `LiveContainer/SideStore`, `LiveContainerSupport`, `044bd72ad4eb270c3900bd04dc6f508d0ac474db` | [SideStore PR #1737](https://github.com/SideStore/SideStore/pull/1737), revision `0e38842215451a472a24a8ca5774c2b993823b34`. |
| SideSign | `SideStore/SideSign`, `752d1ef602aa792a432ffa1e71646dc1ecf7363c` | [SideSign PR #10](https://github.com/SideStore/SideSign/pull/10), revision `8e8016f37de44cfec4acbe68f084d6a78cdb96eb`. |

The two numbered patch files are snapshots of those PR diffs, including their
regression tests. An additional test-only patch imports Foundation explicitly:
the first Actions build exposed missing FileManager/URL/UUID symbols in the
upstream test file. This supplemental patch does not modify production signing.
No third-party binary or extfix release is embedded. Existing SideStore and
SideSign code remains responsible for App ID registration, profile acquisition,
entitlement filtering and CodeSignKit signing. Detecting the extension makes it
participate in those existing operations. There is no main-profile workaround.

`loadExtensions()` now scans both `PlugIns/` and `Extensions/`. A missing first
directory does not stop the second scan; `.appex` matching is case insensitive.
The SideStore patch updates extension inspector views and SC_Info handling.
The existing extension collection also feeds extension prompts, App ID counts,
verification, provisioning and Bundle ID preparation.

For the supplied example, the expected identifiers after personal signing are:

| Bundle | Expected Bundle ID |
| --- | --- |
| UTM | `com.utmapp.UTM.TS8S4YF38T` |
| iOSHelper | `com.utmapp.UTM.TS8S4YF38T.iOSHelper` |

## Build and download

Open **Actions → LC + SideStore ExtensionFix** in this fork. A push to
`sidestore-extension-fix` builds automatically. For a manual rebuild, open an
existing run and choose **Re-run all jobs**. `workflow_dispatch` is also declared
for use if the workflow is later included on the fork's default branch; GitHub
requires that before offering manual dispatch. If GitHub disabled Actions when the
repository was forked, first enable workflows in the Actions tab.

The workflow uses GitHub's `xcode-27` hosted image with Xcode 27.2. It:

1. Checks out LC and its submodules.
2. Fetches the exact SideStore/SideSign revisions in `sources.json`.
3. Applies the two PR snapshots and the test-only Foundation import. An already-applied patch is skipped; a patch
   that neither applies nor reverses cleanly stops the build for review.
4. Runs the actual SideSign ExtensionKit discovery tests using `swift test`.
5. Runs SideStore's `make build fakesign ipa`.
6. Archives LC using its upstream Release settings, then invokes its existing
   packaging script with `SIDESTORE_IPA_PATH` pointing to the fixed IPA.
7. Checks the final integration structure, data UUID, refresh URLs, MH_DYLIB
   conversion, embedded signatures and main/widget app-group entitlements.
8. Uploads **LiveContainer+SideStore-ExtensionFix.ipa** and SHA256SUMS.txt.
   A second artifact contains test/build logs and provenance/validation JSON.

Download and unzip the IPA artifact. The resulting IPA is ad hoc signed for
distribution to a sideloading tool; that tool must sign it for your device and
Apple team. No Apple account, certificate, pairing file or signing secret is
required by this GitHub workflow. Artifact retention is 90 days; rebuild to
produce a fresh copy after expiry.

## Upgrade an existing LC+SS installation

1. Export or back up important LC guest app data using your existing LC backup
   method before upgrading. Do not delete LC or its data as part of the upgrade.
2. Install this IPA **over the existing LC+SS app**, using the same sideloading
   method, Apple team and effective LC Bundle ID used for the current install.
   Preserve the current app groups. If your installer offers a replacement/update
   option, select the existing LC installation. Do not choose a new/random ID.
3. Open LC and confirm the embedded SideStore and existing guest containers load.
   The LC Bundle ID, SideStore guest Bundle ID, fixed LCDataUUID, URL schemes and
   existing storage implementation are retained by this branch. Data migration
   on a real existing installation has not been tested.
4. Import the original UTM 5.0.8 IPA **inside embedded SideStore**. When prompted,
   keep iOSHelper and select normal per-extension provisioning. Do not select
   Remove All or Use Main Profile. No modified/stripped UTM IPA is required.
5. After installation, check UTM launches, snapshot/disk operations use iOSHelper,
   and refresh both LC+SS and UTM. Keep existing backups until these checks pass.

The combined installer remains one top-level app and does not introduce another
LC/SS active app slot. UTM installed separately still consumes its ordinary app
slot. Its helper can require an additional **App ID registration**, which is a
separate Apple free-account limit. This patch cannot bypass Apple's account
limits. Running UTM as an LC guest has different extension/runtime constraints
and has not been validated here.

## Validation status and limits

Local preparation verified both patches apply cleanly to the pinned sources and
can be detected as already applied. Script syntax and workflow configuration
were checked on Linux. This environment has no Xcode or connected iOS device.
Actual macOS compilation and discovery test results must be read from the
corresponding Actions run; the workflow fails if those steps fail.

Source review confirmed that FetchProvisioningProfilesOperation creates the
parent-prefixed extension App ID, ResignAppOperation prepares each discovered
extension's Info.plist, and AppBundleSigner embeds matching profiles and selects
extension entitlements before recursively signing. This is a code-path review,
not a successful Apple portal transaction or device signature acceptance test.

**UTM 5.0.8 installation on iOS 27, iOSHelper functionality, background refresh,
and an in-place upgrade preserving real user data have NOT been tested.** A
successful build/discovery test alone does not establish any of those results.
Record the device model, iOS version, Actions commit, installation result,
rewritten helper ID, snapshot/disk result and refresh result when testing.

## Sync upstream and rebuild

Keep this branch separate from upstream `main`. To incorporate LC changes:

```sh
git remote add upstream https://github.com/LiveContainer/LiveContainer.git # once
git fetch upstream
git switch sidestore-extension-fix
git merge upstream/main
# Resolve any packaging/workflow conflicts, preserving SIDESTORE_IPA_PATH.
git push origin sidestore-extension-fix
```

For SideStore updates, inspect the latest **LiveContainerSupport** branch in
LiveContainer/SideStore first, retaining its LC-specific changes. Update the
SideStore and compatible SideSign commit SHAs in
`.github/extension-fix/sources.json`, then run the build. Subdependencies use
their upstream submodule commits and committed Package.resolved files.

Before changing pins, check whether PR #1737 / #10 or equivalent changes have
landed in the selected sources. Exact already-applied diffs are automatically
skipped. If equivalent upstream code differs and the patch check fails, inspect
the actual implementation and tests, then remove only the superseded entry
from `patches` in sources.json. Do not force a duplicate patch through.

Push the reviewed pin/patch changes to rebuild, inspect the uploaded evidence,
then repeat the device test above. The workflow does not silently follow moving
nightly releases, auto-merge upstream changes, publish releases or submit PRs
to upstream repositories.
