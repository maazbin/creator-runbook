"""Light and project a folded sheet using only math and a Pillow drawing surface.

Local x points along the nose; local z spans both wings. The screen-space anchor
and scale keep the same object usable as a station prop or a close-up insert.
"""

from math import cos, radians, sin, sqrt


def surface(draw, anchor, scale, pitch=0, bank=0, shadow=None):
    # Millimetres in a paper model. Valleys and ridges have distinct elevations.
    verts = [(64, 0, 0), (-53, 9, -46), (-25, -1, -2), (-40, -23, 0), (-48, 12, 48), (-25, -1, 2)]
    faces = [
        ((0, 1, 2), (220, 181, 141)),
        ((0, 2, 3), (182, 128, 101)),
        ((0, 3, 5), (190, 152, 116)),
        ((0, 5, 4), (255, 241, 204)),
    ]
    key = (0.29, 0.78, -0.55)
    b, p = radians(bank), radians(pitch)
    model = []
    for x, y, z in verts:
        y, z = y * cos(b) - z * sin(b), y * sin(b) + z * cos(b)
        x, y = x * cos(p) + y * sin(p), -x * sin(p) + y * cos(p)
        model.append((x, y, z))

    def project(pt):
        x, y, z = pt
        depth = z * 0.88 - y * 0.34
        perspective = 410 / (410 + depth)
        return (
            anchor[0] + scale * (x + z * 0.21) * perspective,
            anchor[1] - scale * (y * 0.93 + z * 0.37) * perspective,
        )

    projected = [project(pt) for pt in model]
    if shadow is not None:
        ground_y, gap, tone = shadow
        footprint = [(px + gap * 0.47, ground_y + (py - anchor[1]) * 0.25) for px, py in projected]
        for face, _ in faces:
            draw.polygon([footprint[k] for k in face], fill=tone)
    for face, base in sorted(
        faces, key=lambda f: -sum(model[k][2] * 0.88 - model[k][1] * 0.34 for k in f[0])
    ):
        a, b, c = [model[k] for k in face]
        u = tuple(b[i] - a[i] for i in range(3))
        v = tuple(c[i] - a[i] for i in range(3))
        normal = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        length = sqrt(sum(n * n for n in normal))
        if normal[1] < 0:
            normal = tuple(-n for n in normal)
        light = 0.71 + 0.36 * max(0, sum(k * n / length for k, n in zip(key, normal)))
        color = tuple(min(255, int(c * light)) for c in base)
        draw.polygon([projected[k] for k in face], fill=color)
        if face == (0, 1, 2):
            # Two ink marks printed on this wing follow its deformation and occlusion.
            for f in (0.20, 0.29):

                def inkpoint(t, u):
                    return tuple(
                        (1 - t - u) * projected[0][axis]
                        + t * projected[1][axis]
                        + u * projected[2][axis]
                        for axis in (0, 1)
                    )

                draw.polygon(
                    [
                        inkpoint(0.50, f),
                        inkpoint(0.61, f),
                        inkpoint(0.60, f + 0.035),
                        inkpoint(0.49, f + 0.035),
                    ],
                    fill="#bb604c",
                )
    draw.line(
        [projected[1], projected[0], projected[4]], fill="#fff0c3", width=max(1, round(scale * 0.9))
    )
    draw.line([projected[2], projected[0]], fill="#92614f", width=max(1, round(scale * 0.65)))
    return projected
