# 3dpce.py

Somewhat configurable script to estimate 3d prints costs, given a configuration and a GCode file.

Run with python, requires no external libraries:
`./3dpce.py -c config.example.ini <path-to-gcode-file>`

GCode parsing has been tested on OrcaSlicer, because I don't like using BambuLab's slicer, it's slow af.
Sample configuration in the `config.example.ini` file.
