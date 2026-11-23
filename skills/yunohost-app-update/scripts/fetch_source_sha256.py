#!/usr/bin/env python3
"""Download upstream release URL(s) in streaming chunks, compute SHA-256, and emit manifest.toml TOML."""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request

VALID_ARCHS = ("amd64", "arm64", "armhf", "i386")


def sha256_url(url: str, timeout: int = 120) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "yunohost-app-maintainer/1.0"})
    digest = hashlib.sha256()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        while True:
            chunk = resp.read(1024 * 64)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest().lower()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute SHA-256 checksums for YunoHost [resources.sources.<id>] entries."
    )
    parser.add_argument("--source-id", default="main", help="Source identifier (default: main)")
    parser.add_argument("--url", default="", help="Single architecture-independent source URL")
    parser.add_argument(
        "--arch",
        action="append",
        default=[],
        metavar="ARCH=URL",
        help="Architecture-specific URL, e.g. --arch amd64=https://... (repeatable)",
    )
    parser.add_argument("--timeout", type=int, default=120, help="HTTP timeout in seconds (default: 120)")
    args = parser.parse_args()

    if bool(args.url) == bool(args.arch):
        raise SystemExit("Provide exactly ONE of --url <URL> OR one or more --arch <arch>=<URL> arguments.")

    print(f"    [resources.sources.{args.source_id}]")
    if args.url:
        checksum = sha256_url(args.url, timeout=args.timeout)
        print(f'    url = "{args.url}"')
        print(f'    sha256 = "{checksum}"')
    else:
        for item in args.arch:
            if "=" not in item:
                raise SystemExit(f"Invalid --arch '{item}': expected ARCH=URL.")
            arch, url = item.split("=", 1)
            if arch not in VALID_ARCHS:
                raise SystemExit(f"Invalid architecture '{arch}': expected one of {VALID_ARCHS}.")
            checksum = sha256_url(url, timeout=args.timeout)
            print(f'    {arch}.url = "{url}"')
            print(f'    {arch}.sha256 = "{checksum}"')


if __name__ == "__main__":
    main()
