# Episode contract

Return one JSON object. Top-level fields are channel (profile id), platform, language (exact profile values), title, angle (a specific editorial question or story), post (public copy in the destination's register), and scenes in edit order. Sum seconds to the requested runtime, using whole frames at 24 fps. The validator allows a 15% runtime tolerance, with a one-second minimum margin. Respect stricter runtimes in the actual commission.

Each scene has a unique id, seconds, basis, evidence (list), voice (exact spoken words or empty string), picture (entry frame), change (visible action or exit), sound (what the listener hears), layout, heading, and line. For authored cards use layout statement, compare (two points), or steps (two or three points). The actual visible copy is heading, line, and points. For layout media supply file, relative to this channel's asset directory. Heading and line on a media scene are editorial metadata; burn required titles into the asset or use screen_label. Optional fields are in, presenter, presenter_in, audio and audio_in, with offsets in seconds. Audio may be @picture or @presenter to follow the selected clip. Supplied audio captions use voice as transcript; the optional caption field overrides the cue text. For wordless work use authored descriptive captions for meaningful sounds.

Use basis documented or observation with a real ID from the profile's sources for factual material. A proposal also needs screen_label and, for a voiced proposal, a spoken_qualification contained in voice. Use fiction for invented narrative and transition for purely connective material. Invented labels, footage and words cannot stand in for evidence. If an essential source is missing, research it or change the claim. For a technical validation failure, repair the named scene while preserving the underlying brief.

A complete tiny fixture is below. It illustrates the data shape. For a motion or performance brief, replace the card with actual picture assets.

Channel sent to configure:

```json
{"id":"night-window","name":"Night Window","platform":"instagram","niche":"microfiction","audience":"night readers","language":"en","voice":"Quiet first person","format":"square","seconds":5,"delivery":"captioned"}
```

Episode sent to finish:

```json
{
  "channel":"night-window", "platform":"instagram", "language":"en",
  "title":"The watch", "angle":"A shift changes hands at dawn",
  "post":"The last light on the street is someone’s first shift.",
  "scenes":[{
    "id":"window","seconds":5,"basis":"fiction","evidence":[],"voice":"",
    "layout":"statement","heading":"One window was still lit.",
    "line":"By dawn, it was my turn to keep watch.",
    "picture":"An illuminated sentence in an otherwise dark frame.",
    "change":"The final line hands the watch to the narrator.","sound":"Intentional silence."
  }]
}
```

For a ready-to-render richer example, see the two drafts and original animation source in the repository's examples directory. The coding agent chooses the form, writes the actual words, and produces or selects assets before calling the renderer.
