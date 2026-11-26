# Voice

A spoken line is a performance. The feeling changes when the film turns. Write that change so the engine can play it, render the turn first, and listen before you render the rest.

System.Speech, macOS `say`, and eSpeak do not perform. Do not use them. The helper's voiced mode does not invent a take. Render the contact take below and supply that wav as the scene's audio. `edge-tts` writes MPEG and does not read a line on stdin, so do not point `CREATOR_TTS_COMMAND` at it. That variable is only for an argv that already writes 16-bit PCM WAV, as [production](production.md) describes. A line with its own rate and pitch is a file. The helper has no field for the pace row.

## Which engine

Use the first case that is true. Stay with that speaker for the whole film.

1. The creator supplied a recording, or an authorized voice. Use that take. Cut on a breath. Do not resynthesize a line you already have.
2. The creator named a provider, or one is already authorized on the machine. Send the words in the spoken field and the direction in that provider's own direction field. Preview the turn, the line where the feeling changes, before you spend a run on the full film.
3. Otherwise a neural voice through `edge-tts`. Install it with `pip install edge-tts`. It needs no key. One voice for the film's language: `en-US-AndrewNeural` for English, `zh-CN-YunxiNeural` for Chinese. For another language, run `python -m edge_tts --list-voices` and take the first Neural voice whose locale matches. Write the name in the consistency document. Do not change it per line.

That service accepts rate and pitch. It does not accept a style tag. A style tag is dropped or replaced with the wrong clip, so do not send one.

## Write the line

Two fields. The spoken field is only words a person would say. The direction field is the row below, or one sentence to a provider: who is speaking, to whom, and what just changed. Direction never goes inside the spoken field. Brackets, asterisks, and labels such as "sadly" are read aloud, or ignored.

Write the spoken field the way it is said. Short sentences. Contractions, unless the unstressed word is the point. A pause is a full stop or a new paragraph, not a stage direction. Say a number the way the ear should hear it, and leave the exact figure on screen. One feeling per line.

| The line | Rate | Pitch |
| --- | --- | --- |
| Setup, a fact before the turn | -8% | -2Hz |
| A question | -4% | +2Hz |
| The turn, where the meaning changes | -14% | -4Hz |
| The release, the last line letting the picture finish | -6% | +0Hz |

The turn uses a different row from the setup. Write the row beside the scene id before you synthesize.

## The contact line

Render the turn before any other line.

```text
python -m edge_tts --voice en-US-AndrewNeural --rate=-14% --pitch=-4Hz --text "The curve stays." --write-media turn.mp3
ffmpeg -y -i turn.mp3 -ar 48000 -ac 2 turn.wav
```

Use the film's voice name, the turn's words, and the turn's row. Open `turn.wav` and listen. If you cannot play it, say so and do not call the take finished. Render that line again when any of these is true:

- The turn is the same pace and pitch as the setup.
- A question does not lift at the end.
- The voice is the operating-system narrator.

Change the words or the row. Do not change the voice name, and do not start a second speaker. After the turn is right, render the other lines with the same voice and their own rows.

## Cut and continuity

The shot ends on the breath after the line. Add a little room from the same space if the picture holds. Do not stretch the voice to fill a longer shot, and do not compress it into one level. The picture is cut to this take.

Match the speaker, the mic distance, and the room across pickups. Keep the original sync audio when the mouth is visible. At source in-point s, edit start e, and playback rate r, a source word at w starts at e + (w − s) / r. If several gaps were removed, apply that mapping between the edits. Never lay a different line over a visible talking mouth.

Hand the wav to the assembler in [production](production.md). The caption file carries the words, not the direction.
