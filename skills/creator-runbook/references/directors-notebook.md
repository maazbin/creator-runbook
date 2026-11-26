# A director’s notebook for generated films

Use this when a brief asks for a film, expressive animation, or an edit worth watching twice. The artist still chooses a style appropriate to the material. Carry the subject of the current commission through its hook, proof, captions, footage, and final card. A past launch can supply a rhythm or framing reference. Importing its footage or dialogue requires a reason in the new story.

## Short film: write a choice the camera can see

Write a tiny chain of events before writing a slogan. For “a paper plane misses the last train,” the plane approaches the gap, the doors close, the slipstream knocks it down, and it catches the roof of the last carriage. The ending changes the meaning of “misses.” The train must already be moving before the paper lifts. On the first board, place the door, plane and escape route where the viewer can relate all three.

Stage the sequence with four drawings or thumbnail renders:

| Frame | What the viewer needs to register | Editorial choice |
| --- | --- | --- |
| Before | The plane and the open door occupy the same space. | Hold a wide shot long enough to read the goal. |
| Contact | The door seam meets just before the nose. | Cut on the latch sound. Give the failed approach a reaction beat. |
| Reversal | The train moves ahead; the nose dips and then rises. | Stay low. Delay the tail slightly. Preserve left-to-right travel across the cut. |
| After | The plane rests on the moving roof. | Let the background move while the two subjects stay together. Hold through the sound resolution. |

A comedy can hold an extra beat before the reveal. An explainer can replace the missed train with a wrong prediction and a visible test. A product film can do the same with an actual input, operation and result. Give each shot one job.

## Animate the action before decorating the frame

Draw a distinct silhouette, a readable field behind it, and a foreground object that can briefly hide it. Decide where the eye should start and end. Define action in local coordinates so that a fold, hand, or door turns on its real hinge. A cubic path is useful for flight. A mechanical door usually follows a constrained line. Set a different size and velocity for foreground, middle distance, and skyline during a tracking shot.

Use the portable [motion helpers](../scripts/motion.py) with Pillow, or implement the same decisions in the host renderer. This is a complete frame recipe for a banked sheet of paper. Advance seconds at the export frame rate:

```python
from PIL import Image, ImageDraw
from motion import ease, flight, pose, progress

def frame(seconds):
    picture = Image.new("RGB", (720, 1280), "#12263b")
    draw = ImageDraw.Draw(picture)
    t = ease(progress(seconds, 0.2, 1.6))
    x, y, angle = flight([(80, 850), (280, 950), (400, 510), (610, 490)], t)
    wing = [(-47, -18), (53, 0), (-33, 15), (-8, 3)]
    draw.polygon(pose(wing, (x, y), 1.3, angle), fill="#ffe7ab")
    return picture
```

Add secondary movement only where it reveals force or character. A passing carriage can tug paper before it lifts; a window reflection can glide over a face before a turn. Decide the audio cue at the same time. Advance a motor, wind or footstep sound across a cut when it connects the spaces. Use a single new accent on the reveal. A still camera often makes a fast subject easier to follow.

**Repair a weak pass.** Render before, contact, reversal and payoff at phone size, hide captions, and name what changed. If all four frames still say “train,” fix the blocking. If the plane disappears against the roof, move its silhouette into open sky. If the viewer cannot tell it landed, lock its position to a particular carriage while the platform lights continue to slide. Preview the intervening frames as a loop to find pops, tangents and motion that reverses for a single frame. A four-frame contact sheet alone cannot show those defects.

## Long film: make each sequence change the question

For a documentary, essay or narrative spanning several minutes, make a sequence card with an incoming question, a scene or source that tests it, the change in the viewer’s understanding, and the next unanswered question. Track what has been *established* separately from what a participant believes. Maintain the map, date, character position, prop state and audio perspective at chapter boundaries.

Worked paper edit for a documentary about a closed station:

| Sequence | Action and evidence needed | Handoff |
| --- | --- | --- |
| The locked gate | Observe one arrival at the gate. Record the time and preserve location sound. | Where does this passenger go now? |
| The walk | Follow the route with consent. Measure this particular trip. Carry a crossing bell over the cut from the gate. | What did the official timetable assume? |
| The timetable | Put the dated schedule beside the measured walk. Identify the route and date each covers. | Who can explain the difference? |
| The return | Use a verified interview select or leave the question open. Return to the same gate and camera position. | Let the final shot acquire its meaning from what the viewer has learned. |

Build a silent thumbnail strip for geography, then a radio edit from the actual voices. Play a minute from the middle without the introduction. If we cannot tell where we are or whose evidence we are hearing, add a local orienting shot or a source cue. Build one chapter to finishing quality first, then reuse its typography, room tone, color relationships and recurring visual motif across the master. Re-time joins from the recorded performances. Give a motif a different narrative job each time it returns.
