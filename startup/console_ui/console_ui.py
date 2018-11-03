###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

from gevent import monkey; monkey.patch_all()
from gevent.lock import Semaphore
import gevent
import rpyc

from auto import logger
log = logger.init('console_ui', terminal=True)


import pygame
from collections import deque
import os
import re
import time
import numpy as np

os.putenv("SDL_VIDEODRIVER", "fbcon")
os.putenv("SDL_FBDEV",       "/dev/fb1")
os.putenv("SDL_MOUSEDRV",    "TSLIB")
os.putenv("SDL_MOUSEDEV",    "/dev/input/event0")


RESOURCE_DIR_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'resources')


# Settings:
CONSOLE_FONT_SIZE = 20
HEADER_FONT_SIZE = 30
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
window_surface = pygame.display.set_mode()
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

# Pre-load the logo
logo = pygame.image.load(LOGO_PATH)
logo_width, logo_height = logo.get_rect().size
logo_image_size = (header_rect.height * logo_width // logo_height, header_rect.height)
logo = pygame.transform.scale(logo, logo_image_size)


# State:
lines = deque()
lines.append([])

big_image_rect = None
big_image = None

big_status = None

stream_img_rect = None
stream_img = None


def draw_header():
    window_surface.fill(HEADER_BG_COLOR, header_rect)
    image_rect = pygame.Rect(console_rect.x + console_rect.width - logo_image_size[0], header_rect.y, *logo_image_size)
    window_surface.blit(logo, image_rect)
    title_text = header_font.render(HEADER_TITLE, True, HEADER_TXT_COLOR)
    window_surface.blit(title_text, (header_rect.x + 10, header_rect.y + 4))


def parse_text(new_text, old_lines, outer_rect):

    for char in new_text:

        if char == '\r':
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
    if big_image is not None:
        window_surface.blit(big_image, big_image_rect)
    if stream_img is not None:
        window_surface.blit(stream_img, stream_img_rect)
    if big_status is not None:
        big_lines = big_status.split('\n')
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


class ConsoleService(rpyc.Service):

    def __init__(self, global_lock):
        self.lock = global_lock

    def on_connect(self, conn):
        with self.lock:
            self.conn = conn
            self.conn_name = self.conn._config["connid"]
            log.info("New client: {}".format(self.conn_name))

    def on_disconnect(self, conn):
        with self.lock:
            log.info("Dead client: {}".format(self.conn_name))

    def exposed_write_text(self, text):
        with self.lock:
            log.info('Will print text: {}'.format(text))
            parse_text(text, lines, console_rect)
            draw_all()

    def exposed_clear_text(self):
        with self.lock:
            log.info('Will clear text!')
            global lines
            lines = deque()
            lines.append([])
            draw_all()

    def exposed_big_image(self, image_path):
        with self.lock:
            log.info('Will show big image at path: {}'.format(image_path))
            image_path = os.path.join(RESOURCE_DIR_PATH, image_path)
            global big_image_rect, big_image
            big_image_rect = full_rect
            big_image = pygame.image.load(image_path)
            big_image = pygame.transform.scale(big_image, big_image_rect.size)
            draw_all()

    def exposed_big_status(self, status):
        with self.lock:
            log.info('Will show big status: {}'.format(status))
            global big_status
            big_status = status
            if len(big_status) == 0:
                big_status = None
            draw_all()

    def exposed_big_clear(self):
        with self.lock:
            log.info('Will clear big image and status!')
            global big_image_rect, big_image, big_status
            big_image_rect = None
            big_image = None
            big_status = None
            draw_all()

    def exposed_stream_image(self, rect_vals, shape, image_buf):
        with self.lock:
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

    def exposed_clear_image(self):
        with self.lock:
            log.info('Will clear streamed image!')
            global stream_img_rect, stream_img
            stream_img_rect = None
            stream_img = None
            draw_all()


from rpyc.utils.server import GeventServer
from rpyc.utils.helpers import classpartial

global_lock = Semaphore(value=1)

ConsoleService = classpartial(ConsoleService, global_lock)

rpc_server = GeventServer(ConsoleService, port=18863)

log.info("RUNNING!")

gevent.joinall([
    gevent.spawn(rpc_server.start),
])

