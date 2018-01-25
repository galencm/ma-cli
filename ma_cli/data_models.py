# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

from ma_cli import local_tools
import redis
from PIL import Image, ImageDraw, ImageFont, ImageShow
from contextlib import contextmanager
import io
import subprocess

r_ip,r_port = local_tools.lookup('redis')
r = redis.StrictRedis(host=r_ip, port=str(r_port),decode_responses=True)
binary_r = redis.StrictRedis(host=r_ip, port=str(r_port))

class FehImageViewer(ImageShow.UnixViewer):
    def show_file(self, filename, **options):
        # -F opens fullscreen with image scaled
        # to fit
        subprocess.Popen(['feh',filename,'-F'])
        return 1

#prefer feh
ImageShow.register(FehImageViewer, order=-1)

@contextmanager
def open_image(uuid,key=None):
    if key is not None:
        bytes_key = r.hget(uuid, key)
    else:
        bytes_key = uuid
    
    key_bytes = binary_r.get(bytes_key)
    file = io.BytesIO()
    file.write(key_bytes)
    image = Image.open(file)
    yield image
    file = io.BytesIO()
    #image.save(file,image.format)
    image.close()
    file.seek(0)
    #binary_r.set(bytes_key, file.read())
    file.close()

def enumerate_data(pattern):
    
    # terminal equivalent $ redis-cli -h {ip} -p {port} keys {pattern}

    for key in r.scan_iter(match=pattern):
        print(key)

def service_connection():

    return (r_ip,r_port)

# from img_pipe.py
def img_overlay(img, text, x, y, fontsize, *args):


    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSansMono.ttf", fontsize)
        draw.text((x, y),text,(255,255,255),font=font)
    except:
        font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/DejaVuSansMono.ttf", fontsize)
        draw.text((x, y),text,(255,255,255),font=font)

def view(thing_uuid, field=None, overlay="", prefix=""):
    if field is not None:
        field_contents = r.hget(prefix + thing_uuid, field)
        with open_image(prefix + thing_uuid, field) as img:
            img_overlay(img,field_contents,1,1,20)
            img_overlay(img,overlay,1,100,20)
            img.show()
        #return { field : field_contents }
    else:
        with open_image(thing_uuid) as img:
            img_overlay(img,overlay,1,100,20)
            img.show()


def pretty_format(dictionary,title="", terminal_colors=False):

    color_green = "\033[0;32m"
    color_end = "\033[0;0m"
    pretty_string = ""

    pretty_string += "{}\n".format(title)
    for k,v in dictionary.items():
        if "glworb" in v and ":" in v and terminal_colors:
            pretty_string += "{:<30}{}{}{}\n".format(k,color_green,v,color_end)
        else:
            pretty_string +=  "{:<30}{}\n".format(k,v)

    return pretty_string

def retrieve(thing_uuid,prefix=""):

    return r.hgetall(prefix + thing_uuid)