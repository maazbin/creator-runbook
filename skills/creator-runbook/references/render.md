# Render a shot

A shot has thickness, a camera, and a light. It is the picture a professional 3D program would render and a professional edit would cut. Blender, Maya, After Effects, and Premiere are that standard. They are not programs to install or open.

You draw the shot. A stroked outline, a flat diagram, or a wireframe is not a shot. An image model does not paint words, numbers, captions, or the diagram.

## How

Draw it in code, then encode it with FFmpeg. The creator does not open an editor, and you do not open one either.

- The subject has a top and a side. Project it from a camera. One key, colored from the palette, and one fill. Shadows sit on the ground.
- Words come from a font file named in the consistency document. A word that moves travels with the object it names. A still title is set in the same frame or composited with FFmpeg. The default font is not used.
- A move eases in and out. A straight lerp is not a move. When nothing changes, hold the frame. The file stays at the master frame rate. Do not stretch or compress the voice to fill a hold.
- Draw one contact frame first. Open it. Fix the first concrete failure. Then write the shot.
- A smear of a few frames is enough blur. Do not start a path tracer, and do not install a 3D application to get one.

Supplied footage is used as itself. A scene file for another program is not a reason to install that program. If the creator already handed you a finished picture, grade it and cut it.

## Defaults

Copy these. Change a number only when the consistency document or [the platform master](platforms.md) requires it.

- Resolution, frame rate, and codec from the platform master. A long film is 1920×1080 at 24 fps. Encode H.264, yuv420p, AAC-LC, faststart.
- The camera feels like a 35mm lens unless the shot needs another. A board is read from the south unless the consistency document says otherwise.
- One grade, the one in the consistency document.
- The world is the palette ground, not a neutral gray and not the only light.

## Encode, then hand it on

Encode the shot with the container in [platforms](platforms.md). A shot with no sound yet can be silent. [Production](production.md) mixes the master and says what the helper may check. The helper does not draw this shot.

## A runnable contact frame

For a folded object, import `surface` from [fold.py](../scripts/fold.py) into the shot. It projects six vertices, draws faces in depth order, shades each normal against a key and fill, and can project a contact shadow. For a different subject keep the projection and replace the mesh and materials. Examine the hinge, shadow and silhouette in the saved frame before rendering the action.

```python
from PIL import Image, ImageDraw
from fold import surface

image = Image.new("RGB", (1080, 1920), "#284e56")
surface(ImageDraw.Draw(image), (530, 900), 5, pitch=-8, bank=20,
        shadow=(1100, 200, "#1b3a40"))
image.save("contact.png")
```
