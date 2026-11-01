#!/bin/bash
# Make sure the cloud workspace can render: python libs, fonts, ffmpeg, draft TTS.
python3 -c "import cairo, numpy, PIL" 2>/dev/null || pip install --break-system-packages -q pycairo numpy pillow
command -v ffmpeg >/dev/null || (apt-get update -qq && apt-get install -y -q ffmpeg)
fc-list | grep -q "Inter" || (apt-get update -qq && apt-get install -y -q fonts-inter)
fc-list | grep -q "Noto Sans CJK" || apt-get install -y -q fonts-noto-cjk
fc-list | grep -q "DejaVu" || apt-get install -y -q fonts-dejavu-core
python3 -c "import cairo; s=cairo.ImageSurface(cairo.FORMAT_ARGB32,10,10); c=cairo.Context(s); c.select_font_face('Inter Black'); print('render env ok')"
