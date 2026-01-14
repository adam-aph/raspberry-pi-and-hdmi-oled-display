#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import moderngl
import numpy as np
from scipy.ndimage import distance_transform_edt as edt
import time
import math
import threading
import queue
from collections import deque
import random
import feedparser
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from PIL import Image
import os
import subprocess

# -------------------------
# Configuration
# -------------------------
WIDTH = 1424
HEIGHT = 600 # 280
CLOCK_W = 210
FEED_W = WIDTH - CLOCK_W
FPS = 30
SCROLL_SPEED = 20.0       # pixels per second for high-res
MAX_TEXT_CHARS = 200
FETCH_INTERVAL = 60.0
INJECT_EVERY = 10
MAX_RSS_PER_FETCH = 30

SCROLL_H = 280
ROW_PADDING_Y = 2
LEFT_PAD = 30
GAP_ICON_TEXT = 6
RIGHT_PAD = 6

FONT_SIZE = 24
SMALL_FONT_SIZE = 18
TINY_FONT_SIZE = 12
LINE_H = FONT_SIZE + 2 * ROW_PADDING_Y
ICON_SIZE = FONT_SIZE

TESS_SIZE = 180
TESS_CHANGE_INTERVAL = 5
TESS_ROT_SPEED = 0.5
TESS_X = WIDTH - (TESS_SIZE * 0.5) - 50
TESS_Y = (TESS_SIZE * 0.5) + 50

PARTICLE_COUNT = 120
PARTICLE_SPEED = 30.0

# Colors
COLOR_WHITE = (1.0, 1.0, 1.0, 1.0)
COLOR_GLOW = (1.0, 0.85, 0.35, 0.45)

ICON_COLORS = {
    'rss': (1.0, 0.55, 0.0, 1.0),
    'sun': (1.0, 0.95, 0.15, 1.0),
    'cloud': (0.72, 0.78, 0.86, 1.0),
    'rain': (0.18, 0.48, 0.95, 1.0),
    'snow': (0.92, 0.96, 1.0, 1.0),
    'thunder': (1.0, 0.95, 0.2, 1.0),
}

ICON_LAYER_COLORS = {
    'rss': {2: (1.0, 0.55, 0.0, 1.0), 3: (1.0, 0.55, 0.0, 1.0)},
    'sun': {2: (1.0, 1.0, 0.5, 1.0), 3: (1.0, 0.95, 0.15, 1.0)},
    'cloud': {2: (0.9, 0.9, 0.9, 1.0), 3: (0.72, 0.78, 0.86, 1.0)},
    'rain': {1: (0.1, 0.1, 1.0, 1.0), 2: (0.72, 0.78, 0.86, 1.0), 3: (0.72, 0.78, 0.86, 1.0)},
    'snow': {1: (0.8, 0.8, 1.0, 1.0), 2: (0.72, 0.78, 0.86, 1.0), 3: (0.72, 0.78, 0.86, 1.0)},
    'thunder': {1: (1.0, 1.0, 0.0, 1.0), 2: (0.72, 0.78, 0.86, 1.0), 3: (0.72, 0.78, 0.86, 1.0)},
}

# -------------------------
# Icon bitmaps (16x16 style)
# -------------------------
_RSS_16 = [
 [0,0,3,3,3,3,3,3,3,3,3,3,3,3,0,0],
 [0,0,3,3,3,3,3,3,3,3,3,3,3,3,0,0],
 [3,3,0,0,0,0,0,0,0,0,0,0,0,0,3,3],
 [3,3,0,0,0,0,0,0,0,0,0,0,0,0,3,3],
 [3,3,0,0,2,2,0,0,2,2,0,0,0,0,3,3],
 [3,3,0,0,2,2,0,0,2,2,0,0,0,0,3,3],
 [3,3,0,0,0,0,2,2,0,0,2,2,0,0,3,3],
 [3,3,0,0,0,0,2,2,0,0,2,2,0,0,3,3],
 [3,3,0,0,2,2,0,0,2,2,0,0,0,0,3,3],
 [3,3,0,0,2,2,0,0,2,2,0,0,0,0,3,3],
 [3,3,0,0,0,0,0,0,0,0,0,0,0,0,3,3],
 [3,3,0,0,0,0,0,0,0,0,0,0,0,0,3,3],
 [0,0,3,3,3,3,3,3,3,3,3,3,3,3,0,0],
 [0,0,3,3,3,3,3,3,3,3,3,3,3,3,0,0],
 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]
_SUN_16 = [
 [0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0],
 [0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0],
 [0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0],
]
_CLOUD_16 = [
 [0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],
 [0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0],
 [0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0],
 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]
_RAIN_16 = [
 [0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],
 [0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [0,0,1,1,0,0,1,1,0,0,1,1,0,0,0,0],
 [0,0,1,1,0,0,1,1,0,0,1,1,0,0,0,0],
 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]
_SNOW_16 = [
 [0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],
 [0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,3,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,3,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [0,0,2,2,3,3,0,0,3,3,0,0,2,2,0,0],
 [0,0,2,2,3,3,0,0,3,3,0,0,2,2,0,0],
 [0,0,1,1,0,0,1,1,0,0,1,1,0,0,0,0],
 [0,0,1,1,0,0,1,1,0,0,1,1,0,0,0,0],
 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
 [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]
_THUNDER_16 = [
 [0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],
 [0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,3,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [2,3,3,3,3,3,3,3,3,3,3,3,3,3,2,2],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [0,0,2,2,3,3,3,3,3,3,3,3,2,2,0,0],
 [0,0,0,0,1,1,3,3,1,1,0,0,0,0,0,0],
 [0,0,0,0,1,1,3,3,1,1,0,0,0,0,0,0],
 [0,0,0,0,0,0,3,3,0,0,0,0,0,0,0,0],
 [0,0,0,0,0,0,3,3,0,0,0,0,0,0,0,0],
]

icon_bitmaps = {
    'rss': _RSS_16,
    'sun': _SUN_16,
    'cloud': _CLOUD_16,
    'rain': _RAIN_16,
    'snow': _SNOW_16,
    'thunder': _THUNDER_16,
}

def create_layer_binary(bitmap, v):
    h = len(bitmap)
    w = len(bitmap[0])
    binary = np.zeros((h, w), bool)
    for y in range(h):
        for x in range(w):
            if bitmap[y][x] == v:
                binary[y, x] = True
    return np.flipud(binary)

# -------------------------
# Weather map (simple)
# -------------------------
WEATHER_MAP = {
    0: ("Clear", 'sun'),
    1: ("Mainly Clear", 'sun'),
    2: ("Partly Cloudy", 'cloud'),
    3: ("Overcast", 'cloud'),
    45: ("Fog", 'cloud'),
    51: ("Drizzle", 'rain'),
    61: ("Rain", 'rain'),
    71: ("Snow", 'snow'),
    80: ("Showers", 'rain'),
    95: ("Thunderstorm", 'thunder'),
}

def get_weather_desc_and_icon(code):
    return WEATHER_MAP.get(code, ("Unknown", 'cloud'))

# -------------------------
# Fetchers
# -------------------------
def fetch_headlines(url="http://feeds.bbci.co.uk/news/rss.xml", max_items=20):
    try:
        feed = feedparser.parse(url)
        return [entry.title for entry in feed.entries[:max_items]]
    except Exception:
        return []

def fetch_weather_warsaw():
    url = ("https://api.open-meteo.com/v1/forecast?"
           "latitude=52.23&longitude=21.01&current_weather=true&timezone=Europe/Warsaw")
    try:
        resp = requests.get(url, timeout=5).json()
        cw = resp.get("current_weather", {})
        temp = cw.get("temperature")
        wind = cw.get("windspeed")
        code = cw.get("weathercode", 0)
        desc, icon = get_weather_desc_and_icon(code)
        if temp is not None and wind is not None:
            txt = f"Warsaw: {temp:.1f}°C, Wind {wind:.1f} km/h, {desc}"
        else:
            txt = f"Warsaw: {desc}"
        if len(txt) > 128:
            txt = txt[:124] + "."
        return txt, icon
    except Exception:
        return "Weather fetch error", 'cloud'

class SingleScroller:
    def __init__(self, area_width, area_height, inject_every=INJECT_EVERY, max_rss_per_fetch=MAX_RSS_PER_FETCH, speed=SCROLL_SPEED):
        self.width = area_width
        self.height = area_height
        self.inject_every = max(1, int(inject_every))
        self.max_rss_per_fetch = max_rss_per_fetch
        self.speed = speed
        self.offset = 0.0                # pixel offset into the first visual row
        self.line_h = LINE_H
        self.visible_rows = max(1, self.height // self.line_h)

        # SOURCE: only RSS items waiting to be displayed (leftmost = oldest)
        self.rows = deque()

        # VISUAL: rows currently on screen (or partially below it).
        # Items are tuples: ('rss', title, icon) or ('weather', text, icon)
        self.visual = deque()

        # producer queue & thread
        self.feed_queue = queue.Queue()
        self._stop_event = threading.Event()
        self.producer_thread = threading.Thread(target=self._producer_loop, daemon=True)
        self.producer_thread.start()

        # dedupe set only for `rows`
        self.titles = set()
        self.skip = {"no feed items", "bbc news app", "play now"}
        self.latest_weather = None

        # how many RSS rows were moved into visual since the last weather injection
        self.rss_since_weather = 0

        # reasonable capacity for rows buffer
        self.capacity = max(4, 4 * self.visible_rows + self.max_rss_per_fetch)

        # seed latest weather and initial headlines
        try:
            wtxt, wicon = fetch_weather_warsaw()
        except Exception:
            wtxt, wicon = "Weather fetch error", 'cloud'
        self.latest_weather = (wtxt, wicon)

        headlines = fetch_headlines(max_items=self.max_rss_per_fetch)
        for title in headlines[::-1]:
            if title:
                self.feed_queue.put((title, 'rss'))

    def _producer_loop(self):
        while not self._stop_event.is_set():
            # keep weather cached
            try:
                wtxt, wicon = fetch_weather_warsaw()
            except Exception:
                wtxt, wicon = "Weather fetch error", 'cloud'
            self.latest_weather = (wtxt, wicon)

            # fetch headlines and enqueue them for the main thread to drain
            headlines = fetch_headlines(max_items=self.max_rss_per_fetch)
            for title in headlines[::-1]:
                if not title:
                    continue
                self.feed_queue.put((title, 'rss'))

            time.sleep(FETCH_INTERVAL)

    def stop(self):
        self._stop_event.set()
        self.producer_thread.join(timeout=2)

    def _drain_feed_queue_to_rows(self):
        """
        Move items from feed_queue into rows (right side). Deduplicate by title.
        titles set tracks only what is in `rows`.
        """
        while not self.feed_queue.empty():
            try:
                item = self.feed_queue.get_nowait()
            except queue.Empty:
                break
            title = item[0].strip() if isinstance(item[0], str) else item[0]
            if not title or title.lower() in self.skip:
                continue
            if title in self.titles:
                # skip duplicate in rows
                continue
            self.rows.append((title, 'rss'))
            self.titles.add(title)
            # enforce capacity (drop the oldest if over)
            if len(self.rows) > self.capacity:
                old = self.rows.popleft()
                self.titles.discard(old[0] if isinstance(old[0], str) else old[0])

    def _ensure_visual_filled(self):
        """
        Fill `visual` so the area below the current offset is covered.
        Insert weather after every self.inject_every RSS entries that are moved into visual.
        """
        current_h = len(self.visual) * self.line_h - self.offset
        target_h = self.height + self.line_h  # keep one extra row beyond screen for smooth entry

        while current_h < target_h:
            # If it's time for weather (after inject_every RSS moved into visual)
            if self.rss_since_weather >= self.inject_every:
                if self.latest_weather is not None:
                    wtxt, wicon = self.latest_weather
                    self.visual.append(('weather', wtxt, wicon))
                else:
                    self.visual.append(('weather', "Weather", 'cloud'))
                self.rss_since_weather = 0
                current_h += self.line_h
                continue

            # Prefer to take one RSS from rows (source) if available
            if len(self.rows) > 0:
                title, kind = self.rows.popleft()
                if isinstance(title, str):
                    # title lived in rows -> remove from dedupe set
                    self.titles.discard(title)
                icon = 'rss'
                self.visual.append(('rss', title, icon))
                self.rss_since_weather += 1
                current_h += self.line_h
                continue

            # No RSS in rows: if producer is idle, re-seed rows from visual's rss (cyclic repeat)
            if self.feed_queue.empty():
                rss_from_visual = [v for v in self.visual if v[0] == 'rss']
                if len(rss_from_visual) > 0:
                    # copy them back into rows so the stream repeats
                    for (_, title, _) in rss_from_visual:
                        self.rows.append((title, 'rss'))
                        self.titles.add(title)
                    # loop will then consume from rows in next iteration
                    continue
                else:
                    # no rss anywhere -> insert placeholder
                    self.visual.append(('rss', 'no feed items', 'rss'))
                    current_h += self.line_h
                    continue

            # producer has items pending - drain them into rows then loop
            self._drain_feed_queue_to_rows()
            if len(self.rows) == 0:
                # nothing available after draining - break to avoid busy-loop
                break

    def update(self, dt):
        """
        Advance offset, pop fully scrolled rows from visual, and refill visual from rows.
        """
        # first bring producer items into rows buffer
        self._drain_feed_queue_to_rows()

        # initial fill if visual empty
        if len(self.visual) == 0:
            self._ensure_visual_filled()

        # advance if we have content
        if len(self.visual) * self.line_h > 0:
            self.offset += self.speed * dt

        # pop rows that fully scrolled off the top
        while self.offset >= self.line_h and len(self.visual) > 0:
            popped = self.visual.popleft()
            # popped rss/weather simply leave visual — rows were already removed earlier
            self.offset -= self.line_h

        # refill bottom as needed (and possibly inject weather)
        self._ensure_visual_filled()

    def render(self, glyph_uvs_main, atlas_size_main, sdf_prog, quad_vao, render_sdf_text):
        line_h = self.line_h
        offset = self.offset

        total_h = len(self.visual) * line_h
        # if visual shorter than screen, anchor to top (don't shift)
        base_offset = offset if total_h > self.height else 0.0

        for idx, item in enumerate(self.visual):
            y_pos = idx * line_h - base_offset

            # stop when beyond screen
            if y_pos > HEIGHT:
                break

            kind, text, icon = item[0], item[1], item[2]

            # --- render icon layers if present ---
            if icon in ICON_LAYER_COLORS:
                for v, col in ICON_LAYER_COLORS[icon].items():
                    icon_key = 'icon:' + icon + ':' + str(v)
                    if icon_key in glyph_uvs_main:
                        u1, v1, u2, v2 = glyph_uvs_main[icon_key]
                        icon_h = int((v2 - v1) * atlas_size_main)
                        icon_y = y_pos + (line_h - icon_h) / 2.0
                        sdf_prog['position'].value = (CLOCK_W + LEFT_PAD, icon_y)
                        sdf_prog['size'].value = (ICON_SIZE, ICON_SIZE)
                        sdf_prog['uv_offset'].value = (u1, v1)
                        sdf_prog['uv_size'].value = (u2 - u1, v2 - v1)
                        sdf_prog['text_color'].value = (col[0], col[1], col[2], 1.0)
                        sdf_prog['glow_color'].value = (col[0], col[1], col[2], 0.35)
                        sdf_prog['threshold'].value = 0.5
                        sdf_prog['edge'].value = 0.02
                        sdf_prog['glow_size'].value = 0.12
                        quad_vao.render(moderngl.TRIANGLE_STRIP)
            else:
                icon_key = 'icon:' + icon
                if icon_key in glyph_uvs_main:
                    u1, v1, u2, v2 = glyph_uvs_main[icon_key]
                    icon_h = int((v2 - v1) * atlas_size_main)
                    icon_y = y_pos + (line_h - icon_h) / 2.0
                    sdf_prog['position'].value = (CLOCK_W + LEFT_PAD, icon_y)
                    sdf_prog['size'].value = (ICON_SIZE, ICON_SIZE)
                    sdf_prog['uv_offset'].value = (u1, v1)
                    sdf_prog['uv_size'].value = (u2 - u1, v2 - v1)
                    sdf_prog['text_color'].value = (ICON_COLORS.get(icon, COLOR_WHITE)[0],
                                                    ICON_COLORS.get(icon, COLOR_WHITE)[1],
                                                    ICON_COLORS.get(icon, COLOR_WHITE)[2], 1.0)
                    sdf_prog['glow_color'].value = (ICON_COLORS.get(icon, COLOR_WHITE)[0],
                                                    ICON_COLORS.get(icon, COLOR_WHITE)[1],
                                                    ICON_COLORS.get(icon, COLOR_WHITE)[2], 0.35)
                    sdf_prog['threshold'].value = 0.5
                    sdf_prog['edge'].value = 0.02
                    sdf_prog['glow_size'].value = 0.12
                    quad_vao.render(moderngl.TRIANGLE_STRIP)

            # --- render text ---
            txt_x = CLOCK_W + LEFT_PAD + ICON_SIZE + GAP_ICON_TEXT
            text_to_draw = text if len(text) <= MAX_TEXT_CHARS else text[:MAX_TEXT_CHARS - 1] + '…'
            render_sdf_text(text_to_draw, txt_x, y_pos + ROW_PADDING_Y, font_h=FONT_SIZE,
                            text_color=(1.0, 1.0, 1.0, 1.0),
                            glow_color=(0.9, 0.8, 0.4, 0.12))

# -------------------------
# Tesseract (enhanced)
# -------------------------
class Tesseract:
    def __init__(self, size=TESS_SIZE, change_interval=TESS_CHANGE_INTERVAL, rot_speed=TESS_ROT_SPEED):
        self.size = size
        self.scale = float(size) / 4.0
        self.change_interval = change_interval
        self.rot_speed = rot_speed
        self.camera4 = 4.0
        self.camera3 = 4.0
        self._eps = 0.1
        self.planes = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]
        self.plane = random.choice(self.planes)
        self.last_change = time.time()
        self.vertices = [[float(x), float(y), float(z), float(w)]
                         for x in (-1.0,1.0) for y in (-1.0,1.0) for z in (-1.0,1.0) for w in (-1.0,1.0)]
        self.edges = []
        for i in range(len(self.vertices)):
            for j in range(i+1, len(self.vertices)):
                diff = sum(abs(self.vertices[i][k] - self.vertices[j][k]) for k in range(4))
                if abs(diff - 2.0) < 1e-6:
                    self.edges.append((i,j))

    def rotate(self, plane, dangle):
        c = math.cos(dangle)
        s = math.sin(dangle)
        i, j = plane
        for v in self.vertices:
            vi = v[i]
            vj = v[j]
            v[i] = vi * c - vj * s
            v[j] = vi * s + vj * c

    def project_4d_to_3d(self, v):
        denom = self.camera4 - v[3]
        if denom < self._eps:
            denom = self._eps
        factor = self.camera4 / denom
        return [v[0]*factor, v[1]*factor, v[2]*factor]

    def project_3d_to_2d(self, p):
        denom = self.camera3 - p[2]
        if denom < self._eps:
            denom = self._eps
        factor = self.camera3 / denom
        return [p[0]*factor, p[1]*factor]

    def update(self, dt):
        self.rotate(self.plane, self.rot_speed * dt)
        if time.time() - self.last_change > self.change_interval:
            self.plane = random.choice(self.planes)
            self.last_change = time.time()

    def render(self, ctx, line_prog):
        proj3ds = [self.project_4d_to_3d(v) for v in self.vertices]
        proj2ds = [self.project_3d_to_2d(p) for p in proj3ds]

        shadow_line_vertices = []
        main_line_vertices_outer = []
        main_line_vertices_inner = []
        for i, j in self.edges:
            p1 = proj2ds[i]
            p2 = proj2ds[j]
            x1 = TESS_X + p1[0] * self.scale
            y1 = TESS_Y + p1[1] * self.scale
            x2 = TESS_X + p2[0] * self.scale
            y2 = TESS_Y + p2[1] * self.scale
            shadow_line_vertices.extend([x1 + 2.0, y1 + 2.0, x2 + 2.0, y2 + 2.0])
            w_avg = (self.vertices[i][3] + self.vertices[j][3]) / 2.0
            if w_avg >= 0.0:
                main_line_vertices_outer.extend([x1, y1, x2, y2])
            else:
                main_line_vertices_inner.extend([x1, y1, x2, y2])

        if len(shadow_line_vertices) > 0:
            svbo = ctx.buffer(np.array(shadow_line_vertices, 'f4').tobytes())
            sva = ctx.vertex_array(line_prog, svbo, 'in_pos')
            line_prog['line_color'].value = (0.04, 0.04, 0.04, 0.95)
            ctx.line_width = 3.0
            sva.render(moderngl.LINES)
            sva.release()
            svbo.release()

        if len(main_line_vertices_outer) > 0:
            ovbo = ctx.buffer(np.array(main_line_vertices_outer, 'f4').tobytes())
            ova = ctx.vertex_array(line_prog, ovbo, 'in_pos')
            line_prog['line_color'].value = (1.0, 0.76, 0.18, 1.0)
            ctx.line_width = 1.6
            ova.render(moderngl.LINES)
            ova.release()
            ovbo.release()

        if len(main_line_vertices_inner) > 0:
            ivbo = ctx.buffer(np.array(main_line_vertices_inner, 'f4').tobytes())
            iva = ctx.vertex_array(line_prog, ivbo, 'in_pos')
            line_prog['line_color'].value = (0.78, 0.9, 1.0, 1.0)
            ctx.line_width = 1.6
            iva.render(moderngl.LINES)
            iva.release()
            ivbo.release()

    def dim(self, ctx, dim_prog, quad_vbo):
        dim_prog['position'].value = (TESS_X - TESS_SIZE * 0.75, TESS_Y - TESS_SIZE * 0.75)
        dim_prog['size'].value = (TESS_SIZE * 1.5, TESS_SIZE * 1.5)
        # Use black with moderate alpha to darken but not hide the content behind.
        # Recommended alpha range: 0.30 .. 0.55; I used 0.45 as a balanced default.
        dim_prog['dim_color'].value = (0.0, 0.0, 0.0, 0.30)
        dim_vao = ctx.vertex_array(dim_prog, quad_vbo, 'in_pos')
        dim_vao.render(moderngl.TRIANGLE_STRIP)
        dim_vao.release()

# -------------------------
# Particles (decorative)
# -------------------------
class Particle:
    def __init__(self):
        self.pos = [random.uniform(0, WIDTH), random.uniform(0, HEIGHT)]
        self.vel = [random.uniform(-PARTICLE_SPEED, PARTICLE_SPEED), random.uniform(-PARTICLE_SPEED, PARTICLE_SPEED)]
        self.size = random.uniform(1.0, 3.0)
        self.color = (random.uniform(0.6, 1.0), random.uniform(0.6, 1.0), random.uniform(0.6, 1.0), 0.35)

particles = [Particle() for _ in range(PARTICLE_COUNT)]

def update_particles(dt):
    for p in particles:
        p.pos[0] += p.vel[0] * dt
        p.pos[1] += p.vel[1] * dt
        if p.pos[0] < 0 or p.pos[0] > WIDTH:
            p.vel[0] = -p.vel[0]
        if p.pos[1] < 0 or p.pos[1] > HEIGHT:
            p.vel[1] = -p.vel[1]

# -------------------------
# Build SDF atlas (glyphs + icons)
# -------------------------
def build_sdf_atlas(font_size):
    pygame.font.init()
    font = pygame.font.SysFont("dejavusans", font_size)
    glyph_widths = {}
    glyph_uvs = {}

    atlas_size = 1024
    atlas_binary = np.zeros((atlas_size, atlas_size), dtype=bool)
    cur_x = 0
    cur_y = 0
    max_h = 0

    # character set
    chars = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~°C"

    for c in chars:
        surf = font.render(c, True, (255,255,255))
        surf = surf.convert_alpha()
        try:
            alpha = pygame.surfarray.pixels_alpha(surf)  # <- use alpha to avoid white rects
            arr2 = np.flipud(alpha.T > 0)
        except Exception:
            arr3 = pygame.surfarray.array3d(surf)
            arr2 = np.flipud(arr3[:,:,0].T > 0)

        h = arr2.shape[0]
        w = arr2.shape[1]
        if w == 0 or h == 0:
            glyph_widths[c] = font_size // 2
            glyph_uvs[c] = (0.0, 0.0, 0.0, 0.0)
            continue

        if cur_x + w > atlas_size:
            cur_x = 0
            cur_y += max_h
            max_h = 0
        if cur_y + h > atlas_size:
            raise RuntimeError("Atlas too small for glyphs")

        atlas_binary[cur_y:cur_y+h, cur_x:cur_x+w] = arr2
        u1, v1 = cur_x / atlas_size, cur_y / atlas_size
        u2, v2 = (cur_x + w) / atlas_size, (cur_y + h) / atlas_size
        glyph_uvs[c] = (u1, v1, u2, v2)
        glyph_widths[c] = w
        max_h = max(max_h, h)
        cur_x += w

    # add icon layers into atlas
    for name, bitmap in icon_bitmaps.items():
        unique_vals = sorted({v for row in bitmap for v in row if v > 0})
        h = len(bitmap)
        w = len(bitmap[0])
        for v in unique_vals:
            binary = create_layer_binary(bitmap, v)
            if cur_x + w > atlas_size:
                cur_x = 0
                cur_y += max_h
                max_h = 0
            if cur_y + h > atlas_size:
                raise RuntimeError("Atlas too small for icons")
            atlas_binary[cur_y:cur_y+h, cur_x:cur_x+w] = binary
            u1, v1 = cur_x / atlas_size, cur_y / atlas_size
            u2, v2 = (cur_x + w) / atlas_size, (cur_y + h) / atlas_size
            key = 'icon:' + name + ('' if len(unique_vals) == 1 else ':' + str(v))
            glyph_uvs[key] = (u1, v1, u2, v2)
            glyph_widths[key] = w
            max_h = max(max_h, h)
            cur_x += w

    # compute SDF
    dist_inside = edt(atlas_binary)
    dist_outside = edt(~atlas_binary)
    sdf = dist_inside - dist_outside
    max_d = max(8, font_size // 2)
    sdf_norm = (sdf / (2.0 * max_d) + 0.5).clip(0.0, 1.0)
    sdf_data = (sdf_norm * 255.0).astype('u1')
    return sdf_data, atlas_size, glyph_uvs, glyph_widths

# -------------------------
# Moderngl shader sources
# -------------------------
VERT_SDF = '''
#version 300 es
precision mediump float;

in vec2 in_pos;
in vec2 in_uv;
out vec2 frag_uv;
uniform mat4 mvp;
uniform vec2 position;
uniform vec2 size;
uniform vec2 uv_offset;
uniform vec2 uv_size;
void main() {
    vec2 p = in_pos * size + position;
    gl_Position = mvp * vec4(p, 0.0, 1.0);
    frag_uv = in_uv * uv_size + uv_offset;
}
'''
FRAG_SDF = '''
#version 300 es
precision mediump float;

in vec2 frag_uv;
out vec4 fragColor;
uniform sampler2D tex;
uniform vec4 text_color;
uniform vec4 glow_color;
uniform float threshold;
uniform float edge;
uniform float glow_size;
void main() {
    float d = texture(tex, frag_uv).r;
    float base = smoothstep(threshold - edge, threshold + edge, d);
    float glow = smoothstep(threshold - glow_size, threshold, d) * glow_color.a;
    vec3 color = text_color.rgb * base + glow_color.rgb * glow;
    float alpha = clamp(text_color.a * base + glow_color.a * glow, 0.0, 1.0);
    if (alpha < 0.01) discard;
    fragColor = vec4(color, alpha);
}
'''

VERT_LINE = '''
#version 300 es
precision mediump float;

in vec2 in_pos;
uniform mat4 mvp;
void main() {
    gl_Position = mvp * vec4(in_pos, 0.0, 1.0);
}
'''
FRAG_LINE = '''
#version 300 es
precision mediump float;

uniform vec4 line_color;
out vec4 fragColor;
void main() { fragColor = line_color; }
'''

VERT_RADIAL = '''
#version 300 es
precision mediump float;

in vec2 in_pos;
out vec2 frag_pos;
uniform mat4 mvp;
uniform vec2 position;
uniform vec2 size;
void main() {
    vec2 p = in_pos * size + position;
    gl_Position = mvp * vec4(p, 0.0, 1.0);
    frag_pos = p;
}
'''
FRAG_RADIAL = '''
#version 300 es
precision mediump float;

in vec2 frag_pos;
out vec4 fragColor;
uniform vec2 center;
uniform float radius;
uniform vec4 color1;
uniform vec4 color2;
void main() {
    float d = length(frag_pos - center) / radius;
    if (d > 1.0) discard;
    fragColor = mix(color1, color2, d);
}
'''

VERT_PART = '''
#version 300 es
precision mediump float;

in vec2 in_pos;
uniform mat4 mvp;
uniform float size;
void main() {
    gl_Position = mvp * vec4(in_pos, 0.0, 1.0);
    gl_PointSize = size;
}
'''
FRAG_PART = '''
#version 300 es
precision mediump float;

uniform vec4 p_color;
out vec4 fragColor;
void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    float alpha = 1.0 - smoothstep(0.4, 0.6, dist);
    fragColor = p_color * alpha;
}
'''

VERT_DIM = '''
#version 300 es
precision mediump float;

in vec2 in_pos;
uniform mat4 mvp;
uniform vec2 position;
uniform vec2 size;
void main() {
    vec2 p = in_pos * size + position;
    gl_Position = mvp * vec4(p, 0.0, 1.0);
}
'''
FRAG_DIM = '''
#version 300 es
precision mediump float;

uniform vec4 dim_color;
out vec4 fragColor;
void main() {
    fragColor = dim_color;
}
'''

VERT_DIM_CIRC = '''
#version 300 es
precision mediump float;

in vec2 in_pos;
uniform mat4 mvp;
uniform vec2 position;
uniform vec2 size;
out vec2 texCoord;
void main() {
    vec2 p = in_pos * size + position;
    gl_Position = mvp * vec4(p, 0.0, 1.0);
    texCoord = in_pos;
}
'''
FRAG_DIM_CIRC = '''
#version 300 es
precision mediump float;

uniform vec4 dim_color;
uniform vec2 size;
in vec2 texCoord;
out vec4 fragColor;
void main() {
    vec2 center = vec2(0.5, 0.5);
    vec2 delta = texCoord - center;
    vec2 delta_world = delta * size;
    float dist = length(delta_world);
    float radius = min(size.x, size.y) * 0.5;
    if (dist > radius) {
        discard;
    } else {
        fragColor = dim_color;
    }
}
'''

FRAG_CIRCLE = '''
#version 300 es
precision mediump float;

in vec2 frag_pos;
out vec4 fragColor;

uniform vec4 solid_color;
uniform vec2 center;
uniform float radius;

void main() {
    float dist = distance(frag_pos, center);
    if (dist <= radius) {
        fragColor = solid_color;
    } else {
        discard;
    }
}
'''

VERT_CIRCLE = '''
#version 300 es
precision mediump float;

in vec2 in_pos;
out vec2 frag_pos;
uniform mat4 mvp;
uniform vec2 position;
uniform vec2 size;
void main() {
    vec2 p = in_pos * size + position;
    gl_Position = mvp * vec4(p, 0.0, 1.0);
    frag_pos = p;
}
'''
VERT_SIMPLE = '''
#version 300 es
precision mediump float;

in vec2 in_pos;
in vec4 in_color;
out vec4 v_color;
void main() {
    gl_Position = vec4(in_pos, 0.0, 1.0);  // Adjust projection if needed
    v_color = in_color;
}
'''
FRAG_SIMPLE = '''
#version 300 es
precision mediump float;

in vec4 v_color;
out vec4 fragColor;
void main() {
    fragColor = v_color;
}
'''

VERT_WALL = """
    #version 300 es
    precision mediump float;

    in vec2 in_pos;
    out vec2 uv;
    
    void main() {
        uv = (in_pos + 1.0) * 0.5;   // map [-1,1] → [0,1]
        gl_Position = vec4(in_pos, 0.0, 1.0);
    }
"""

FRAG_WALL = """
    #version 300 es
    precision mediump float;

    in vec2 uv;
    uniform sampler2D wall_tex;
    out vec4 fragColor;
    
    void main() {
        fragColor = texture(wall_tex, uv);
    }
"""

# -------------------------
# Utility: text rendering & pixel width
# -------------------------
# These will be created after atlas build in main() because they need glyph_uvs/glyph_widths

def get_display_index(display_name):
    """Return the Pygame display index for the given display name using wlr-randr."""
    while True:
        try:
            result = subprocess.run(['wlr-randr'], capture_output=True, text=True, check=True)
            lines = result.stdout.splitlines()
            index = 0
            for line in lines:
                lstripped = line.strip()
                if lstripped and not line.startswith(' '):
                    if lstripped.startswith(display_name):
                        print(f"Display {display_name} found on index {index}.")
                        return index
                index += 1
            print(f"Display {display_name} not found")
            sleep(1)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"Error running wlr-randr.")

# Set SDL/pygame environment variables BEFORE importing pygame/initializing SDL
# Use wayland backend and instruct SDL which display index should be used for fullscreen
display_index = get_display_index("HDMI-A-1")
os.environ.setdefault("SDL_VIDEODRIVER", "wayland")
os.environ["SDL_VIDEO_FULLSCREEN_DISPLAY"] = str(display_index)
os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"

# Now import pygame and create fullscreen window on the chosen display
import pygame
from pygame.locals import *

pygame.init()

# -------------------------
# Main program
# -------------------------
def main():
    pygame.font.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 0)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
    # pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    screen = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL | FULLSCREEN, display=display_index)
    ctx = moderngl.create_context(require=300)

    ctx.enable(moderngl.PROGRAM_POINT_SIZE)
    ctx.enable(moderngl.BLEND)
    try:
        ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
    except Exception:
        pass

    # Load wallpaper (1600x900)
    wall_img = Image.open("/home/adamh/bin/forest-3804001-1920.jpg").convert("RGB")
    wall_img = wall_img.transpose(Image.FLIP_TOP_BOTTOM)  # flip vertically
    tex_wall = ctx.texture(wall_img.size, 3, wall_img.tobytes())
    tex_wall.build_mipmaps()
    # Enable mipmapped filtering for nice downscaling
    tex_wall.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
    tex_wall.use(location=0)

    # MVP matrix mapping pixel coords to NDC
    mvp = np.array([
        [2.0 / WIDTH, 0.0, 0.0, 0.0],
        [0.0, -2.0 / HEIGHT, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [-1.0, 1.0, 0.0, 1.0]
    ], dtype='f4')

    # Build two atlases: main (with icons) and tiny (glyphs only) for subdials
    sdf_data_main, atlas_size_main, glyph_uvs_main, glyph_widths_main = build_sdf_atlas(FONT_SIZE)
    sdf_data_tiny, atlas_size_tiny, glyph_uvs_tiny, glyph_widths_tiny = build_sdf_atlas(TINY_FONT_SIZE)

    tex_main = ctx.texture((atlas_size_main,atlas_size_main),1,data=sdf_data_main.tobytes())
    tex_main.filter=(moderngl.LINEAR,moderngl.LINEAR)
    tex_tiny = ctx.texture((atlas_size_tiny,atlas_size_tiny),1,data=sdf_data_tiny.tobytes())
    tex_tiny.filter=(moderngl.LINEAR,moderngl.LINEAR)

    # compile programs
    sdf_prog = ctx.program(vertex_shader=VERT_SDF, fragment_shader=FRAG_SDF)
    sdf_prog['mvp'].value = tuple(mvp.flatten())

    line_prog = ctx.program(vertex_shader=VERT_LINE, fragment_shader=FRAG_LINE)
    line_prog['mvp'].value = tuple(mvp.flatten())

    radial_prog = ctx.program(vertex_shader=VERT_RADIAL, fragment_shader=FRAG_RADIAL)
    radial_prog['mvp'].value = tuple(mvp.flatten())

    circle_prog = ctx.program(vertex_shader=VERT_CIRCLE, fragment_shader=FRAG_CIRCLE)
    circle_prog['mvp'].value = tuple(mvp.flatten())

    simple_prog = ctx.program(vertex_shader=VERT_SIMPLE, fragment_shader=FRAG_SIMPLE)
    # simple_prog['mvp'].value = tuple(mvp.flatten())

    particle_prog = ctx.program(vertex_shader=VERT_PART, fragment_shader=FRAG_PART)
    particle_prog['mvp'].value = tuple(mvp.flatten())

    dim_prog = ctx.program(vertex_shader=VERT_DIM, fragment_shader=FRAG_DIM)
    dim_prog['mvp'].value = tuple(mvp.flatten())

    dim_prog_circ = ctx.program(vertex_shader=VERT_DIM_CIRC, fragment_shader=FRAG_DIM_CIRC)
    dim_prog_circ['mvp'].value = tuple(mvp.flatten())

    wall_prog = ctx.program(vertex_shader=VERT_WALL, fragment_shader=FRAG_WALL)

    # Fullscreen quad VBO (two triangles forming [-1,-1] to [1,1])
    quad_vbo_wall = ctx.buffer(
        np.array([
            -1.0, -1.0,
            1.0, -1.0,
            -1.0, 1.0,
            1.0, 1.0
        ], dtype='f4').tobytes()
    )

    # quad data (pos, uv)
    quad_data = np.array([
        0.0, 0.0, 0.0, 1.0,
        1.0, 0.0, 1.0, 1.0,
        0.0, 1.0, 0.0, 0.0,
        1.0, 1.0, 1.0, 0.0,
    ], dtype='f4')
    quad_vbo = ctx.buffer(quad_data.tobytes())
    quad_vao = ctx.vertex_array(sdf_prog, quad_vbo, 'in_pos', 'in_uv')

    # helper arrays/buffers
    particle_vbo = ctx.buffer(reserve=PARTICLE_COUNT * 8, dynamic=True)
    particle_vao = ctx.vertex_array(particle_prog, particle_vbo, 'in_pos')

    # scroller and tesseract
    scroller = SingleScroller(FEED_W, SCROLL_H)
    tesseract = Tesseract()

    # helper functions (now we have glyph_uvs/glyph_widths)
    def text_pixel_width(text, font_h=FONT_SIZE):
        """Return pixel width for text when rendered at font_h by selecting the correct atlas."""
        if font_h<=TINY_FONT_SIZE:
            gw=glyph_widths_tiny
            scale=float(font_h)/float(TINY_FONT_SIZE) if TINY_FONT_SIZE>0 else 1.0
        else:
            gw=glyph_widths_main
            scale=float(font_h)/float(FONT_SIZE) if FONT_SIZE>0 else 1.0
        total=0
        for ch in text:
            w=gw.get(ch,FONT_SIZE//2)
            total+=max(1,int(round(w*scale)))
        return total

    def render_sdf_text(text, px, py, font_h=FONT_SIZE, text_color=(1.0,1.0,1.0,1.0), glow_color=(1.0,0.85,0.35,0.14)):
        """Render text using SDF atlas scaled to font_h. Chooses tiny atlas when font_h <= TINY_FONT_SIZE."""
        cur_x=px
        if font_h<=TINY_FONT_SIZE:
            gu=glyph_uvs_tiny; gw=glyph_widths_tiny; tex_use=tex_tiny; scale=float(font_h)/float(TINY_FONT_SIZE) if TINY_FONT_SIZE>0 else 1.0
        else:
            gu=glyph_uvs_main; gw=glyph_widths_main; tex_use=tex_main; scale=float(font_h)/float(FONT_SIZE) if FONT_SIZE>0 else 1.0
        tex_use.use(location=0)
        for ch in text:
            if ch not in gu:
                cur_x+=gw.get(ch,font_h//2)
                continue
            u1,v1,u2,v2=gu[ch]
            w_atlas=gw.get(ch,font_h//2)
            w_scaled=max(1,int(round(w_atlas*scale)))
            sdf_prog['position'].value=(cur_x,py)
            sdf_prog['size'].value=(w_scaled,font_h)
            sdf_prog['uv_offset'].value=(u1,v1)
            sdf_prog['uv_size'].value=(u2-u1,v2-v1)
            sdf_prog['text_color'].value=text_color
            sdf_prog['glow_color'].value=glow_color
            sdf_prog['threshold'].value=0.5
            sdf_prog['edge'].value=0.02
            sdf_prog['glow_size'].value=0.10
            quad_vao.render(moderngl.TRIANGLE_STRIP)
            cur_x+=w_scaled

    # -------------------------
    # Draw Subdial with ticks + label above pivot
    # -------------------------
    def draw_subdial(ctx, line_prog, radial_prog, quad_vbo, text_pixel_width, render_sdf_text,
                     center_x, center_y, radius, tz_label, tz_name, now_t):

        try:
            dt_utc = datetime.fromtimestamp(now_t, timezone.utc)
            dt_tz = dt_utc.astimezone(ZoneInfo(tz_name))
            hour = dt_tz.hour % 12 + dt_tz.minute / 60.0 + dt_tz.second / 3600.0
            minute = dt_tz.minute + dt_tz.second / 60.0
        except Exception as e:
            print(e)
            t = time.localtime(now_t)
            hour = t.tm_hour % 12 + t.tm_min / 60.0
            minute = t.tm_min + t.tm_sec / 60.0

        # solid, slightly larger circle
        border_width = 0.02
        circle_prog['position'].value = (center_x - radius - border_width - 1, center_y - radius - border_width - 1)
        circle_prog['size'].value = (2.0 * (radius + border_width) + 2, 2.0 * (radius + border_width) + 2)
        circle_prog['center'].value = (center_x, center_y)
        circle_prog['radius'].value = radius + 1
        circle_prog['solid_color'].value = (0.5, 0.8, 1.0, 1.0) #(0.0, 0.0, 0.5, 1.0)
        vao = ctx.vertex_array(circle_prog, quad_vbo, 'in_pos')
        vao.render(moderngl.TRIANGLE_STRIP)
        vao.release()

        # face
        radial_prog['position'].value = (center_x - radius, center_y - radius)
        radial_prog['size'].value = (2 * radius, 2 * radius)
        radial_prog['center'].value = (center_x, center_y)
        radial_prog['radius'].value = radius
        radial_prog['color1'].value = (0.08, 0.08, 0.1, 1.0)
        radial_prog['color2'].value = (0.15, 0.15, 0.2, 1.0)
        vao = ctx.vertex_array(radial_prog, quad_vbo, 'in_pos')
        vao.render(moderngl.TRIANGLE_STRIP)
        vao.release()

        # label ABOVE pivot
        lbl_w = text_pixel_width(tz_label, font_h=TINY_FONT_SIZE)
        render_sdf_text(tz_label, center_x - lbl_w / 2, center_y - TINY_FONT_SIZE - 2,
                        font_h=TINY_FONT_SIZE, text_color=(0.3, 0.6, 0.3, 1.0), glow_color=(0.3, 0.6, 0.3, 1.0))

        # ticks
        tick_vertices = []
        for i in range(12):
            angle = math.radians(i * 30 - 90)
            inner = radius - 3
            outer = radius
            x1, y1 = center_x + inner * math.cos(angle), center_y + inner * math.sin(angle)
            x2, y2 = center_x + outer * math.cos(angle), center_y + outer * math.sin(angle)
            tick_vertices.extend([x1, y1, x2, y2])
        tick_vbo = ctx.buffer(np.array(tick_vertices, 'f4').tobytes())
        tick_vao = ctx.vertex_array(line_prog, tick_vbo, 'in_pos')
        line_prog['line_color'].value = (0.8, 0.8, 0.8, 1.0)
        ctx.line_width = 1.0
        tick_vao.render(moderngl.LINES)
        tick_vao.release()
        tick_vbo.release()

        # hands (subdial) — keep as lines (unchanged)
        hour_ang = math.radians(hour * 30 - 90)
        min_ang = math.radians(minute * 6 - 90)
        hx, hy = center_x + (radius * 0.55) * math.cos(hour_ang), center_y + (radius * 0.55) * math.sin(hour_ang)
        mx, my = center_x + (radius * 0.8) * math.cos(min_ang), center_y + (radius * 0.8) * math.sin(min_ang)

        hv = np.array([center_x, center_y, hx, hy], 'f4')
        hvbo = ctx.buffer(hv.tobytes())
        hvao = ctx.vertex_array(line_prog, hvbo, 'in_pos')
        line_prog['line_color'].value = (0.5, 0.8, 1.0, 1.0)
        ctx.line_width = 3.0
        hvao.render(moderngl.LINES)
        hvao.release()
        hvbo.release()

        mv = np.array([center_x, center_y, mx, my], 'f4')
        mvbo = ctx.buffer(mv.tobytes())
        mvao = ctx.vertex_array(line_prog, mvbo, 'in_pos')
        line_prog['line_color'].value = (0.5, 0.8, 1.0, 1.0)
        ctx.line_width = 2.0
        mvao.render(moderngl.LINES)
        mvao.release()
        mvbo.release()

    def draw_clock(now_t):
        r =  CLOCK_W * 0.5
        cx = r + 10
        cy = r + 10

        # solid, slightly larger circle
        border_width = 0.05
        circle_prog['position'].value = (cx - r - border_width - 4, cy - r - border_width - 4)
        circle_prog['size'].value = (2.0 * (r + border_width) + 8, 2.0 * (r + border_width) + 8)
        circle_prog['center'].value = (cx, cy)
        circle_prog['radius'].value = r + 4
        circle_prog['solid_color'].value = (0.0, 0.0, 0.5, 1.0)  # Dark blue color
        vao = ctx.vertex_array(circle_prog, quad_vbo, 'in_pos')
        vao.render(moderngl.TRIANGLE_STRIP)
        vao.release()

        # face gradient
        radial_prog['position'].value = (cx - r, cy - r)
        radial_prog['size'].value = (2 * r, 2 * r)
        radial_prog['center'].value = (cx, cy)
        radial_prog['radius'].value = r
        radial_prog['color1'].value = (0.03, 0.03, 0.06, 1.0)
        radial_prog['color2'].value = (0.05, 0.18, 0.16, 1.0)
        vao = ctx.vertex_array(radial_prog, quad_vbo, 'in_pos')
        vao.render(moderngl.TRIANGLE_STRIP)
        vao.release()

        # face radial
        radial_prog['position'].value = (cx - r, cy - r)
        radial_prog['size'].value = (2.0 * r, 2.0 * r)
        radial_prog['center'].value = (cx, cy)
        radial_prog['radius'].value = r
        radial_prog['color1'].value = (0.03, 0.03, 0.06, 1.0)
        radial_prog['color2'].value = (0.05, 0.18, 0.16, 1.0)
        radial_vao = ctx.vertex_array(radial_prog, quad_vbo, 'in_pos')
        radial_vao.render(moderngl.TRIANGLE_STRIP)
        radial_vao.release()

        # Control Center text above pivot
        label1 = "Control"
        label2 = "Center"
        w_l1 = text_pixel_width(label1, font_h=TINY_FONT_SIZE)
        w_l2 = text_pixel_width(label2, font_h=TINY_FONT_SIZE)
        box_w = max(w_l1, w_l2)
        tx = cx - box_w / 2.0
        ty = cy - 65
        text_color = (0.3, 0.3, 0.6, 1.0)
        render_sdf_text(label1, tx + (box_w - w_l1)/2.0, ty, font_h=TINY_FONT_SIZE, text_color=text_color, glow_color=text_color)
        render_sdf_text(label2, tx + (box_w - w_l2)/2.0, ty + TINY_FONT_SIZE, font_h=TINY_FONT_SIZE, text_color=text_color, glow_color=text_color)

        # --- Subdials (RI, NV, IND) ---
        sub_r = int(r * 0.25)
        draw_subdial(ctx, line_prog, radial_prog, quad_vbo, text_pixel_width, render_sdf_text,
                     cx - r * 0.5, cy, sub_r, "RI", "America/New_York", now_t)
        draw_subdial(ctx, line_prog, radial_prog, quad_vbo, text_pixel_width, render_sdf_text,
                     cx + r * 0.5, cy, sub_r, "NV", "America/Los_Angeles", now_t)
        draw_subdial(ctx, line_prog, radial_prog, quad_vbo, text_pixel_width, render_sdf_text,
                     cx, cy + r * 0.5, sub_r, "IND", "Asia/Calcutta", now_t)

        # ticks
        tick_vertices = []
        for i in range(60):
            angle_deg = i * 6
            rad_ang = math.radians(angle_deg - 90)
            outer = r
            inner = r - (18 if i % 5 == 0 else 8)
            x1 = cx + inner * math.cos(rad_ang)
            y1 = cy + inner * math.sin(rad_ang)
            x2 = cx + outer * math.cos(rad_ang)
            y2 = cy + outer * math.sin(rad_ang)
            tick_vertices.extend([x1, y1, x2, y2])
        tick_vbo = ctx.buffer(np.array(tick_vertices, 'f4').tobytes())
        tick_vao = ctx.vertex_array(line_prog, tick_vbo, 'in_pos')
        line_prog['line_color'].value = (0.85, 0.85, 0.85, 1.0)
        ctx.line_width = 1.4
        tick_vao.render(moderngl.LINES)
        tick_vao.release()
        tick_vbo.release()

        # hour labels: 12, 3, 6, 9
        hour_labels = [
            ("12", 0),
            ("3", 90),
            ("6", 180),
            ("9", 270)
        ]
        label_radius = r - 20
        label_font_h = SMALL_FONT_SIZE
        for txt, angle_deg in hour_labels:
            rad = math.radians(angle_deg - 90)
            label_cx = cx + label_radius * math.cos(rad)
            label_cy = cy + label_radius * math.sin(rad)
            w = text_pixel_width(txt, font_h=label_font_h)
            tx = label_cx - w / 2.0
            ty = label_cy - label_font_h / 2.0
            render_sdf_text(txt, tx, ty, font_h=label_font_h, text_color=(1.0,1.0,1.0,1.0), glow_color=(1.0,0.85,0.35,0.14))

        # hands: compute angles
        dt_utc = datetime.fromtimestamp(now_t, timezone.utc)
        # main (Warsaw) local time - use ZoneInfo
        try:
            dt_local = dt_utc.astimezone(ZoneInfo("Europe/Warsaw"))
            frac_sec = dt_local.second % 60
            minute = dt_local.minute + frac_sec / 60.0
            hour = (dt_local.hour % 12) + minute / 60.0
            day_angle = int(dt_local.hour * 15)
        except Exception as e:
            print(e)
            tstruct = time.localtime(now_t)
            frac_sec = tstruct.tm_sec % 60
            minute = tstruct.tm_min + frac_sec / 60.0
            hour = (tstruct.tm_hour % 12) + minute / 60.0
            day_angle = int(tstruct.tm_hour * 15)

        hour_angle = hour * 30 - 90
        minute_angle = minute * 6 - 90
        second_angle = frac_sec * 6 - 90

        # drawing functions for hands
        def draw_hand(angle_deg, length_ratio, thickness, color, shadow=False):
            rad = math.radians(angle_deg)
            x_tip = cx + r * length_ratio * math.cos(rad)
            y_tip = cy + r * length_ratio * math.sin(rad)
            x_start = cx - 6 * math.cos(rad)
            y_start = cy - 6 * math.sin(rad)

            if shadow:
                ox, oy = 1.6, 1.6
            else:
                ox, oy = 0.0, 0.0
            v = np.array([x_start+ox, y_start+oy, x_tip+ox, y_tip+oy], 'f4')
            vbo = ctx.buffer(v.tobytes())
            vao = ctx.vertex_array(line_prog, vbo, 'in_pos')
            line_prog['line_color'].value = color
            ctx.line_width = thickness
            vao.render(moderngl.LINES)
            vao.release()
            vbo.release()

        def draw_diamond(angle_deg, length_ratio, base_width, color, shadow=False):
            """
            Draws a simple 3D-style diamond clock hand using two triangles
            """
            # ---- helper to convert pixel -> NDC ----
            def to_ndc(px, py):
                nx = (px / WIDTH) * 2.0 - 1.0
                ny = 1.0 - (py / HEIGHT) * 2.0
                return nx, ny

            # ---- basic geometry ----
            rad = math.radians(angle_deg)
            dx = math.cos(rad)
            dy = math.sin(rad)

            tip_x = cx + r * length_ratio * dx
            tip_y = cy + r * length_ratio * dy
            back_offset = max(10.0, r * 0.06)
            back_x = cx - dx * back_offset
            back_y = cy - dy * back_offset

            # Compute mid_frac to place the shared edge at the pivot (center)
            total_length = back_offset + r * length_ratio
            mid_frac = 0.1

            # waist (midpoint between back and tip)
            mid_cx = back_x + (tip_x - back_x) * mid_frac
            mid_cy = back_y + (tip_y - back_y) * mid_frac

            # perpendicular unit vector
            px_v = -dy
            py_v = dx

            half_waist = base_width / 2.0
            mid_left_x = mid_cx + px_v * half_waist
            mid_left_y = mid_cy + py_v * half_waist
            mid_right_x = mid_cx - px_v * half_waist
            mid_right_y = mid_cy - py_v * half_waist

            vertices = []

            # ---- optional shadow ----
            if shadow:
                sox, soy = 1.6, 1.6
                s_col = (0.0, 0.0, 0.0, 0.35)
                # tip triangle shadow
                for px_, py_ in [(tip_x + sox, tip_y + soy), (mid_left_x + sox, mid_left_y + soy),
                                 (mid_right_x + sox, mid_right_y + soy)]:
                    nx, ny = to_ndc(px_, py_)
                    vertices += [nx, ny, *s_col]
                # back triangle shadow
                for px_, py_ in [(back_x + sox, back_y + soy), (mid_right_x + sox, mid_right_y + soy),
                                 (mid_left_x + sox, mid_left_y + soy)]:
                    nx, ny = to_ndc(px_, py_)
                    vertices += [nx, ny, *s_col]

            # ---- fill: two triangles forming "<>" ----
            left_bias = 0.94
            right_bias = 1.02

            # tip triangle
            tri_tip = [
                (tip_x, tip_y, *color),
                (mid_left_x, mid_left_y, color[0] * left_bias, color[1] * left_bias, color[2] * left_bias, color[3]),
                (mid_right_x, mid_right_y, color[0] * right_bias, color[1] * right_bias, color[2] * right_bias, color[3])
            ]
            # back triangle
            tri_back = [
                (back_x, back_y, *color),
                (mid_right_x, mid_right_y, color[0] * right_bias, color[1] * right_bias, color[2] * right_bias, color[3]),
                (mid_left_x, mid_left_y, color[0] * left_bias, color[1] * left_bias, color[2] * left_bias, color[3])
            ]

            for ax, ay, r_, g_, b_, a_ in (tri_tip + tri_back):
                nx, ny = to_ndc(ax, ay)
                vertices += [nx, ny, r_, g_, b_, a_]

            # ---- draw fill ----
            vdata = np.array(vertices, dtype='f4')
            vbo = ctx.buffer(vdata.tobytes())
            vao = ctx.vertex_array(simple_prog, [(vbo, '2f 4f', 'in_pos', 'in_color')])
            vao.render(moderngl.TRIANGLES)
            vao.release()
            vbo.release()

            # ---- outline ----
            line_color = (0.35, 0.35, 0.35, 1.0)
            line_pts = [
                # Diamond edges: tip -> mid_right -> back -> mid_left -> tip
                (tip_x, tip_y), (mid_right_x, mid_right_y),  # Line 1: tip -> mid_right
                (mid_right_x, mid_right_y), (back_x, back_y),  # Line 2: mid_right -> back
                (back_x, back_y), (mid_left_x, mid_left_y),  # Line 3: back -> mid_left
                (mid_left_x, mid_left_y), (tip_x, tip_y),  # Line 4: mid_left -> tip
                # Central line: tip -> back
                (tip_x, tip_y), (back_x, back_y)  # Line 5: central
            ]

            line_vertices = []
            for px, py in line_pts:
                nx, ny = to_ndc(px, py)
                line_vertices += [nx, ny, *line_color]

            lvdata = np.array(line_vertices, dtype='f4')
            lvbo = ctx.buffer(lvdata.tobytes())
            lvao = ctx.vertex_array(simple_prog, [(lvbo, '2f 4f', 'in_pos', 'in_color')])
            ctx.line_width = 1.0
            lvao.render(moderngl.LINES)
            lvao.release()
            lvbo.release()

        # draw shadows (kept dark for contrast)
        main_hands_shade = (0.1, 0.1, 0.1, 0.8)
        draw_diamond(hour_angle, 0.5, 1.0, main_hands_shade, shadow=True)
        draw_diamond(minute_angle, 0.78, 1.0, main_hands_shade, shadow=True)
        draw_hand(second_angle, 0.92, 2.2, (0.02, 0.02, 0.02, 0.9), shadow=True)

        # draw actual hands (light blue gradient)
        main_hands_color = (0.1, 0.3, 1.0, 1.0)
        draw_diamond(hour_angle, 0.5, 15.0, main_hands_color)
        draw_diamond(minute_angle, 0.78, 10.0, main_hands_color)
        draw_hand(second_angle, 0.92, 1.6, (1.0, 0.15, 0.15, 1.0))

        # gray pivot dot (overlay)
        pivot_radius = 3.0
        circle_prog['position'].value = (cx - pivot_radius - 1.0, cy - pivot_radius - 1.0)
        circle_prog['size'].value = (2.0 * pivot_radius + 2.0, 2.0 * pivot_radius + 2.0)
        circle_prog['center'].value = (cx, cy)
        circle_prog['radius'].value = pivot_radius
        circle_prog['solid_color'].value = (0.55, 0.55, 0.55, 1.0)  # gray dot
        cvao = ctx.vertex_array(circle_prog, quad_vbo, 'in_pos')
        cvao.render(moderngl.TRIANGLE_STRIP)
        cvao.release()

        # outer ring subtle highlight
        ring_verts = []
        for i in range(0, day_angle, 8):
            a1 = math.radians(i - 90)
            a2 = math.radians(i + 4 - 90)
            r_out = r + 4
            x1, y1 = cx + r_out * math.cos(a1), cy + r_out * math.sin(a1)
            x2, y2 = cx + r_out * math.cos(a2), cy + r_out * math.sin(a2)
            ring_verts += [x1, y1, x2, y2]
        if len(ring_verts) > 0:
            rvbo = ctx.buffer(np.array(ring_verts, 'f4').tobytes())
            rvao = ctx.vertex_array(line_prog, rvbo, 'in_pos')
            line_prog['line_color'].value = (0.5, 0.8, 1.0, 1.0)
            ctx.line_width = 2.0
            rvao.render(moderngl.LINES)
            rvao.release()
            rvbo.release()

        ring_verts = []
        for i in range(day_angle + 1, 360, 8):
            a1 = math.radians(i - 90)
            a2 = math.radians(i + 4 - 90)
            r_out = r + 4
            x1, y1 = cx + r_out * math.cos(a1), cy + r_out * math.sin(a1)
            x2, y2 = cx + r_out * math.cos(a2), cy + r_out * math.sin(a2)
            ring_verts += [x1, y1, x2, y2]
        if len(ring_verts) > 0:
            rvbo = ctx.buffer(np.array(ring_verts, 'f4').tobytes())
            rvao = ctx.vertex_array(line_prog, rvbo, 'in_pos')
            line_prog['line_color'].value = (0.12, 0.14, 0.18, 0.9)
            ctx.line_width = 2.0
            rvao.render(moderngl.LINES)
            rvao.release()
            rvbo.release()

        # digital date/time below
        try:
            cal_text = dt_local.strftime("%a, %d-%m-%Y")
            dig_text = dt_local.strftime("%H:%M:%S")
        except Exception:
            tstruct = time.localtime(now_t)
            cal_text = time.strftime("%a, %d-%m-%Y", tstruct)
            dig_text = time.strftime("%H:%M:%S", tstruct)

        w_cal = text_pixel_width(cal_text, font_h=SMALL_FONT_SIZE)
        w_dig = text_pixel_width(dig_text, font_h=SMALL_FONT_SIZE)
        box_w = max(w_cal, w_dig)
        tx = cx - box_w / 2.0
        ty = cy + r + 15
        text_color = (0.99, 0.99, 0.99, 1.0)  # Dark blue color  ## (0.92,0.92,0.92,1.0) (0.9,0.9,0.8,0.18) (1.0,1.0,1.0,1.0) (1.0,0.85,0.4,0.25)
        render_sdf_text(cal_text, tx + (box_w - w_cal)/2.0, ty, font_h=SMALL_FONT_SIZE, text_color=text_color, glow_color=text_color)
        render_sdf_text(dig_text, tx + (box_w - w_dig)/2.0, ty + SMALL_FONT_SIZE + 6, font_h=SMALL_FONT_SIZE, text_color=text_color, glow_color=text_color)

    def draw_wallpaper():
        tex_wall.use(location=0)
        wall_vao = ctx.vertex_array(wall_prog, [(quad_vbo_wall, "2f", "in_pos")])
        wall_vao.render(moderngl.TRIANGLE_STRIP)
        wall_vao.release()

    def draw_particles():
        particle_coords = np.array([p.pos for p in particles], 'f4')
        particle_vbo.write(particle_coords.tobytes())
        for i,p in enumerate(particles):
            particle_prog['size'].value = p.size
            particle_prog['p_color'].value = p.color
            particle_vao.render(moderngl.POINTS, vertices=1, first=i)

    clock = pygame.time.Clock()
    running = True

    # main loop
    while running:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False

        now_t = time.time()
        dt = clock.get_time() / 1000.0 if clock.get_time() > 0 else 1.0 / FPS

        # updates
        update_particles(dt)
        scroller.update(dt)
        tesseract.update(dt)

        # clear
        ctx.clear(0.0, 0.0, 0.0, 1.0)

        # Draw wallpaper background
        draw_wallpaper()

        # particles
        draw_particles()

        # clock
        draw_clock(now_t)

        # scroller rendering (visual-queue approach)
        tex_main.use(location=0)
        scroller.render(glyph_uvs_main, atlas_size_main, sdf_prog, quad_vao, render_sdf_text)

        # Tesseract dim background
        tesseract.dim(ctx, dim_prog_circ, quad_vbo)
        # Render tesseract (shadow + coloring split)
        tesseract.render(ctx, line_prog)

        # present (swap buffers)
        pygame.display.flip()
        clock.tick(FPS)

    # cleanup
    scroller.stop()

if __name__ == "__main__":
    main()
    
