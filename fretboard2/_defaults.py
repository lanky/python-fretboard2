import yaml

DEFAULTS = yaml.safe_load(
    """
# global settings for fretboard/diagram
dynaconf_merge: true
drawing:
  orientation: portrait
  background_color:
  font_color: dimgray
  font_family: Verdana
  font_size: 24
  height: 400
  width: 300
  spacing: 30
  label_all_frets: true
# colour and weight of the nut (fret zero)
nut:
  color: darkslategray
  size: 10
# color and weight of frets
fret:
  color: darkgray
  size: 2
  label:
    font_size: 80%
    font_style: italic
# fret numbers
fret_label:
  width: 28
  font_style: italic
  font_size: 14
  font_color: blue
# fretboard inlays
inlays:
  color: darkslategray
  radius: 2
# strings and their labels
string:
  color: darkslategray
  size: 3
  muted_font_color: green
  open_font_color: red
  label_font_family: Verdana
  label_font_size: 14
  equal_weight: false
# blobs/finger position markers
marker:
  border_color: black
  color: black
  font_color: white
  radius: 2
  stroke_width: 2
# title, at top of diagram
title:
  font_color: dimgray
  font_family: Verdana
  font_size: 30
"""
)

CHORD = yaml.safe_load(
    """
chord:
  # These have the same options as above, and override them
  dynaconf_merge: true
  string:
    muted_font_color: silver
    open_font_color: darkslategray
    label_font_size: 12
"""
)
