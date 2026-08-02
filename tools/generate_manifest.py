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


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def reconstruct_archive() -> bytes:
    files = [PARTS / f"part-{index:03d}.b64" for index in range(12)]
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise RuntimeError("Missing release parts: " + ", ".join(missing))
    chunks = []
    for path in files:
        chunk = path.read_text(encoding="utf-8").strip()
        print(f"Using {path.name}: {len(chunk)} characters")
        chunks.append(chunk)
    encoded = "".join(chunks)
    raw = base64.b64decode(encoded, validate=True)
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
