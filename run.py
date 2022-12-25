#!/usr/bin/env python

import logging
import time
from datetime import datetime
import argparse
import subprocess
import sys

from os.path import expanduser, sep, exists, getsize
from os import makedirs

import pygame
import pygame.camera


logging.basicConfig(
    level=logging.INFO
)

_IMAGE_NUMBER_FORMAT = "05d"
_IMAGE_POSTFIX = r"{:" + _IMAGE_NUMBER_FORMAT + r"}"
_IMAGE_PREFIX = "img"

_TIMEDATE_FORMAT = "%Y_%m_%d__%H_%M_%S"

_MEGA_BYTE = 1024 * 1024

_DEFAULT_MAKE_VIDEO = 'n'
_DEFAULT_RESOLUTION = '640x480'
_DEFAULT_MAXSIZE_MB = 100
_DEFAULT_DESTINATION = expanduser("~") + sep + "timelapse-pics"
_DEFAULT_INTERVAL_SEC = 10


def check_ffmpeg():
    '''Checks if ffmpeg is instaled'''
    output = subprocess.run(['which', 'ffmpeg'], check=True, stdout=subprocess.PIPE)
    return output.stdout.decode('utf-8').strip() != ""


def create_dir_if_not_exist(dir_path):
    '''Creates directory if it doesn't exist'''
    if not exists(dir_path):
        makedirs(dir_path)

def to_bytes(mega_bytes):
    '''Turns MB to B'''
    return mega_bytes * _MEGA_BYTE


def default_camera():
    '''Returns location of camera'''
    pygame.camera.init()
    cams = pygame.camera.list_cameras()
    return cams[0]


parser = argparse.ArgumentParser()

parser.add_argument(
    '--camera',
    default=default_camera(),
    help='mount point of camera (e.g. /dev/video0)'
    )

parser.add_argument(
    '--resolution',
    default=_DEFAULT_RESOLUTION,
    help='resolution of images (e.g. 640x480)'
    )

parser.add_argument(
    '--maxsize',
    default=str(_DEFAULT_MAXSIZE_MB),
    type=int,
    help='max size of images in MB (e.g. 100)'
    )

parser.add_argument(
    '--interval',
    default=str(_DEFAULT_INTERVAL_SEC),
    type=int,
    help='default interval (in secunds) between taken images (e.g. 10)'
    )

parser.add_argument(
    '--destination',
    default=_DEFAULT_DESTINATION,
    help='path to directory for storing images'
    )

parser.add_argument(
    '--video',
    default=_DEFAULT_MAKE_VIDEO,
    help='create video from pictures',
    choices=['y', 'n']
    )

args = parser.parse_args()


logging.info("Camera mounted at %s will be used", args.camera)
logging.info("Images will have resolution %s", args.resolution)
logging.info("Images will take at max %sMB (+1 image)", args.maxsize)
logging.info("Images will be taken every %ss", args.interval)
logging.info("Images will be stored at %s", args.destination)
logging.info("Video will be created %s", args.video)


class StorageSpaceExceeded(Exception):
    '''Exception raised when designated memory is full'''

    def __init__(self, maxsize, taken):
        self._max = maxsize
        self._taken = taken

    def __str__(self):
        used_s = int(self._taken/_MEGA_BYTE)
        max_s = int(self._max/_MEGA_BYTE)
        return f"Used {used_s}MB disk space from available {max_s}MB"


class SdCard:
    '''Manages stored pictures'''

    def __init__(self, size, directory):
        self._dir = directory
        self._size = size
        self._used = 0
        self._files = 0

    def storage_location(self):
        '''Returns path to dorectory that contains taken photos'''
        return self._dir

    def store(self, img):
        '''Stores given image'''
        img_number = _IMAGE_POSTFIX.format(self._files)
        img_path = self._dir + sep + _IMAGE_PREFIX + img_number + ".jpg"

        pygame.image.save(img, img_path)
        img_size = getsize(img_path)

        self._files += 1

        logging.info("Image %s persisted", img_path)

        self._used += img_size
        if self._used > self._size:
            raise StorageSpaceExceeded(self._size, self._used)


class Camera:
    '''Simplifies taking pictures with pygame and making videos with ffmpeg'''

    def __init__(self, mount_dir, resolution, card):
        self._card = card

        r_parts = resolution.split("x")
        res = (int(r_parts[0]), int(r_parts[1]))

        self._cam = pygame.camera.Camera(mount_dir, res)
        self._cam.start()

    def pics_location(self):
        '''Returns path to dorectory that contains taken photos'''
        return self._card.storage_location()

    def make_image(self):
        '''Takes photo and stores it'''
        img = self._cam.get_image()
        self._card.store(img)

    def generate_movie(self):
        '''Generates mp4 from taken pictures'''
        logging.info("generationg video started")
        subprocess.call([
            'ffmpeg',
            '-framerate', '1',
            '-i', self.pics_location() + sep + "img" + '%' + _IMAGE_NUMBER_FORMAT + ".jpg",
            '-c:v', 'libx264',
            '-profile:v', 'high',
            '-crf', '20',
            '-pix_fmt', 'yuv420p',
            self.pics_location() + sep + 'output.mp4'
        ])
        logging.info("generationg video ended")



class TimelapseMaker:
    '''High level object for taking mulitiple pictures and generating videos'''

    def __init__(self, pics_camera, interval, make_vid):
        self._camera = pics_camera
        self._interval = interval
        self._make_video = make_vid

    def take_timelapse_images(self):
        '''Takes pictures until the designated memory is full'''
        try:
            while True:
                self._camera.make_image()
                time.sleep(self._interval)

        except StorageSpaceExceeded as storage_ex:
            logging.info("error: %s", storage_ex)
            if self._make_video:
                self._camera.generate_movie()




make_video = args.video == 'y'

if make_video and not check_ffmpeg():
    logging.error("making video not supported, please install ffmpeg")
    sys.exit(1)

sd_card_location = args.destination + sep + datetime.now().strftime(_TIMEDATE_FORMAT)

create_dir_if_not_exist(args.destination)
create_dir_if_not_exist(sd_card_location)

sd_card = SdCard(to_bytes(args.maxsize), sd_card_location)

camera = Camera(args.camera, args.resolution, sd_card)

maker = TimelapseMaker(camera, args.interval, make_video)

maker.take_timelapse_images()


logging.info("EXITING...")
sys.exit(0)
