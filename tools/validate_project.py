from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "Contents" / "mods" / "SaninkaVoiceSystem" / "42"
MANIFEST = MOD / "media" / "lua" / "shared" / "SVS" / "SVS_Manifest.lua"

REQUIRED = [
    MOD / "mod.info",
    MOD / "icon.png",
    MOD / "poster.png",
    MOD / "media" / "lua" / "client" / "SVS" / "SVS_Audio.lua",
    MOD / "media" / "lua" / "client" / "SVS" / "SVS_Client.lua",
    MOD / "media" / "lua" / "client" / "SVS" / "SVS_ReactionEngine.lua",
    MOD / "media" / "lua" / "server" / "SVS" / "SVS_Server.lua",
    MOD / "media" / "lua" / "shared" / "SVS" / "SVS_Config.lua",
    MANIFEST,
    MOD / "media" / "scripts" / "SVS_Sounds.txt",
    MOD / "media" / "sound" / "SaninkaVoiceSystem" / "_placeholder_silence.ogg",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.is_file()]
    if missing:
        fail("Missing required files: " + ", ".join(missing))

    text = MANIFEST.read_text(encoding="utf-8")
    event_count = len(re.findall(r'^\s{4}\["[^"]+"\]\s*=\s*\{', text, flags=re.MULTILINE))
    audio_count = len(re.findall(r'\bfile\s*=\s*"svs_[^"]+\.ogg"', text))
    sound_count = len(re.findall(r'\bsound\s*=\s*"SVS_[A-Z0-9_]+"', text))

    if event_count != 74:
        fail(f"Expected 74 events, found {event_count}")
    if audio_count != 204:
        fail(f"Expected 204 audio slots, found {audio_count}")
    if sound_count != 204:
        fail(f"Expected 204 sound identifiers, found {sound_count}")

    mod_info = (MOD / "mod.info").read_text(encoding="utf-8")
    if "Saninka Voice System" not in mod_info:
        fail("mod.info does not contain the public mod name")

    print("Validation passed")
    print(f"Events: {event_count}")
    print(f"Audio slots: {audio_count}")


if __name__ == "__main__":
    main()
