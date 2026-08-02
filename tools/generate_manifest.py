from __future__ import annotations

import base64
import hashlib
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / ".release" / "package"
TAG = "v0.1.0-alpha"
EXPECTED_SHA256 = "450f34092bf695ba77fcea475baaab03d773832df36703c7eb64ef2c582757dd"
INSTALL_ZIP = ROOT / "dist" / f"SaninkaVoiceSystem-{TAG}.zip"
CHUNK_HASHES = {
    "part-000.b64": "aca6c01dd2a35242d6f6bd8ff14d9dc7bdc2a79389202730b3855c86fd9dbab2",
    "part-001.b64": "4d57a73ff095d9c08ee750e2936e30f349b081923e7857b0c856dd538e268655",
    "part-002.b64": "9e1873cc4ce5e342ccf9c5f12dfefa35d21e2ef3698efbdcae5cd124df140f7c",
    "part-003.b64": "2c03d4ae44eaeeae08398abd9fe0b3049377048c2512a6ecc421a947db2ea38f",
    "part-004.b64": "4d816de42612860e79abcf87f6fb43bf5b8dff4f8831fcaaa1078686178111b1",
    "part-005.b64": "29cb8d95d64f7dc9b4d132e14635ac8f6f0e6e9db740a6506ddbfbfd74af9313",
    "part-006.b64": "48c43f98cd18922faa4f98064145ccc68b8cf28e730b852e4b946aaab5cbadac",
    "part-007.b64": "50c89ac739feee58d6899499bb7be5feb838eefd5173ef17b13fe98880f0a33f",
    "part-008.b64": "168955f957dba711118dce9937e82e2c82a100f9cbd63f7b3f121594789446c0",
    "part-009a.b64": "534df05b6af61cd2e6bc5ebdbffed6afacbd94cd8c92b578645e55d4f6910613",
    "part-009b.b64": "8331bfbeff798e3cd878a34fa211f83e775b428e154836252371b89583507fb0",
    "part-010.b64": "4b8f6e01fbfc326cac5a046f0c03de3ed41a550f23cb1419a138c6df6315cbff",
    "part-011.b64": "ea3c485631e173ae7a3b74395cc0fcc5db55ccce91c7791d6babf598e16d27bd",
}


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def reconstruct_archive() -> bytes:
    chunks: list[str] = []
    for name, expected_hash in CHUNK_HASHES.items():
        path = PARTS / name
        if not path.is_file():
            raise RuntimeError(f"Missing release part: {name}")
        chunk = path.read_text(encoding="utf-8").strip()
        digest = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
        if digest != expected_hash:
            raise RuntimeError(f"Corrupt release part {name}: {digest}")
        print(f"Verified {name}: {len(chunk)} characters")
        chunks.append(chunk)
    raw = base64.b64decode("".join(chunks), validate=True)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"Archive SHA-256 mismatch: {digest}")
    return raw


def write_project_files() -> None:
    readme = """# 🎙️ Saninka Voice System

Русский голосовой мод для **Project Zomboid Build 42**.

> **v0.1.0-alpha** — технический каркас с бесшумными заглушками до добавления записанной озвучки.

## ✨ Возможности

- 🧠 74 контекстных игровых события;
- 🎤 204 подготовленных аудиослота;
- 🧟 реакции на зомби, орды и опасность;
- ❤️ состояния персонажа: голод, жажда, боль, паника и усталость;
- 🛠️ реакции на лечение, чтение, ремонт и строительство;
- 🌐 клиентская и серверная Lua-логика;
- 🔊 приоритеты, cooldown, субтитры и пространственный звук;
- 🔇 безопасный OGG-placeholder вместо отсутствующих записей.

## 📦 Установка

1. Скачай ZIP в разделе **Releases**.
2. Распакуй папку `Contents` в каталог Project Zomboid.
3. Включи **Saninka Voice System** в меню модов.

## 🎧 Запись озвучки

Имена будущих WAV-файлов берутся из `SVS_Manifest.lua`. Рекомендуемый формат: mono, 48 kHz, 24-bit PCM.

## ⚠️ Статус

Реальные голосовые записи и окончательная регистрация отдельного Voice Style будут добавлены в следующих версиях.
"""
    notes = """# 🎙️ Saninka Voice System v0.1.0-alpha

Первый технический alpha-релиз мода озвучки для Project Zomboid Build 42.

## ✨ В релизе

- 74 игровых события и 204 аудиослота;
- клиентская, серверная и общая Lua-логика;
- cooldown, приоритеты, субтитры и пространственный звук;
- подготовленная структура будущего аудиобанка;
- бесшумный OGG-placeholder до добавления записей.

## ⚠️ Важно

Реальные голосовые записи пока не включены.
"""
    recording = """# 🎤 Руководство по записи

Записывай в WAV mono, 48 kHz, 24-bit PCM. Не добавляй музыку, реверберацию или эффект рации. Оставляй 100–200 мс тишины в начале и конце.

Имена файлов находятся в:
`Contents/mods/SaninkaVoiceSystem/42/media/lua/shared/SVS/SVS_Manifest.lua`
"""
    architecture = """# 🧩 Архитектура

- `SVS_Manifest.lua` — события, варианты, субтитры и имена файлов.
- `SVS_ReactionEngine.lua` — игровые состояния и действия.
- `SVS_Audio.lua` — очередь, приоритеты и воспроизведение.
- `SVS_Client.lua` / `SVS_Server.lua` — клиент и мультиплеер.
- `SVS_Sounds.txt` — регистрация звуков Project Zomboid.
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    (ROOT / "RELEASE_NOTES.md").write_text(notes, encoding="utf-8")
    (ROOT / "VERSION").write_text("0.1.0-alpha\n", encoding="utf-8")
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "RECORDING_GUIDE.md").write_text(recording, encoding="utf-8")
    (docs / "ARCHITECTURE.md").write_text(architecture, encoding="utf-8")

    workflows = ROOT / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    for path in workflows.glob("*.yml"):
        path.unlink()
    (workflows / "release.yml").write_text("""name: Validate release tags
on:
  push:
    tags: ['v*']
permissions:
  contents: read
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python tools/validate_project.py
      - run: python tools/package_release.py
""", encoding="utf-8")


def main() -> None:
    raw = reconstruct_archive()
    INSTALL_ZIP.parent.mkdir(exist_ok=True)
    INSTALL_ZIP.write_bytes(raw)
    with zipfile.ZipFile(INSTALL_ZIP) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"Corrupt ZIP entry: {bad}")
        archive.extractall(ROOT)

    shutil.rmtree(ROOT / "bootstrap", ignore_errors=True)
    shutil.rmtree(ROOT / ".release", ignore_errors=True)
    trigger = ROOT / ".github" / "RELEASE_v0.1.0-alpha"
    if trigger.exists():
        trigger.unlink()
    write_project_files()

    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("git", "add", "-A")
    status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, check=True, text=True, capture_output=True)
    if status.stdout.strip():
        run("git", "commit", "-m", f"🎙️ Release Saninka Voice System {TAG}")
        run("git", "push", "origin", "HEAD:main")
    print(f"Prepared {INSTALL_ZIP.name}; SHA-256 {EXPECTED_SHA256}")


if __name__ == "__main__":
    main()
