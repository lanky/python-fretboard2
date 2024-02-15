import copy

import attrdict
import svgwrite

# fretboard = Fretboard(strings=6, frets=(3, 8))
# fretboard.add_string_label(string=1, label='X', color='')
# fretboard.add_barre(fret=1, strings=(0, 5), label='')
# fretboard.add_marker(fret=1, string=1, label='', color='')
from ._defaults import DEFAULTS
from .compat import StringIO
from .utils import dict_merge


class Fretboard(object):
    default_style = DEFAULTS

    def __init__(self, strings=None, frets=(0, 5), inlays=None, title=None, style=None):
        self.frets = list(range(max(frets[0] - 1, 0), frets[1] + 1))
        self.strings = [
            attrdict.AttrDict(
                {
                    "color": None,
                    "label": None,
                    "font_color": None,
                }
            )
            for x in range(self.string_count)
        ]

        self.markers = []

        # Guitars and basses have different inlay patterns than, e.g., ukulele
        # A double inlay will be added at the 12th/24th/... fret regardless.
        self.inlays = inlays or self.inlays

        self.layout = attrdict.AttrDict()

        self.style = attrdict.AttrDict(
            dict_merge(copy.deepcopy(self.default_style), style or {})
        )

        self.title = title

        self.drawing = None

    def add_string_label(self, string, label, font_color=None):
        self.strings[string].label = label
        self.strings[string].font_color = font_color

    def add_marker(self, string, fret, color=None, label=None, font_color=None):
        self.markers.append(
            attrdict.AttrDict(
                {
                    "fret": fret,
                    "string": string,
                    "color": color,
                    "label": label,
                    "font_color": font_color,
                }
            )
        )

    def add_barre(self, fret, strings, finger):
        self.add_marker(
            string=(strings[0], strings[1]),
            fret=fret,
            label=finger,
        )

    def calculate_layout(self):
        """Figure out spacing on left, right, top etc.

        Taking into account whether this is portrait or landscape.
        Some of these variable names could do with being clearer

        Uses the configurtion read in from your config.yml (or defaults)
        Key vars/settings

        drawing.spacing: default margin around fretboard
        drawing.width:   width of entire image
        drawing.height:  height of entire image
        nut.size:        how wide the "zero fret" should be
        title.font_size: size of font for title
        string.label.font_size: size of font for string labels

        The config includes settings for title fonts etc too, sizes are taken
        into consideration

        Calculates (as self.layout.THING):
            self.layout:
              x:            x coordinate of fretboard (measured from left)
              y:            y coord of fretboard (measured from top)
              width:        width of fretboard
              height:       height of fretboard
              string_space: spacing between strings
              fret_space:   spacing between frets
              marker_size:  size (diameter/stroke size) for markers and barres
        """
        # common calculations for both portrait and landscape layouts
        # both orientations have the title at the top, if there is one
        self.layout.y = self.style.drawing.spacing

        # if there is a title, it needs some extra space
        if self.title:
            self.layout.y += self.style.drawing.spacing + self.style.title.font_size

        # we always have at least the default margin on the left
        self.layout.x = self.style.drawing.spacing

        # now cope with portrait and landscape differences
        # portrait:
        # string labels & title on top
        # inlays on left, fret numbers on right
        if self.style.drawing.orientation == "portrait":
            # fret length, wdith from str[0]->[-1]
            # ALWAYS leave space on the right for fret labels
            self.layout.width = self.style.drawing.width - (
                self.layout.x + self.style.drawing.spacing
            )
            if self.frets[0] > 0:
                self.layout.width -= self.style.drawing.spacing

            # length of strings, from top to bottom of grid
            self.layout.height = self.style.drawing.height - (
                self.layout.y + self.style.drawing.spacing
            )

            self.layout.string_space = self.layout.width / (len(self.strings) - 1)
            self.layout.fret_space = (self.layout.height - self.style.nut.size * 2) / (
                len(self.frets) - 1
            )

        # landscape:
        # title and fret numbers (if shown) on top
        # string labels on left
        # inlays on bottom
        else:
            # if you still have your drawing width < height, this will appear quite sqaushed.
            self.layout.width = self.style.drawing.height - (
                self.style.drawing.spacing * 2.25
            )

            self.layout.height = self.style.drawing.width - (
                self.style.drawing.spacing * 2
            )

            self.layout.x = (
                self.style.drawing.spacing + self.style.string.label_font_size
            )

            self.layout.string_space = self.layout.height / (len(self.strings) - 1)
            self.layout.fret_space = self.layout.width / (len(self.frets) - 1)

        # radius for markers and barres - no more than 60% of the width of a fret
        self.layout.radius = (
            min([self.layout.fret_space, self.layout.string_space]) * 0.3
        )

    def get_layout_string_index(self, string_index):
        if self.style.drawing.orientation == "portrait":
            return string_index
        else:
            return len(self.strings) - string_index - 1

    def draw_frets(self):
        for index, fret in enumerate(self.frets):
            if index == 0 and self.frets[0] == 0:
                # The first fret is the nut, don't draw it.
                continue
            else:
                if self.style.drawing.orientation == "portrait":
                    top = self.layout.y + self.style.nut.size
                    start = (self.layout.x, top + (self.layout.fret_space * index))
                    end = (
                        self.layout.x + self.layout.width,
                        top + (self.layout.fret_space * index),
                    )
                else:
                    left = self.layout.x + self.style.nut.size
                    fret_x = left + (self.layout.fret_space * index)
                    start = (fret_x, self.layout.y)
                    end = (fret_x, self.layout.y + self.layout.height)

                self.drawing.add(
                    self.drawing.line(
                        start=start,
                        end=end,
                        stroke=self.style.fret.color,
                        stroke_width=self.style.fret.size,
                    )
                )

    def draw_strings(self):
        """
        Draw lines to represent strings
        """
        if self.style.drawing.orientation == "portrait":
            # vertical strings, y is a constant
            start = self.layout.y
            end = start + self.layout.height
            label_y = (
                self.layout.y
                - self.style.drawing.spacing
                + self.style.drawing.font_size / 2
            )
        else:
            # horizontal strings, x is a constant
            start = self.layout.x
            end = start + self.layout.width
            # x coordinate for string labels
            label_x = (
                self.layout.x
                + self.style.drawing.font_size / 2
                - self.style.drawing.spacing
            )

        for index, string in enumerate(self.strings):
            # Offset the first and last strings, so they're not drawn outside the edge of the nut.
            string_width = self.style.string.size - (
                (self.style.string.size / (len(self.strings) * 1.5)) * index
            )
            offset = 0
            str_index = self.get_layout_string_index(index)

            if str_index == 0:
                offset += string_width / 2.0
            elif str_index == len(self.strings) - 1:
                offset -= string_width / 2.0

            if self.style.drawing.orientation == "portrait":

                # horizontal position of str and its label
                label_x = (
                    self.layout.x + (self.layout.string_space * str_index) + offset
                )
                string_start = (label_x, start)
                string_stop = (label_x, end)

            elif self.style.drawing.orientation == "landscape":
                # strings go left to right, so only the ex coordinate changes
                label_y = (
                    self.layout.y + (self.layout.string_space * str_index) + offset
                )
                string_start = (start, label_y)
                string_stop = (end, label_y)

            self.drawing.add(
                self.drawing.line(
                    start=string_start,
                    end=string_stop,
                    stroke=string.color or self.style.string.color,
                    stroke_width=string_width,
                )
            )

            # Draw the label obove the string
            if string.label is not None:
                self.drawing.add(
                    self.drawing.text(
                        string.label,
                        insert=(label_x, label_y),
                        font_family=self.style.drawing.font_family,
                        font_size=self.style.drawing.font_size,
                        font_weight="bold",
                        fill=string.font_color or self.style.marker.color,
                        text_anchor="middle",
                        alignment_baseline="middle",
                    )
                )

    def draw_nut(self):
        if self.style.drawing.orientation == "portrait":
            top = self.layout.y + (self.style.nut.size / 2)
            nut_start = (self.layout.x, top)
            nut_end = (self.layout.x + self.layout.width, top)
        else:
            left = self.layout.x + (self.style.nut.size / 2)
            nut_start = (left, self.layout.y)
            nut_end = (left, self.layout.y + self.layout.height)

        if self.frets[0] == 0:
            self.drawing.add(
                self.drawing.line(
                    start=nut_start,
                    end=nut_end,
                    stroke=self.style.nut.color,
                    stroke_width=self.style.nut.size,
                )
            )

    def draw_inlays(self):
        for index, fret in enumerate(self.frets):
            if index == 0:
                continue

            inlay_dist = (
                self.style.nut.size
                + self.layout.fret_space * index
                - self.layout.fret_space / 2
            )

            if self.style.drawing.orientation == "portrait":
                x = self.style.drawing.spacing - (self.style.inlays.radius * 4)
                y = self.layout.y + inlay_dist
            else:
                x = self.layout.x + inlay_dist
                y = self.layout.y + self.layout.height + (self.style.inlays.radius * 4)

            if fret in self.inlays or fret - 12 in self.inlays:
                # Single dot inlay
                self.drawing.add(
                    self.drawing.circle(
                        center=(x, y),
                        r=self.style.inlays.radius,
                        fill=self.style.inlays.color,
                    )
                )
            elif fret > 0 and not fret % 12:
                if self.style.drawing.orientation == "portrait":
                    dot_1 = (x, y - (self.style.inlays.radius * 2))
                    dot_2 = (x, y + (self.style.inlays.radius * 2))
                else:
                    dot_1 = (x - (self.style.inlays.radius * 2), y)
                    dot_2 = (x + (self.style.inlays.radius * 2), y)

                # Double dot inlay
                self.drawing.add(
                    self.drawing.circle(
                        center=dot_1,
                        r=self.style.inlays.radius,
                        fill=self.style.inlays.color,
                    )
                )
                self.drawing.add(
                    self.drawing.circle(
                        center=dot_2,
                        r=self.style.inlays.radius,
                        fill=self.style.inlays.color,
                    )
                )

    def draw_fret_label(self):
        if self.frets[0] > 0:
            if self.style.drawing.orientation == "portrait":
                x = (
                    self.layout.width
                    + self.style.drawing.spacing
                    + self.style.inlays.radius
                )
                y = (
                    self.layout.y
                    + self.style.nut.size
                    + (self.style.drawing.font_size * 0.2)
                )
            else:
                x = (
                    self.layout.x
                    + self.style.nut.size
                    - (self.style.drawing.font_size * 0.75)
                )
                y = (
                    self.layout.y
                    - self.style.drawing.spacing
                    + self.style.drawing.font_size / 2
                )

            self.drawing.add(
                self.drawing.text(
                    f"{self.frets[0]}",
                    insert=(x, y),
                    font_family=self.style.fret.label.get("font_family")
                    or self.style.drawing.font_family,
                    font_size=self.style.fret.label.font_size,
                    font_style="italic",
                    font_weight="bold",
                    fill=self.style.drawing.font_color,
                    text_anchor="start",
                )
            )

    def draw_markers(self):
        for marker in self.markers:
            if isinstance(marker.string, (list, tuple)):
                self.draw_barre(marker)
            else:
                self.draw_marker(marker)

    def draw_marker(self, marker):
        # Fretted position, add the marker to the fretboard.
        marker_string = self.get_layout_string_index(marker.string)

        if self.style.drawing.orientation == "portrait":
            x = self.style.drawing.spacing + (self.layout.string_space * marker_string)
            y = sum(
                (
                    self.layout.y,
                    self.style.nut.size,
                    (self.layout.fret_space * (marker.fret - self.frets[0]))
                    - (self.layout.fret_space / 2),
                )
            )
        else:
            x = sum(
                (
                    self.layout.x,
                    self.style.nut.size,
                    (self.layout.fret_space * (marker.fret - self.frets[0]))
                    - (self.layout.fret_space / 2),
                )
            )
            y = self.style.drawing.spacing + (self.layout.string_space * marker_string)

        self.drawing.add(
            self.drawing.circle(
                center=(x, y),
                r=self.style.marker.radius,
                fill=marker.color or self.style.marker.color,
                stroke=self.style.marker.border_color,
                stroke_width=self.style.marker.stroke_width,
            )
        )

        # Draw the label
        if marker.label is not None:
            self.drawing.add(
                self.drawing.text(
                    marker.label,
                    insert=(x, y),
                    font_family=self.style.drawing.font_family,
                    font_size=self.style.drawing.font_size,
                    font_weight="bold",
                    fill=self.style.marker.font_color,
                    text_anchor="middle",
                    alignment_baseline="central",
                )
            )

    def draw_barre(self, marker):
        marker_string_0 = self.get_layout_string_index(marker.string[0])
        marker_string_1 = self.get_layout_string_index(marker.string[1])

        if self.style.drawing.orientation == "portrait":
            y = sum(
                (
                    self.layout.y,
                    self.style.nut.size,
                    (self.layout.fret_space * (marker.fret - self.frets[0]))
                    - (self.layout.fret_space / 2),
                )
            )
            start = (
                self.style.drawing.spacing
                + (self.layout.string_space * marker_string_0),
                y,
            )
            end = (
                self.style.drawing.spacing
                + (self.layout.string_space * marker_string_1),
                y,
            )

        else:
            x = sum(
                (
                    self.layout.x,
                    self.style.nut.size,
                    (self.layout.fret_space * (marker.fret - self.frets[0]))
                    - (self.layout.fret_space / 2),
                )
            )
            start = (
                x,
                self.style.drawing.spacing
                + (self.layout.string_space * marker_string_1),
            )
            end = (
                x,
                self.style.drawing.spacing
                + (self.layout.string_space * marker_string_0),
            )

        # Lines don't support borders, so fake it by drawing
        # a slightly larger line behind it.
        self.drawing.add(
            self.drawing.line(
                start=start,
                end=end,
                stroke=self.style.marker.border_color,
                stroke_linecap="round",
                stroke_width=(self.style.marker.radius * 2)
                + (self.style.marker.stroke_width * 2),
            )
        )

        self.drawing.add(
            self.drawing.line(
                start=start,
                end=end,
                stroke=self.style.marker.color,
                stroke_linecap="round",
                stroke_width=self.style.marker.radius * 2,
            )
        )

        if marker.label is not None:
            self.drawing.add(
                self.drawing.text(
                    marker.label,
                    insert=start,
                    font_family=self.style.drawing.font_family,
                    font_size=self.style.drawing.font_size,
                    font_weight="bold",
                    fill=self.style.marker.font_color,
                    text_anchor="middle",
                    alignment_baseline="central",
                )
            )

    def draw_title(self):
        if self.title is not None:
            x = self.layout.width / 2 + self.style.drawing.spacing
            y = self.layout.y - self.style.drawing.spacing
            self.drawing.add(
                self.drawing.text(
                    self.title,
                    insert=(x, y),
                    font_family=self.style.drawing.font_family,
                    font_size=self.style.drawing.font_size,
                    font_weight="bold",
                    fill=self.style.drawing.font_color,
                    text_anchor="middle",
                    alignment_baseline="central",
                )
            )

    def draw(self):
        self.drawing = svgwrite.Drawing(
            size=(
                self.style.drawing.width,
                self.style.drawing.height,
            )
        )

        if self.style.drawing.background_color is not None:
            self.drawing.add(
                self.drawing.rect(
                    insert=(0, 0),
                    size=(
                        self.style.drawing.width,
                        self.style.drawing.height,
                    ),
                    fill=self.style.drawing.background_color,
                )
            )

        self.calculate_layout()
        self.draw_frets()
        self.draw_inlays()
        self.draw_fret_label()
        self.draw_strings()
        self.draw_nut()
        self.draw_markers()
        self.draw_title()

    def render(self, output=None):
        self.draw()

        if output is None:
            output = StringIO()

        self.drawing.write(output)
        return output

    def save(self, filename):
        with open(filename, "w") as output:
            self.render(output)


class GuitarFretboard(Fretboard):
    string_count = 6
    inlays = (3, 5, 7, 9)


class BassFretboard(Fretboard):
    string_count = 4
    inlays = (3, 5, 7, 9)


class UkuleleFretboard(Fretboard):
    string_count = 4
    inlays = (3, 5, 7, 10)
