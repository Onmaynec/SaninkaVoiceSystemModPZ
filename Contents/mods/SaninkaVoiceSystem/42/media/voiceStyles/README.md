# Native Voice Style integration

This directory is intentionally non-executable in v0.1.0-alpha.

The exact Build 42.20 voice-style schema will be copied from the installed game
reference before enabling `Saninka` in the built-in character creation list.
Shipping a guessed XML file could prevent the entire mod from loading.

Expected reference inputs from the game installation:

- `media/voiceStyles`
- `media/scripts/generated/sounds/player`

Once verified, this directory will contain the Saninka voice-style definition
and the generated sound-event mapping.
