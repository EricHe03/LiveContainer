#!/usr/bin/env python3
"""Check LC+SS packaging invariants. This cannot validate a device installation."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import plistlib
import struct
import subprocess
import tempfile
import zipfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(ipa):
    with zipfile.ZipFile(ipa) as archive:
        require(archive.testzip() is None, "Corrupt ZIP member")
        names = set(archive.namelist())
        apps = {PurePosixPath(n).parts[1] for n in names
                if n.startswith("Payload/") and len(PurePosixPath(n).parts) > 1
                and PurePosixPath(n).parts[1].endswith(".app")}
        require(apps == {"LiveContainer.app"}, f"Unexpected top-level apps: {apps}")
        base = "Payload/LiveContainer.app/"
        guest = base + "Frameworks/SideStoreApp.framework/"
        widget = base + "PlugIns/LiveWidgetExtension.appex/"
        required = [base + "Info.plist", base + "LiveContainer",
                    base + "Frameworks/SideStoreSupport.framework/SideStoreSupport",
                    guest + "Info.plist", guest + "SideStore", guest + "LCAppInfo.plist",
                    widget + "Info.plist", widget + "LiveWidgetExtension",
                    base + "Metadata.appintents/extract.actionsdata"]
        for name in required:
            require(name in names and archive.getinfo(name).file_size > 0, f"Missing {name}")
        info = plistlib.loads(archive.read(base + "Info.plist"))
        require(info["CFBundleIdentifier"] == "com.kdt.livecontainer", "Changed LC identity")
        require("group.com.SideStore.SideStore" in info.get("ALTAppGroups", []), "Missing SS group")
        schemes = {s for item in info.get("CFBundleURLTypes", [])
                   for s in item.get("CFBundleURLSchemes", [])}
        require({"sidestore", "sidestore-com.kdt.livecontainer"} <= schemes, "Missing refresh URLs")
        guest_info = plistlib.loads(archive.read(guest + "Info.plist"))
        require(guest_info["CFBundleIdentifier"] == "com.SideStore.SideStore", "Changed SS identity")
        lc_info = plistlib.loads(archive.read(guest + "LCAppInfo.plist"))
        require(lc_info["LCDataUUID"] == "752B6522-37A4-404B-B0C6-8A37556C9F72", "Changed SS data UUID")
        require(lc_info.get("dontSign") is True, "Changed LC guest signing mode")
        widget_info = plistlib.loads(archive.read(widget + "Info.plist"))
        require(widget_info["CFBundleIdentifier"] == "com.kdt.livecontainer.LiveWidget", "Changed widget ID")
        binary = archive.read(guest + "SideStore")
        require(binary[:4] == b"\xcf\xfa\xed\xfe", "Expected thin arm64 Mach-O after dylibify")
        require(struct.unpack_from("<I", binary, 12)[0] == 6, "SideStore was not converted to MH_DYLIB")
        # Inspect the ad hoc embedded signatures, not an Apple-issued device signature.
        signatures = {}
        with tempfile.TemporaryDirectory() as tmp:
            for label, member in {"sidestore": guest + "SideStore",
                                  "widget": widget + "LiveWidgetExtension",
                                  "livecontainer": base + "LiveContainer"}.items():
                target = Path(tmp) / label
                target.write_bytes(archive.read(member))
                result = subprocess.run(["codesign", "-d", str(target)], capture_output=True, text=True)
                require(result.returncode == 0, f"Missing embedded signature: {label}: {result.stderr}")
                signatures[label] = "embedded signature present (not device provisioning validation)"
                if label in ("widget", "livecontainer"):
                    entitlements = subprocess.run(["ldid", "-e", str(target)], check=True,
                                                 capture_output=True).stdout
                    entitlements = plistlib.loads(entitlements)
                    require("group.com.SideStore.SideStore" in entitlements.get("com.apple.security.application-groups", []),
                            f"Missing signing app group: {label}")
        return {"ipa": ipa.name, "sha256": hashlib.sha256(ipa.read_bytes()).hexdigest(),
                "top_level_apps": sorted(apps), "integration_checks": "PASS",
                "embedded_signatures": signatures,
                "device_installation_test": "NOT RUN",
                "utm_5_0_8_installation_and_helper_test": "NOT RUN"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ipa", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = validate(args.ipa)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
