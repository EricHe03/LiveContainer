#!/usr/bin/env python3
"""Prepare pinned, LC-compatible sources; fail on patch drift instead of guessing."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent


def git(root, *args, check=True):
    result = subprocess.run(["git", "-C", str(root), *args],
                            text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stdout}{result.stderr}")
    return result


def checkout(repository, revision, destination):
    if destination.exists():
        raise RuntimeError(f"Refusing to overwrite {destination}")
    destination.mkdir(parents=True)
    git(destination, "init")
    git(destination, "remote", "add", "origin", f"https://github.com/{repository}.git")
    git(destination, "fetch", "--depth", "1", "origin", revision)
    git(destination, "checkout", "--detach", "FETCH_HEAD")
    actual = git(destination, "rev-parse", "HEAD").stdout.strip()
    if actual != revision:
        raise RuntimeError(f"Source revision mismatch: {actual} != {revision}")


def apply_patch(root, patch):
    if git(root, "apply", "--reverse", "--check", str(patch), check=False).returncode == 0:
        return "already-applied"
    git(root, "apply", "--check", str(patch))
    git(root, "apply", str(patch))
    return "applied"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    config = json.loads((HERE / "sources.json").read_text())
    ss = args.destination.resolve()
    checkout(config["sidestore"]["repository"], config["sidestore"]["revision"], ss)
    git(ss, "submodule", "update", "--init", "--recursive", "--depth", "1")
    sign = ss / "Dependencies/SideSign"
    git(sign, "fetch", "--depth", "1", "origin", config["sidesign"]["revision"])
    git(sign, "checkout", "--detach", config["sidesign"]["revision"])
    results = []
    for item in config["patches"]:
        patch = HERE / "patches" / item["file"]
        root = ss if item["target"] == "sidestore" else sign
        status = apply_patch(root, patch)
        results.append({**item, "status": status,
                        "sha256": hashlib.sha256(patch.read_bytes()).hexdigest()})
        print(f"{item['file']}: {status}", flush=True)
    report = {"sources": config, "patches": results,
              "device_installation_test": "NOT RUN",
              "apple_portal_provisioning_test": "NOT RUN"}
    (ss.parent / "extension-fix-provenance.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
