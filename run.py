


import pygame
import pygame.camera

import time
from datetime import datetime

from os.path import expanduser, sep, isdir, exists, isfile, join, getsize
from os import makedirs, listdir

import argparse

def create_dir_if_not_exists(dir_path):
    if not exists(dir_path):
        makedirs(dir_path)

def to_bytes(mega_bytes):
    return mega_bytes * 1024 * 1024

def default_camera():
    pygame.camera.init()
    cams = pygame.camera.list_cameras()
    return cams[0]

default_resolution = '640x480'
default_maxsize = 100 # MB
default_destination = expanduser("~") + sep + "timelapse-pics"
default_interval = 10 # sec


class Args:
    pass

a = Args

parser = argparse.ArgumentParser()
parser.add_argument('--camera', default=default_camera(), help='mount point of camera (e.g. /dev/video0)')
parser.add_argument('--resolution', default=default_resolution, help='resolution of images (e.g. 640x480)')
parser.add_argument('--maxsize', default=str(default_maxsize), help='max size of images in MB (e.g. 100)')
parser.add_argument('--interval', default=str(default_interval), help='default interval (in secunds) between taken images (e.g. 10')
parser.add_argument('--destination', default=default_destination, help='path to directory for storing images')



args = parser.parse_args(namespace=a)




# print(str(a.camera))
# print(str(a.resolution))
# print(str(a.maxsize))
# print(str(a.delay))
# print(str(a.destination))

print("Camera mounted at {0} will be used".format(a.camera))
print("Images will have resolution {0}".format(a.resolution))
print("Images will take {0}MB at max (+1 image)".format(a.maxsize))
print("Images will be taken every {0}s".format(a.interval))
print("Images will be stored at {0}".format(a.destination))

class StorageSpaceExceeded(Exception):

    def __init__(self, max_size, real_size):
        self.max_size = max_size
        self.real_size = real_size

    def __str__(self):
        return "no available space left"


class SdCard:

    def __init__(self, size, dir):
        self.dir = dir
        self.size = size
        self.used = 0
        self._files = 0

    def store(self, img):
        number = "{:05d}".format(self._files)
        self._files += 1
        img_path = self.dir + sep + "img" + number + ".jpg"

        pygame.image.save(img, img_path)
        size = getsize(img_path)

        print("Image {0} persisted".format(img_path))

        self.used += size
        if self.used > self.size:
            raise StorageSpaceExceeded(self.size, self.used)


class Camera:

    def __init__(self, location, resolution, card):
        self.card = card

        r_parts = resolution.split("x")
        res = (int(r_parts[0]), int(r_parts[1]))

        self.cam = pygame.camera.Camera(location, res)
        self.cam.start()

    def make_image(self):
        img = self.cam.get_image()
        self.card.store(img)


class TimelapseMaker:

    def __init__(self, camera, interval):
        self.camera = camera
        self.interval = interval

    def take_timelapse_images(self):
        while True:
            self.camera.make_image()
            time.sleep(self.interval)



sd_card_location = a.destination + sep + datetime.now().strftime("%Y_%m_%d__%H_%M_%S")

create_dir_if_not_exists(a.destination)
create_dir_if_not_exists(sd_card_location)

sd_card = SdCard(to_bytes(int(a.maxsize)), sd_card_location)

camera = Camera(a.camera, a.resolution, sd_card)

maker = TimelapseMaker(camera, int(a.interval))


try:
    maker.take_timelapse_images()

except Exception as e:
    print(str(e))