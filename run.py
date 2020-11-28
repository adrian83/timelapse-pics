#!/usr/bin/env python

import pygame
import pygame.camera

import time
from datetime import datetime

import argparse

from os.path import expanduser, sep, isdir, exists, isfile, join, getsize
from os import makedirs, listdir



mega_byte = 1024 * 1024

def create_dir_if_not_exists(dir_path):
    if not exists(dir_path):
        makedirs(dir_path)

def to_bytes(mega_bytes):
    return mega_bytes * mega_byte


def default_camera():
    pygame.camera.init()
    cams = pygame.camera.list_cameras()
    return cams[0]

default_resolution = '640x480'
default_maxsize = 100 # MB
default_destination = expanduser("~") + sep + "timelapse-pics"
default_interval = 10 # sec


parser = argparse.ArgumentParser()
parser.add_argument('--camera', default=default_camera(), help='mount point of camera (e.g. /dev/video0)')
parser.add_argument('--resolution', default=default_resolution, help='resolution of images (e.g. 640x480)')
parser.add_argument('--maxsize', default=str(default_maxsize), type=int, help='max size of images in MB (e.g. 100)')
parser.add_argument('--interval', default=str(default_interval), type=int, help='default interval (in secunds) between taken images (e.g. 10')
parser.add_argument('--destination', default=default_destination, help='path to directory for storing images')


class CmdArgs:
    pass

cmd_args = CmdArgs
args = parser.parse_args(namespace=cmd_args)


print("")
print("Camera mounted at {0} will be used".format(cmd_args.camera))
print("Images will have resolution {0}".format(cmd_args.resolution))
print("Images will take at max {0}MB (+1 image)".format(cmd_args.maxsize))
print("Images will be taken every {0}s".format(cmd_args.interval))
print("Images will be stored at {0}".format(cmd_args.destination))
print("")


class StorageSpaceExceeded(Exception):

    def __init__(self, max, taken):
        self._max = max
        self._taken = taken

    def __str__(self):
        return "Used {0}MB disk space from available {1}MB".format(int(self._taken/mega_byte), self._max/mega_byte)


class SdCard:

    def __init__(self, size, dir):
        self._dir = dir
        self._size = size
        self._used = 0
        self._files = 0

    def store(self, img):
        number = "{:05d}".format(self._files)
        self._files += 1
        img_path = self._dir + sep + "img" + number + ".jpg"

        pygame.image.save(img, img_path)
        img_size = getsize(img_path)

        print("Image {0} persisted".format(img_path))

        self._used += img_size
        if self._used > self._size:
            raise StorageSpaceExceeded(self._size, self._used)


class Camera:

    def __init__(self, mount_dir, resolution, card):
        self._card = card

        r_parts = resolution.split("x")
        res = (int(r_parts[0]), int(r_parts[1]))

        self._cam = pygame.camera.Camera(mount_dir, res)
        self._cam.start()

    def make_image(self):
        img = self._cam.get_image()
        self._card.store(img)


class TimelapseMaker:

    def __init__(self, camera, interval):
        self._camera = camera
        self._interval = interval

    def take_timelapse_images(self):
        while True:
            self._camera.make_image()
            time.sleep(self._interval)



sd_card_location = cmd_args.destination + sep + datetime.now().strftime("%Y_%m_%d__%H_%M_%S")

create_dir_if_not_exists(cmd_args.destination)
create_dir_if_not_exists(sd_card_location)

sd_card = SdCard(to_bytes(cmd_args.maxsize), sd_card_location)

camera = Camera(cmd_args.camera, cmd_args.resolution, sd_card)

maker = TimelapseMaker(camera, cmd_args.interval)


try:
    maker.take_timelapse_images()

except StorageSpaceExceeded as e:
    print("")
    print(e)

except Exception as e:
    print("")
    print(str(e))

print("EXITING...")
print("")