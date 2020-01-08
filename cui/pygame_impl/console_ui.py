###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

import os
import sys
import time
import pygame
import numpy as np
from collections import deque

from auto.services.labs.util import _shutdown

from auto import logger
log = logger.init(__name__, terminal=True)


RESOURCE_DIR_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')


# Settings:
CONSOLE_FONT_SIZE = 20
HEADER_FONT_SIZE = 25
BIG_STATUS_FONT_SIZE = 25
BG_COLOR = (0, 0, 0)
HEADER_BG_COLOR = (136, 204, 136)
HEADER_TXT_COLOR = (0, 68, 0)
CONSOLE_BG_COLOR = (255, 255, 255)
CONSOLE_TXT_COLOR = (0, 0, 255)
CONSOLE_TXT_BG_COLOR = (198, 205, 246)
BIG_STATUS_COLOR = (255, 255, 255)
BIG_STATUS_BG_COLOR = (50, 50, 50)
HEADER_CONSOLE_SPLIT = 7
HEADER_TITLE = 'AutoAuto Console'
HEADER_FONT_PATH = os.path.join(RESOURCE_DIR_PATH, 'fonts/DejaVuSansMono-Bold.ttf')
CONSOLE_FONT_PATH = os.path.join(RESOURCE_DIR_PATH, 'fonts/DejaVuSansMono.ttf')
LOGO_PATH = os.path.join(RESOURCE_DIR_PATH, 'images/logo_2017_03_17.png')

# Init pygame:
pygame.init()

# Create the window.
window_surface = pygame.display.set_mode(flags=pygame.FULLSCREEN)
window_width, window_height = window_surface.get_size()
pygame.display.set_caption(HEADER_TITLE)
pygame.mouse.set_visible(False)
window_surface.fill(BG_COLOR, window_surface.get_rect())

# Define the window areas:
border_width = 0
full_rect = pygame.Rect(border_width, border_width, window_width-2*border_width, window_height-2*border_width)
header_rect = pygame.Rect(full_rect.x, full_rect.y, full_rect.width, full_rect.height//HEADER_CONSOLE_SPLIT)
console_rect = pygame.Rect(full_rect.x, header_rect.y + header_rect.height, full_rect.width, full_rect.height-header_rect.height)

# The fonts we'll use:
console_font = pygame.font.Font(CONSOLE_FONT_PATH, CONSOLE_FONT_SIZE)
header_font = pygame.font.Font(HEADER_FONT_PATH, HEADER_FONT_SIZE)
big_status_font = pygame.font.Font(CONSOLE_FONT_PATH, BIG_STATUS_FONT_SIZE)

# Pre-load some stuff:
logo = pygame.image.load(LOGO_PATH)
logo_width, logo_height = logo.get_rect().size
logo_image_size = (header_rect.height * logo_width // logo_height, header_rect.height)
logo = pygame.transform.scale(logo, logo_image_size)
logo_rect = pygame.Rect(console_rect.x + console_rect.width - logo_image_size[0], header_rect.y, *logo_image_size)
header_title_sprite = header_font.render(HEADER_TITLE, True, HEADER_TXT_COLOR)


# State:
lines = deque()
lines.append([])

big_image_rect = None
big_image_obj = None

big_status_str = None

stream_img_rect = None
stream_img = None

battery_sprite = None


def draw_header():
    window_surface.fill(HEADER_BG_COLOR, header_rect)
    window_surface.blit(logo, logo_rect)
    window_surface.blit(header_title_sprite, (header_rect.x + 10, header_rect.y + 8))
    if battery_sprite is not None:
        battery_origin_x = console_rect.x + console_rect.width - logo_image_size[0] - battery_sprite.get_rect().width - 5
        battery_origin_y = header_rect.y + 8
        window_surface.blit(battery_sprite, (battery_origin_x, battery_origin_y))


def parse_text(new_text, old_lines, outer_rect):

    if old_lines:
        if len(old_lines[-1]) == 1 and old_lines[-1][0][0] == '\r':
            old_lines.pop()
            if old_lines:
                old_lines.pop()
            old_lines.append([])

    for char in new_text:

        if char == '\r':
            old_lines.append([('\r', None)])
            continue
        sprite = console_font.render(char, True, CONSOLE_TXT_COLOR, CONSOLE_TXT_BG_COLOR)
        rect = sprite.get_rect()

        last_line = old_lines[-1]

        if char == '\n':
            last_line.append((char, sprite))
            old_lines.append([])

        else:
            if len(last_line) < (outer_rect.width // rect.width):
                last_line.append((char,sprite))
            else:
                old_lines.append([(char, sprite)])

        while len(old_lines) > (outer_rect.height // rect.height):
            old_lines.popleft()


def draw_lines(lines, outer_rect):
    x, y = outer_rect.topleft
    for line in lines:
        if len(line)==1 and line[0][0] == '\r':
            continue
        for char, sprite in line:
            rect = sprite.get_rect()
            rect.topleft = (x, y)
            if char != '\n':
                window_surface.blit(sprite, rect)
            x += rect.width
        if line:
            x = outer_rect.x
            y += line[0][1].get_rect().height


def draw_console():
    window_surface.fill(CONSOLE_BG_COLOR, console_rect)
    draw_lines(lines, console_rect)


def draw_all():
    draw_header()
    draw_console()
    if big_image_obj is not None:
        window_surface.blit(big_image_obj, big_image_rect)
    if stream_img is not None:
        window_surface.blit(stream_img, stream_img_rect)
    if big_status_str is not None:
        big_lines = big_status_str.split('\n')
        y = full_rect.height - 10
        for line in reversed(big_lines):
            line = big_status_font.render(line, True, BIG_STATUS_COLOR, BIG_STATUS_BG_COLOR)
            line_rect = line.get_rect()
            line_rect.x += (full_rect.width - line_rect.width) / 2
            line_rect.y = (y - line_rect.height)
            y -= (line_rect.height + 5)
            window_surface.blit(line, line_rect)
    pygame.display.update()


draw_all()
needs_draw = False


def write_text(text):
    log.info('Will print text: {}'.format(text))
    parse_text(text, lines, console_rect)
    draw_all()


def clear_text():
    log.info('Will clear text!')
    global lines
    lines = deque()
    lines.append([])
    draw_all()


def big_image(image_path):
    log.info('Will show big image at path: {}'.format(image_path))
    image_path = os.path.join(RESOURCE_DIR_PATH, image_path)
    global big_image_rect, big_image_obj
    big_image_rect = full_rect
    big_image_obj = pygame.image.load(image_path)
    big_image_obj = pygame.transform.scale(big_image_obj, big_image_rect.size)
    draw_all()


def big_status(status):
    log.info('Will show big status: {}'.format(status))
    global big_status_str
    big_status_str = status
    if len(big_status_str) == 0:
        big_status_str = None
    draw_all()


def big_clear():
    log.info('Will clear big image and status!')
    global big_image_rect, big_image_obj, big_status_str
    big_image_rect = None
    big_image_obj = None
    big_status_str = None
    draw_all()


def stream_image(rect_vals, shape, image_buf):
    log.info('Will shows streamed image with shape: {}'.format(shape))
    width, height, channels = shape
    if channels not in (1, 3):
        return False
    global stream_img_rect, stream_img
    stream_img_rect = pygame.Rect(*rect_vals)
    if rect_vals == (0, 0, 0, 0):  # <-- sentinel value to mean the full screen
        stream_img_rect = full_rect
    if channels == 1:
        data2 = np.fromstring(image_buf, dtype=np.uint8).reshape((height, width))
        data = np.zeros((height, width, 3), dtype=np.uint8)
        data[:,:,0] = data2
        data[:,:,1] = data2
        data[:,:,2] = data2
        data = data.tobytes()
    else:   # channels == 3
        data = image_buf  # the `image_buf` is already bytes
    stream_img = pygame.image.fromstring(data, (width, height), 'RGB')
    stream_img = pygame.transform.scale(stream_img, stream_img_rect.size)
    draw_all()
    return True


def clear_image():
    log.info('Will clear streamed image!')
    global stream_img_rect, stream_img
    stream_img_rect = None
    stream_img = None
    draw_all()


def set_battery_percent(pct):
    """
    `pct` should be an integer in [0, 100].
    """
    if not isinstance(pct, int) or not (0 <= pct <= 100):
        raise Exception("Invalid battery percent")
    pct = "{}%".format(pct)
    global battery_sprite
    battery_sprite = header_font.render(pct, True, HEADER_TXT_COLOR)
    draw_all()


def close():
    log.info('Will close...')
    sys.exit(1)


mouse_up_event_times = deque()
n_mouse_up_target = 2
mouse_up_max_delay = 1.0  # seconds


def check_events():
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.MOUSEBUTTONUP:
            mouse_up_event_times.append(time.time())
            while len(mouse_up_event_times) > n_mouse_up_target:
                mouse_up_event_times.popleft()
            if len(mouse_up_event_times) == n_mouse_up_target:
                delay_here = mouse_up_event_times[-1] - mouse_up_event_times[0]
                if delay_here <= mouse_up_max_delay:
                    write_text('\nSHUTTING DOWN\n\n')
                    output = _shutdown(reboot=False)
                    write_text(output + '\n')


log.info("RUNNING!")

