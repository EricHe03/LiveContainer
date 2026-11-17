# ExtensionFix build and test record

Date: 17 November 2026 (Hong Kong).

- Source commit: `26e00b30a2a48704f9f87bd16fa710cfd4e4b654`.
- [Successful GitHub Actions run](https://github.com/EricHe03/LiveContainer/actions/runs/44050086015).
- Toolchain: Xcode 27.2, iPhoneOS 27.2 SDK, arm64 Release archives.
- [IPA artifact (ZIP)](https://github.com/EricHe03/LiveContainer/actions/runs/44050086015/artifacts/14314490943).
- [Build evidence artifact](https://github.com/EricHe03/LiveContainer/actions/runs/44050086015/artifacts/14312869977).

The IPA artifact contains `LiveContainer+SideStore-ExtensionFix.ipa` and
`SHA256SUMS.txt`. Unzip it before passing the IPA to your sideloading tool.

SHA-256 of the **IPA**, distinct from the enclosing Actions artifact ZIP:

```text
fd96d6b0d4a5bb5d72f8e2185c15c83b65534ce1457196bc298ea2ff9dabd138
```

## Observed results

| Check | Result | Evidence / scope |
| --- | --- | --- |
| Pinned source fetch and patch application | PASS | Actions preparation step; exact source/patch hashes in provenance JSON. |
| Duplicate patch detection | PASS | Local repeat application returned `already-applied` for both PRs and the Foundation import. |
| Production SideSign discovery: both directories | PASS | `appBundleLoadsExtensionsFromPlugInsAndExtensionsDirectories`; 0.011 seconds. |
| Production SideSign discovery: Extensions only | PASS | `appBundleLoadsExtensionsWhenOnlyExtensionsDirectoryExists`; 0.009 seconds. |
| Filtered Swift test suite | PASS | Log: 2 tests in 1 suite passed. |
| Fixed LC-compatible SideStore archive / fakesign / IPA | PASS | `make build fakesign ipa`. |
| LiveContainer Release archive | PASS | Xcode archive step. |
| Upstream LC+SS embedding process | PASS | Source-built SideStore converted to SideStoreApp.framework by `.github/build_github.sh`. |
| ZIP integrity / single top-level app | PASS | Final validator found only `Payload/LiveContainer.app`. |
| Embedded SideStore, support framework and widget | PASS | Required bundle files present and non-empty. |
| SideStore Mach-O conversion | PASS | Thin arm64 MH_DYLIB. |
| LC / SideStore / widget identifiers and SideStore data UUID | PASS | Original integration identities retained. |
| Refresh URL schemes and App Intents metadata | PASS | Final IPA structure checked. |
| Embedded binary signatures and app-group entitlements | PASS | Signature presence checked for LC, SideStore and widget; LC/widget retain the SideStore app group. This does not validate Apple-issued provisioning or device acceptance. |
| Official UTM 5.0.8 input structure | PASS | Original release downloaded and its release SHA-256 verified; helper confirmed under Extensions/. |
| Live Apple portal App ID / provisioning transaction | NOT RUN | No Apple credentials or certificates were supplied or used. |
| UTM 5.0.8 installation on iOS 27 | NOT RUN | No connected iOS test device. |
| iOSHelper snapshot / disk functionality | NOT RUN | Requires a successful real installation and UTM runtime test. |
| Real device background refresh / in-place data migration | NOT RUN | Requires an existing LC+SS device installation. |

## Official UTM input inspection

[UTM v5.0.8 release](https://github.com/utmapp/UTM/releases/tag/v5.0.8), `UTM.ipa`:

```text
SHA-256: 4875a1ec869278fb173b37467388ea627bfa6d95f1d64501bc41bb86dd7d53b2
Main bundle ID: com.utmapp.UTM
Helper path: Payload/UTM.app/Extensions/iOSHelper.appex
Helper bundle ID: com.utmapp.UTM.iOSHelper
Helper executable: iOSHelper
Helper package type: XPC!
Extension point: com.utmapp.UTM.qemu-helper
```

This inspection did not modify UTM or delete its helper. The expected
post-signing helper ID under the example team remains
`com.utmapp.UTM.TS8S4YF38T.iOSHelper`; that actual on-device signing/install result
has not been observed. Build success must not be read as a confirmed UTM fix.

The earlier run failed because the upstream SideSign test file omitted
`import Foundation`. The supplemental test-only import in the successful source
commit resolves that compile error without changing production signing policy.
