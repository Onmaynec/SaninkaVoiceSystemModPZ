from __future__ import annotations

import hashlib
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = os.environ.get("TAG", "v0.1.0-alpha")
DIST = ROOT / "dist"
INSTALL = DIST / f"SaninkaVoiceSystem-{TAG}.zip"
SOURCE = DIST / f"SaninkaVoiceSystem-Source-{TAG}.zip"
CHECKSUMS = DIST / "SHA256SUMS.txt"


def add_tree(archive: zipfile.ZipFile, path: Path) -> None:
    if path.is_file():
        archive.write(path, path.relative_to(ROOT).as_posix())
        return
    for file in sorted(path.rglob("*")):
        if not file.is_file():
            continue
        relative = file.relative_to(ROOT)
        if any(part in {".git", ".release", "bootstrap", "__pycache__", "dist"} for part in relative.parts):
            continue
        archive.write(file, relative.as_posix())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    DIST.mkdir(exist_ok=True)
    mod_root = ROOT / "Contents"
    if not mod_root.is_dir():
        raise SystemExit("Contents directory is missing")

    with zipfile.ZipFile(INSTALL, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        add_tree(archive, mod_root)

    source_paths = [
        ROOT / "Contents",
        ROOT / "docs",
        ROOT / "tools",
        ROOT / ".github" / "workflows" / "release.yml",
        ROOT / "README.md",
        ROOT / "RELEASE_NOTES.md",
        ROOT / "VERSION",
        ROOT / ".gitignore",
    ]
    with zipfile.ZipFile(SOURCE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in source_paths:
            if path.exists():
                add_tree(archive, path)

    entries = [f"{sha256(INSTALL)}  {INSTALL.name}", f"{sha256(SOURCE)}  {SOURCE.name}"]
    CHECKSUMS.write_text("\n".join(entries) + "\n", encoding="utf-8")

    for path in (INSTALL, SOURCE):
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:
                raise SystemExit(f"Corrupt archive entry: {bad}")

    print(INSTALL)
    print(SOURCE)
    print(CHECKSUMS)


if __name__ == "__main__":
    main()
