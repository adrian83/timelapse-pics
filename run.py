


import pygame
import pygame.camera

import time
from datetime import datetime

from os.path import expanduser, sep, isdir, exists, isfile, join, getsize
from os import makedirs, listdir

import argparse

def default_camera():
    pygame.camera.init()
    cams = pygame.camera.list_cameras()
    return cams[0]

def default_resolution():
    return '640x480'


class Args:
    pass

a = Args

parser = argparse.ArgumentParser()

parser.add_argument('--camera', help='foo help')
parser.add_argument('--resolution', help='foo help')

args = parser.parse_args(args=['--camera', default_camera(), '--resolution', default_resolution()], namespace=a)

print(str(a.camera))
print(str(a.resolution))

class Camera:

    def __init__(self, location, resolution):
        r_parts = resolution.split("x")
        res = (int(r_parts[0]), int(r_parts[1]))

        self.cam = pygame.camera.Camera(location, res)
        self.cam.start()

    def save_image(self, img_path):
        img = self.cam.get_image()
        pygame.image.save(img, img_path)

cam = Camera(a.camera, a.resolution)

def create_dir_if_not_exists(dir_path):
    if not exists(dir_path):
        makedirs(dir_path)

class Session:

    def __init__(self):
        user_dir = expanduser("~")
        self.app_dir = user_dir + sep + "pi-images"

        now_str = datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
        self.session_dir = self.app_dir + sep + now_str

        self.file_index = 1

    def create_dirs(self):
        create_dir_if_not_exists(self.app_dir)
        create_dir_if_not_exists(self.session_dir)


    def next_file(self):
        number = "{:05d}".format(self.file_index)
        self.file_index += 1
        return self.session_dir + sep + "img" + number + ".jpg"

    def imgages_size(self):
        return sum([getsize(join(self.session_dir, f)) for f in listdir(self.session_dir) if isfile(join(self.session_dir, f))])




session = Session()
session.create_dirs()

try:

    while True:

        cam.save_image(session.next_file())

        pics_size = session.imgages_size()
        print("files ", str(pics_size))
        if pics_size > (10 * 1024 * 1024):
            print("max pics size exceded, exiting")
            break


        time.sleep(5)

except Exception as e:
    print(str(e))