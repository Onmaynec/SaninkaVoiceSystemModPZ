from __future__ import annotations

import base64
import hashlib
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / ".release" / "package"
EXPECTED_SHA256 = "450f34092bf695ba77fcea475baaab03d773832df36703c7eb64ef2c582757dd"
TAG = "v0.1.0-alpha"
INSTALL_ZIP = ROOT / "dist" / f"SaninkaVoiceSystem-{TAG}.zip"


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def reconstruct_archive() -> bytes:
    files = sorted(PARTS.glob("part-*.b64"))
    if not files:
        raise RuntimeError("Release package parts were not found")
    encoded = "".join(path.read_text(encoding="utf-8").strip() for path in files)
    raw = base64.b64decode(encoded, validate=True)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"Archive SHA-256 mismatch: {digest}")
    return raw


def write_documentation() -> None:
    readme = """# 🎙️ Saninka Voice System

Русский голосовой мод для **Project Zomboid Build 42**.

> Текущая версия: **v0.1.0-alpha** — технический каркас с бесшумными заглушками до добавления записанной озвучки.

## ✨ Что уже готово

- 🧠 74 контекстных игровых события;
- 🎤 204 подготовленных аудиослота;
- 🧟 реакции на зомби, орды и опасность;
- ❤️ голод, жажда, боль, паника, усталость и другие состояния;
- 🛠️ лечение, чтение, ремонт, строительство и прочие действия;
- 🌐 клиентская и серверная Lua-логика;
- 🔊 приоритеты, cooldown, субтитры и пространственный звук;
- 🔇 безопасный OGG-placeholder вместо отсутствующих записей.

## 📦 Установка

1. Скачай ZIP из раздела **Releases**.
2. Распакуй папку `Contents` в каталог Project Zomboid.
3. Включи **Saninka Voice System** в меню модов.

## 🎧 Добавление записей

Исходные WAV-файлы будут подключены в следующем релизе. Имена должны совпадать с манифестом в `SVS_Manifest.lua`.

## 🚧 Статус

Это предварительная alpha-версия. Нативная регистрация отдельного Voice Style будет окончательно подключена после проверки схемы Build 42.20 и получения записанного аудиобанка.
"""
    notes = """# 🎙️ Saninka Voice System v0.1.0-alpha

Первый технический alpha-релиз мода озвучки для Project Zomboid Build 42.

## ✨ В релизе

- 74 игровых события и 204 аудиослота;
- клиентская, серверная и общая Lua-логика;
- cooldown, приоритеты, субтитры и пространственный звук;
- подготовленная структура для будущего аудиобанка;
- бесшумный OGG-placeholder до добавления реальных записей.

## ⚠️ Важно

Реальные голосовые записи пока не включены. Это рабочий технический каркас для дальнейшего наполнения.
"""
    recording = """# 🎤 Руководство по записи

Записывай файлы в WAV mono, 48 kHz, 24-bit PCM. Не добавляй музыку, реверберацию или эффект рации. Оставляй 100–200 мс тишины в начале и конце.

Имена файлов берутся из:

`Contents/mods/SaninkaVoiceSystem/42/media/lua/shared/SVS/SVS_Manifest.lua`

Примеры:

- `svs_zombie_spotted_horde_01.wav`
- `svs_hunger_light_01.wav`
- `svs_combat_hit_taken_heavy_03.wav`
"""
    architecture = """# 🧩 Архитектура

- `SVS_Manifest.lua` — события, варианты, субтитры и имена аудиофайлов.
- `SVS_ReactionEngine.lua` — определение игровых состояний и действий.
- `SVS_Audio.lua` — очередь, приоритеты, cooldown и воспроизведение.
- `SVS_Client.lua` — клиентская инициализация и сетевые команды.
- `SVS_Server.lua` — серверная ретрансляция и ограничения.
- `SVS_Sounds.txt` — регистрация звуковых событий Project Zomboid.
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    (ROOT / "RELEASE_NOTES.md").write_text(notes, encoding="utf-8")
    (ROOT / "VERSION").write_text("0.1.0-alpha\n", encoding="utf-8")
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "RECORDING_GUIDE.md").write_text(recording, encoding="utf-8")
    (docs / "ARCHITECTURE.md").write_text(architecture, encoding="utf-8")


def write_future_release_workflow() -> None:
    workflow = """name: Validate release tags

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate project
        run: python tools/validate_project.py
      - name: Build archives
        run: python tools/package_release.py
"""
    directory = ROOT / ".github" / "workflows"
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("bootstrap.yml", "publish-on-trigger.yml", "publish-v0.1.0-alpha.yml", "trigger-test.yml"):
        path = directory / name
        if path.exists():
            path.unlink()
    (directory / "release.yml").write_text(workflow, encoding="utf-8")


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

    write_documentation()
    write_future_release_workflow()

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
