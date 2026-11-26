# Render a shot

A shot is a lit scene with thickness: geometry or footage, a camera, materials, and motion blur. That is the picture Blender and Maya render, the composite After Effects finishes, and the sequence Premiere cuts. A stroked outline, a flat polygon, or a wireframe is not a shot.

The creator does not open an editor. You run the tools.

## Which tool

Use the first case that is true. Stay with it for the shot.

1. The creator supplied a Maya scene, and `Render` or `mayapy` runs. Render that scene. Do not rebuild it as polygons in another program.
2. The creator supplied an After Effects project, and `aerender` runs. Render that comp. Do not author a new `.aep`.
3. Otherwise Blender. If `blender` is not on PATH, install the current official build and call that binary. Windows: `winget install --id BlenderFoundation.Blender -e`. macOS: `brew install --cask blender`. Linux: the official tarball from blender.org for the same major version you will script. Do not install Maya, After Effects, or Premiere in order to start a shot.

A new graphic that would have been an After Effects comp is a Blender scene held to the same rules: one job per shot, eased keys, motion blur, type from a font file.

The edit that would have been a Premiere sequence is an in and an out on a frame, handles of at least eight frames, the joins in [craft](craft.md), and sound cut separately from picture. Execute that with FFmpeg, then the assembler in [production](production.md). Do not open Premiere. Leave a supplied `.prproj` untouched.

`scripts/motion.py` can check a path or a timing while you block. It does not draw the frame that ships.

## Defaults

Copy these. Change a number only when [the consistency document](craft.md) or [the platform master](platforms.md) requires it.

- Cycles. 32 samples for the contact frame. 128 samples and denoising for the shot.
- Motion blur on, shutter 0.5, centered on the frame.
- AgX when that view transform exists, otherwise Filmic. Look none. The film's one grade is applied later, from the consistency document.
- Resolution, frame rate, and the delivery codec from the platform master. Write a 16-bit PNG sequence, then encode the shot.
- Lens 35mm unless the shot needs another. Depth of field off unless the consistency document names a focus target.
- An area key light, its size written in the script, colored from the palette. One fill or a bounce card. The world is the palette ground at a strength below 1, not the startup gray and not the only light.
- Principled BSDF. Roughness and metallic are numbers in the script. The subject has thickness. Emission is a practical lamp, not the edge of the subject.
- Freestyle off. No Grease Pencil picture. No wireframe modifier. No outline pass.
- Words that move are a text object. Load the font file named in the consistency document with `bpy.data.fonts.load`. A still title may be a font plate composited in the edit. The startup font is not used. An image model does not paint words.
- Keys stay Bezier. Factory startup already does that. Do not switch a move to linear.

## The shot file

One `shot.py` for this shot, written before the render. The next shot is a new file that appends the canon objects. Put `CONTACT = True` on the first line. Render the contact, open the PNG, and fix the first concrete failure in this file. Set `CONTACT = False` only after that frame is right, then render the shot. Do not start a second scene.

```python
CONTACT = True

import bpy

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 32 if CONTACT else 128
scene.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    # Factory startup leaves the compute type at NONE, so a listed GPU is unused
    # until one backend is selected. Enable that backend only.
    chosen = None
    for backend in ("CUDA", "OPTIX", "HIP", "ONEAPI", "METAL"):
        try:
            prefs.compute_device_type = backend
        except TypeError:
            continue
        prefs.get_devices()
        if any(device.type == backend for device in prefs.devices):
            chosen = backend
            break
    if chosen:
        for device in prefs.devices:
            device.use = device.type == chosen
        scene.cycles.device = "GPU"
    else:
        scene.cycles.device = "CPU"
except Exception:
    scene.cycles.device = "CPU"

# Master size and frame rate from platforms.md. 1920x1080 at 24 is the long master.
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 1 if CONTACT else 48  # replace 48 with this shot's last frame
scene.render.use_motion_blur = True
scene.render.motion_blur_shutter = 0.5
scene.render.motion_blur_position = "CENTER"
names = {item.identifier for item in scene.view_settings.bl_rna.properties["view_transform"].enum_items}
scene.view_settings.view_transform = "AgX" if "AgX" in names else "Filmic"
scene.view_settings.look = "None"
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_depth = "16"
scene.render.filepath = "//contact.png" if CONTACT else "//shot_"
scene.render.use_file_extension = not CONTACT

world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
background = world.node_tree.nodes.get("Background")
if background:
    # Replace with the palette ground from consistency.md before the contact render.
    background.inputs[0].default_value = (0.05, 0.05, 0.06, 1)
    background.inputs[1].default_value = 0.2

cube = bpy.data.objects.get("Cube")
if cube:
    bpy.data.objects.remove(cube, do_unlink=True)
if scene.camera:
    scene.camera.data.lens = 35

# Build the subject here. Aim the camera. Area key, plus one fill or a bounce.
# Keyframe with keyframe_insert. Leave the interpolation at Bezier.
# Moving type: curve = bpy.data.curves.new("Title", "FONT"); curve.font = bpy.data.fonts.load(font_path)

if CONTACT:
    bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
```

Run it with factory startup so a custom startup file cannot leak into the frame:

```text
blender --background --factory-startup --python shot.py
```

Open `contact.png` before you change `CONTACT`. Check the subject, the light direction, the lens, and any word against the consistency document. Then render the range.

A supplied Maya scene, with the renderer saved in the file:

```text
Render -s 1 -e 48 -x 1920 -y 1080 scene.ma
```

Match the master resolution and frame rate. Motion blur stays as the scene saved it. If a moving subject is sharp, turn motion blur on in that scene and render the contact again. An Arnold frame with a watermark is not a master. Render that shot in Blender instead.

A supplied After Effects project:

```text
aerender -project spot.aep -comp MASTER -output shot_[#####].png
```

## Encode, then hand it on

Encode the PNG sequence to one shot file with the container in [platforms](platforms.md): MP4, H.264, yuv420p, faststart. Use the master frame rate. A shot with no sound yet can be silent. [Production](production.md) mixes the master and says what the helper may check. The helper does not draw this shot.
