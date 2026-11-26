# Creator Runbook

**Describe the film. Get the masters back.**

Creator Runbook is the procedure a smaller model follows to finish at a Fable and Astra level. What that level means is in [the skill](skills/creator-runbook/SKILL.md). You write the brief. If you have footage, you give access to it. You do not open an editor. When a shot has no asset, the agent researches it, produces the picture and the type, and cuts the film. Recurring people, places, and palettes get one consistency document before the second shot.

The finish is a designed frame: real typography, a grade, and a join that means something. Shorts and long-form documentaries. YouTube, Instagram, TikTok, Bilibili, Douyin, Xiaohongshu, and the other players in [the platform list](skills/creator-runbook/references/platforms.md).

## A seven-word brief

“A paper plane misses the last train.” Watch the door light disappear, then follow the wing onto the last carriage. [Play the 15-second animation](examples/last-train/film.mp4) · [See the four shots and their source](examples/last-train/README.md).

## A finished pair

[Cordouan, 25 July 1823](examples/cordouan/). One researched film, two edits.

- Long master, 16:9, for YouTube and Bilibili. A cold open and one schematic chapter.
- Short master, 9:16, for Reels, TikTok, Shorts, and Douyin. The date is on screen in the first second.
- English and Chinese type, from the same grade and the same consistency document.

The pictures are labeled reconstructions. The date and the mechanism are sourced in that document. Those masters are a stills study. A new shot is a lit render, as in [the render path](skills/creator-runbook/references/render.md).

## Make one

Paste this into your coding agent.

```text
Use the video skill at https://github.com/maazbin/creator-runbook.
Read skills/creator-runbook/SKILL.md and handle setup for me.
Make a 45-second film, 16:9 and 9:16, about one real mechanism I can check.
Design the type, the grade, and the joins. Write the consistency note.
Give me the playable masters, captions, and the YouTube and Bilibili posts.
```

For your own footage, replace the brief and give the agent the folder. To keep the skill across projects, ask the agent to install `skills/creator-runbook`. It follows the [Agent Skills specification](https://agentskills.io/specification).

## What you can hand it

| You say | What the agent does |
| --- | --- |
| “Here is the folder. I am not opening an editor.” | Selects from the footage, builds what is missing, and returns masters. |
| “No assets. Find the story and make the pictures.” | Researches the claim, produces original picture and type, labels reconstructions. |
| “A documentary, and a short for every player.” | One consistency document, a long 16:9 cut, a 9:16 cut with its own first second, posts per destination. |
| “Use five seconds of me. Let my voice carry the demo.” | A short on-camera open, the voice continuous over the work, and a return for the close. [Presenter edit](skills/creator-runbook/references/presenter-short.md). |

## Under the hood

The agent writes, designs, and directs. Picture and type follow [the craft note](skills/creator-runbook/references/craft.md). A missing shot is drawn by the agent, as in [the render path](skills/creator-runbook/references/render.md). The cut is executed with FFmpeg. A spoken line is a performance from [the voice note](skills/creator-runbook/references/voice.md). The included helper uses Python, Pillow, and FFmpeg to assemble those finished shots, draw an intertitle when a chapter card is actually called for, and mux captions. Your footage and channel history stay in a private working directory.

The files in `examples/motion-notes` and `examples/last-light` are assembler fixtures. They are not the visual standard.

[Read the skill](skills/creator-runbook/SKILL.md) · [Craft](skills/creator-runbook/references/craft.md) · [Render](skills/creator-runbook/references/render.md) · [Voice](skills/creator-runbook/references/voice.md) · [Platforms](skills/creator-runbook/references/platforms.md) · [Production](skills/creator-runbook/references/production.md) · [MIT license](LICENSE)
