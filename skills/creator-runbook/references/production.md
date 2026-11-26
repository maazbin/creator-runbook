# Agent-operated production

The creator asks for the result in chat and, when they have material, gives access to it. They do not open an editor. The commands here are for the coding agent. Use the native code sandbox or shell. The supplied path uses Python 3.10+, Pillow, and an FFmpeg build with libx264 and AAC. Locate existing runtimes first; when needed, provision missing dependencies in a private workspace using the host's normal package mechanism. Pictures are rendered first, as in [the render path](render.md). This helper does not draw the shot.

Produce missing picture, type, and sound yourself before you call the helper. Set type in a font engine or in HTML. [Craft](craft.md) is the finish bar. The helper assembles finished shots and can draw an intertitle. It is not the design.

## One commission

Create a private working directory outside the public checkout for briefs, licensed material, receipts and exports. Copy only relevant assets obtained with the creator's access. Keep the original read-only. A local channel profile needs id, name, platform, niche, audience, language and editorial voice. Give each distinct destination a different stable id, even for two accounts on the same platform. Optional fields are format (portrait, square or landscape), seconds (default 45), accent (hex), delivery (captioned or voiced), font (local font with the required glyphs), voice_model and sources (a map of evidence IDs to precise descriptions and locators).

Run from the skill directory. Supply UTF-8 JSON on standard input to configure and finish. The angle brackets below denote values the agent substitutes. The example files in the repository show complete inputs.

```text
python scripts/channels.py --desk <private-dir> configure
python scripts/channels.py --desk <private-dir> claim <channel-id> <request-id>
python scripts/channels.py --desk <private-dir> finish <job-number> <token>
python scripts/channels.py --desk <private-dir> status
```

Configure upserts a full profile. Read the existing profile with `list` before modifying it. Store approved media under `<private-dir>/assets/<channel-id>/`. Claim returns the channel brief, asset filenames, recent angles and a job token. Read the current creative request alongside this packet. Write according to [the episode contract](episode-contract.md), then call finish. If FFmpeg is outside PATH, set CREATOR_FFMPEG to its executable. The writer and the renderer use the same host. Keep the request ID stable on retries; a completed request returns its prior delivery path. A new commission gets a new request ID. After an interrupted claim, its lease can be reclaimed after two hours. A failed validation leaves the job open for correction with the same token. To park it, call `block <job-number> <token> <reason>`; after a missing asset or brief is fixed, call `retry <job-number>`, then claim the same request again.

Finish produces video.mp4, captions.srt, post.txt, script.txt, episode.json and channel.json. Return only the requested shareable materials. Keep channel.json and production records private unless the creator asks for them. Scene-level captions are a starting point. Split long lines into timed phrases against recorded speech, include meaningful sounds, and check the final SRT against playback.

## Voice, sound and character

For a supplied performance use its measured source in-points. Cut the picture to the voice, keeping a continuous reading across cutaways. Supply a mixed audio master or individual stems mixed into one track per shot. The helper accepts an audio file, synced picture sound, or synced presenter sound. A presenter clip occupies the lower half of the frame. For a generic narrator, the voiced mode can use an installed Windows system voice, macOS say or Linux eSpeak, with no provider key. Check that the chosen voice speaks the channel language. For a specifically requested voice clone, use its authorized recording or provider. The optional CREATOR_TTS_COMMAND accepts a JSON argv array for a local synthesizer reading text on stdin and writing PCM WAV to {wav}, with {voice} expanded from the profile. Only the host configures executable commands. Silence is a valid choice for a commissioned wordless piece. Never substitute silence for requested speech without saying so.

Author the picture first, as in [the render path](render.md), then cut it with the media layout so the evidence checks still run. A scene is photography, footage, or that finished render, graded to the consistency document. For a long film, render by sequence, review the joins and the claims, then assemble at the master aspect ratio. Use `statement`, `compare`, and `steps` only for a true intertitle or a chapter card. Those layouts are not the documentary and not the performance.
