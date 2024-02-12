import os
import sys

import invoke
import livereload

sys.path.append(os.path.abspath(".."))

from fretboard2 import (  # noqa:L E402
    BassChord,
    GuitarChord,
    GuitarFretboard,
    UkuleleChord,
)

server = livereload.Server()


@invoke.task
def clean(ctx):
    os.system("rm -rf ./svg/*.svg")


@invoke.task
def build(ctx):
    # Chord (D)
    chord = GuitarChord(positions="xx0232", fingers="---132", title="D Major Chord")
    chord.save("svg/D.svg")

    # Barre chord (F#)
    chord = GuitarChord(positions="133211", fingers="134211", title="F#")
    chord.save("svg/F-sharp.svg")

    # C shape, higher up the neck
    chord = GuitarChord(positions="x-15-14-11-12-11", fingers="-43121", title="C")
    chord.save("svg/C-shape.svg")

    # Ukulele chord (G)
    chord = UkuleleChord(positions="x232", fingers="-132", title="G")
    chord.save("svg/ukulele-G.svg")

    # Ukulele chord (G)
    chord = UkuleleChord(positions="x232", fingers="-132")
    chord.save("svg/ukulele-G-no-title.svg")

    # Bass chord (E)
    chord = BassChord(positions="x221", fingers="-321", title="E")
    chord.save("svg/bass-E.svg")

    # Fretboard w/ Rocksmith-style string colors (F#)
    fb = GuitarFretboard(
        title="F#",
        style={
            "drawing": {"background_color": "black"},
            "fret": {"color": "darkslategray"},
            "nut": {"color": "darkslategray"},
            "marker": {"color": "darkslategray", "border_color": "slategray"},
            "string": {"color": "darkslategray"},
        },
    )
    fb.add_marker(string=(0, 5), fret=1, label="1")
    fb.add_marker(string=1, fret=3, label="3")
    fb.add_marker(string=2, fret=3, label="4")
    fb.add_marker(string=3, fret=2, label="2")

    fb.strings[0].color = "red"
    fb.strings[1].color = "gold"
    fb.strings[2].color = "deepskyblue"
    fb.strings[3].color = "orange"
    fb.strings[4].color = "limegreen"
    fb.strings[5].color = "magenta"

    fb.save("svg/F-sharp-rocksmith.svg")

    # Pentatonic scale shape w/ highlighted root notes
    fb = GuitarFretboard(
        frets=(5, 8),
        style={
            "marker": {"color": "cornflowerblue"},
            "drawing": {"orientation": "landscape"},
        },
    )
    fb.add_marker(string=0, fret=5, label="A", color="salmon")
    fb.add_marker(string=1, fret=5, label="D")
    fb.add_marker(string=2, fret=5, label="G")
    fb.add_marker(string=3, fret=5, label="C")
    fb.add_marker(string=4, fret=5, label="E")
    fb.add_marker(string=5, fret=5, label="A", color="salmon")

    fb.add_marker(string=0, fret=8, label="C")
    fb.add_marker(string=1, fret=7, label="E")
    fb.add_marker(string=2, fret=7, label="A", color="salmon")
    fb.add_marker(string=3, fret=7, label="D")
    fb.add_marker(string=4, fret=8, label="G")
    fb.add_marker(string=5, fret=8, label="C")
    fb.save("svg/pentatonic-shape.svg")


@invoke.task(pre=[clean, build])
def serve(ctx):
    server.watch(__file__, lambda: os.system("invoke build"))
    server.watch("index.html", lambda: os.system("invoke build"))
    server.watch("../fretboard/", lambda: os.system("invoke build"))

    server.serve(root=".", host="localhost", liveport=35729, port=8080)
