#!/usr/bin/env python3
"""Nucleus Deck: SteamOS-native companion using PartyDeck's Linux engine.

The original Nucleus Co-op WinForms/Win32 application is not run by this tool.
A locally installed, checksum-verified PartyDeck release provides the runtime.
GPL-3.0-or-later; see the repository LICENSE.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import webbrowser

PARTYDECK_API = "https://api.github.com/repos/partydeck/partydeck/releases/latest"
HANDLER_URL = "https://github.com/partydeck/partydeck/issues/190"
GUIDE_URL = "https://github.com/GiantDwarf288/splitscreenme-nucleus/blob/feature/steamos-native-deck-edition/steamdeck/README.md"
MAX_DOWNLOAD = 200 * 1024 * 1024
MAX_UNPACKED = 800 * 1024 * 1024


def data_root() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "nucleus-deck"


def is_steamos() -> bool:
    try:
        text = Path("/etc/os-release").read_text(encoding="utf-8").lower()
        return "id=steamos" in text or "id=\"steamos\"" in text
    except OSError:
        return False


def find_executable(folder: Path, filename: str) -> Path | None:
    if not folder.exists():
        return None
    paths = sorted(folder.rglob(filename), key=lambda p: (len(p.parts), str(p)))
    return next((p for p in paths if p.is_file() and os.access(p, os.X_OK)), None)


def choose_asset(release: dict) -> tuple[str, str, str]:
    """Require an official SteamOS x86_64 archive with its GitHub SHA256 digest."""
    for item in release.get("assets", []):
        name = item.get("name", "")
        url = item.get("browser_download_url", "")
        digest = item.get("digest") or ""
        if (name.endswith("-SteamOS-x86_64.tar.gz")
                and url.startswith("https://github.com/partydeck/partydeck/releases/download/")
                and digest.startswith("sha256:")
                and len(digest) == 71):
            hexdigest = digest[7:]
            if all(c in "0123456789abcdefABCDEF" for c in hexdigest):
                return name, url, hexdigest.lower()
    raise RuntimeError("No checksum-verified SteamOS x86_64 asset in the latest PartyDeck release.")


def request_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "NucleusDeck/0.1",
                                                "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res)


def download_verified(url: str, digest: str, target: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "NucleusDeck/0.1"})
    checksum = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(req, timeout=45) as res, target.open("wb") as dst:
        # A GitHub release redirects to GitHub's asset storage.
        if res.url.split("/")[0] != "https:":
            raise RuntimeError("Refusing a non-HTTPS download.")
        while True:
            chunk = res.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_DOWNLOAD:
                raise RuntimeError("Archive exceeds safe download limit.")
            dst.write(chunk)
            checksum.update(chunk)
    if checksum.hexdigest() != digest:
        raise RuntimeError("SHA256 verification failed; archive not installed.")


def extract_safe(archive: Path, destination: Path) -> None:
    """Never follow archived symlinks, hard links, absolute or traversal paths."""
    destination.mkdir(parents=True, exist_ok=False)
    unpacked = 0
    with tarfile.open(archive, mode="r:gz") as tar:
        for member in tar:
            name = PurePosixPath(member.name)
            if (name.is_absolute() or not name.parts or
                    any(p in ("", ".", "..") for p in name.parts)):
                raise RuntimeError(f"Unsafe archive path: {member.name}")
            target = destination.joinpath(*name.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise RuntimeError(f"Unsupported archive entry: {member.name}")
            unpacked += member.size
            if unpacked > MAX_UNPACKED:
                raise RuntimeError("Archive exceeds safe extracted size limit.")
            target.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as src, target.open("wb") as out:
                if src is None:
                    raise RuntimeError("Unable to read archive entry.")
                shutil.copyfileobj(src, out)
            target.chmod(0o755 if member.mode & 0o111 else 0o644)


def install_backend(root: Path) -> str:
    if platform.machine() not in ("x86_64", "AMD64"):
        raise RuntimeError("This edition currently supports x86_64 devices only.")
    print("Finding the latest official SteamOS PartyDeck release...")
    release = request_json(PARTYDECK_API)
    name, url, digest = choose_asset(release)
    print(f"Downloading {name}; expected SHA256 {digest}")
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nucleus-deck-", dir=root) as work:
        workdir = Path(work)
        archive = workdir / "backend.tar.gz"
        download_verified(url, digest, archive)
        staging = workdir / "unpacked"
        extract_safe(archive, staging)
        binary = find_executable(staging, "partydeck")
        if binary is None:
            raise RuntimeError("Archive contains no executable PartyDeck binary.")
        current = root / "partydeck"
        backup = root / "partydeck-backup"
        if backup.exists():
            shutil.rmtree(backup)
        if current.exists():
            current.rename(backup)
        try:
            staging.rename(current)
        except Exception:
            if backup.exists():
                backup.rename(current)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    return str(release.get("tag_name", "unknown release"))


def doctor(root: Path) -> tuple[str, bool]:
    checks = [
        ("Architecture x86_64", platform.machine() in ("x86_64", "AMD64")),
        ("SteamOS detected", is_steamos()),
        ("gamescope installed", shutil.which("gamescope") is not None),
        ("bubblewrap installed", shutil.which("bwrap") is not None),
        ("PartyDeck backend installed", find_executable(root / "partydeck", "partydeck") is not None),
    ]
    report = ["Nucleus Deck / SteamOS diagnostics", ""]
    for label, ok in checks:
        report.append(f"{'OK  ' if ok else 'CHECK'} {label}")
    report += ["", "kdialog (optional UI): " + ("present" if shutil.which("kdialog") else "missing"),
               "No Windows installation or .NET Framework needed.",
               "Windows-only games still use Proton through PartyDeck.",
               "SteamOS 3.7+ / KDE Plasma 6 required for PartyDeck automatic tiling."]
    return "\n".join(report), all(ok for label, ok in checks if label != "SteamOS detected")


def display(message: str, title: str = "Nucleus Deck") -> None:
    if shutil.which("kdialog") and os.environ.get("DISPLAY") or (shutil.which("kdialog") and os.environ.get("WAYLAND_DISPLAY")):
        subprocess.run(["kdialog", "--title", title, "--msgbox", message], check=False)
    else:
        print(message)


def gui(root: Path) -> None:
    if not shutil.which("kdialog"):
        print("KDE kdialog not found; use --doctor / --install-backend / --launch.")
        return
    while True:
        command = subprocess.run(
            ["kdialog", "--title", "Nucleus Deck (SteamOS)", "--menu",
             "Linux-native split-screen powered by PartyDeck",
             "launch", "Start split-screen launcher",
             "install", "Install/update SteamOS runtime",
             "doctor", "Check Steam Deck requirements",
             "handlers", "World at War Zombies handler instructions",
             "quit", "Close"],
            text=True, capture_output=True, check=False)
        if command.returncode or command.stdout.strip() == "quit":
            return
        action = command.stdout.strip()
        if action == "install":
            accepted = subprocess.run(
                ["kdialog", "--yesno",
                 "Download the official PartyDeck SteamOS release into your home folder?"],
                check=False)
            if accepted.returncode == 0:
                try:
                    version = install_backend(root)
                    display(f"Installed PartyDeck {version}.\nLaunch it, then import the World at War handler.")
                except Exception as exc:
                    display(f"Installation failed:\n{exc}", "Nucleus Deck error")
        elif action == "launch":
            binary = find_executable(root / "partydeck", "partydeck")
            if binary is None:
                display("Runtime not installed. Choose Install/update first.")
            else:
                os.execv(str(binary), [str(binary)])
        elif action == "doctor":
            display(doctor(root)[0], "Steam Deck diagnostics")
        elif action == "handlers":
            webbrowser.open(HANDLER_URL)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SteamOS-native Nucleus Deck companion (powered by PartyDeck)")
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--gui", action="store_true", help="Open KDE menu")
    choice.add_argument("--doctor", action="store_true", help="Check dependencies")
    choice.add_argument("--install-backend", action="store_true", help="Download verified Linux runtime")
    choice.add_argument("--launch", action="store_true", help="Run installed Linux runtime")
    choice.add_argument("--handler-guide", action="store_true", help="Open World at War handler page")
    args = parser.parse_args(argv)
    root = data_root()
    try:
        if args.doctor:
            report, ok = doctor(root)
            print(report)
            return 0 if ok else 1
        if args.install_backend:
            print("Installed", install_backend(root))
        elif args.launch:
            binary = find_executable(root / "partydeck", "partydeck")
            if binary is None:
                parser.error("PartyDeck is not installed. Run --install-backend first.")
            os.execv(str(binary), [str(binary)])
        elif args.handler_guide:
            print(HANDLER_URL)
            webbrowser.open(HANDLER_URL)
        else:
            gui(root)
        return 0
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"Nucleus Deck error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
