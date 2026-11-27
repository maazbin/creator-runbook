# Opening a Filmcraft project

Keep the existing film.json and its media directory together. From the repository root, use the installed cut assembler to validate the plan, extract recording copy or render the file.

```sh
python skills/creator-runbook/scripts/cut.py check path/to/film.json
python skills/creator-runbook/scripts/cut.py script path/to/film.json
python skills/creator-runbook/scripts/cut.py render path/to/film.json path/to/new-master.mp4
```

The original booklet is a 21-second animation with paper sounds. To build its source clips and assemble them, install Pillow 10.1 or later and make FFmpeg available on PATH. Give the generator an empty working directory.

```sh
python skills/creator-runbook/examples/booklet/make_booklet.py productions/booklet
python skills/creator-runbook/scripts/cut.py render productions/booklet/film.json productions/booklet/master.mp4
```

See the [source edit plan](../examples/booklet/film.json) for the scene schema. The assembler resolves media relative to the plan and preserves existing exports.
