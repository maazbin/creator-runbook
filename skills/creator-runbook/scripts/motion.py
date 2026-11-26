"""Small, frame-rate independent motion primitives for original Pillow animation."""
from bisect import bisect_right
from math import atan2, cos, degrees, radians, sin

from PIL import Image


def progress(time, start, end):
    """Clamped progress for a beat specified in seconds."""
    if end <= start:
        raise ValueError("A motion beat needs a positive duration")
    return max(0.0, min(1.0, (time - start) / (end - start)))


def ease(value):
    """Ease both ends of a decision or a camera settle."""
    return value * value * (3 - 2 * value)


def track(time, keys):
    """Interpolate (second, value) pairs. Equal neighboring values create a hold."""
    if not keys or any(a[0] >= b[0] for a, b in zip(keys, keys[1:])):
        raise ValueError("Key times must be strictly increasing")
    i = bisect_right([k[0] for k in keys], time)
    if i == 0:
        return keys[0][1]
    if i == len(keys):
        return keys[-1][1]
    a, b = keys[i-1], keys[i]
    return a[1] + (b[1] - a[1]) * ease(progress(time, a[0], b[0]))


def flight(points, t):
    """A cubic path and its tangent. Return x, y and screen-space angle in degrees."""
    if len(points) != 4:
        raise ValueError("A cubic flight path needs four control points")
    a,b,c,d = points
    t = max(0, min(1, t))
    u = 1-t
    xy = [u**3*a[i] + 3*u*u*t*b[i] + 3*u*t*t*c[i] + t**3*d[i] for i in (0,1)]
    dx,dy = [3*u*u*(b[i]-a[i])+6*u*t*(c[i]-b[i])+3*t*t*(d[i]-c[i]) for i in (0,1)]
    return *xy, degrees(atan2(dy,dx))


def pose(vertices, centre, scale, angle):
    """Place an illustrated silhouette with a stable local pivot."""
    a = radians(angle)
    x,y = centre
    return [(x+scale*(u*cos(a)-v*sin(a)), y+scale*(u*sin(a)+v*cos(a)))
            for u,v in vertices]


def camera(image, size, centre, zoom=1):
    """Render a subpixel camera crop; clamp the crop inside the source."""
    if zoom < 1:
        raise ValueError("Use overscan artwork for a wider view")
    w,h=image.size
    scale=min(w/size[0], h/size[1])/zoom
    cw,ch=size[0]*scale,size[1]*scale
    left=max(0,min(w-cw,centre[0]-cw/2))
    top=max(0,min(h-ch,centre[1]-ch/2))
    return image.resize(size,Image.Resampling.LANCZOS,box=(left,top,min(w,left+cw),min(h,top+ch)))
