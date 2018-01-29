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
import uuid

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

class Default(dict):
    def __missing__(self, key):
        return "{"+key+"}"

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

    return list(r.scan_iter(match=pattern))

def service_connection():

    return (r_ip,r_port)

def open_img(uuid,key=None):
    if key is not None:
        bytes_key = r.hget(uuid, key)
    else:
        bytes_key = uuid

    key_bytes = binary_r.get(bytes_key)
    file = io.BytesIO()
    file.write(key_bytes)
    image = Image.open(file)
    #file.close()
    # file does not get closed
    return image, file
    # yield image
    # file = io.BytesIO()
    # #image.save(file,image.format)
    # image.close()
    # file.seek(0)
    # #binary_r.set(bytes_key, file.read())
    # file.close()

def close_img(img):
    try:
        img.close()
    except:
        pass

def img_rotate(img,rotation):
    rotation = int(rotation)
    img = img.rotate(rotation, expand=1)
    return img

def img_rectangle_grid(img,xspacing=100,yspacing=100,upper_left_square=0,lower_right_square=0):
    xspacing = int(xspacing)
    yspacing = int(yspacing)
    upper_left_square = int(upper_left_square)
    lower_right_square = int(lower_right_square)

    draw = ImageDraw.Draw(img)
    imgw,imgh = img.size

    grid_number = 0
    x,y,x2,y2 = 0,0,0,0
    for col in range(0,imgw,xspacing):
        for row in range(0,imgh,yspacing):
            if grid_number == upper_left_square:
                x = col
                y = row
            elif grid_number == lower_right_square:
                x2 = col + xspacing
                y2 = row + yspacing

            grid_number +=1

    print(x,y,x2-x,y2-y)
    img = img_rectangle(img,x,y,x2-x,y2-y)

    return img

def img_grid(img,xspacing=100,yspacing=100,r=255,g=255,b=255,a=127,label=True,**kwargs):
    xspacing = int(xspacing)
    yspacing = int(yspacing)
    r = int(r)
    g = int(g)
    b = int(b)
    a = int(a)
    draw = ImageDraw.Draw(img)
    imgw,imgh = img.size

    for col in range(0,imgw,xspacing):
        draw.line((col,0,col,imgh), fill=(r,g,b))

    for row in range(0,imgh,yspacing):
        draw.line((0,row,imgw,row), fill=(r,g,b))

    if label:
        grid_number = 0
        for col in range(0,imgw,xspacing):
            for row in range(0,imgh,yspacing):
                draw.text((col, row),str("({}, {})".format(col,row)),(255,255,255))
                grid_label = str("{}".format(grid_number))
                w, h = draw.textsize(grid_label)
                tx = int(round(col+(xspacing/2)-(w/2)))
                ty = int(round(row+(yspacing/2)-(h/2)))
                # print(tx,ty)
                # #draw.text(tx, ty, grid_label, (255,255,255))
                draw.text((tx, ty), grid_label, (255,255,255))
                grid_number +=1

    #del draw
    return img

def img_rectangle_column(img,xspacing=100,left_column=0,right_column=0):
    xspacing = int(xspacing)
    left_column = int(left_column)
    right_column = int(right_column)

    draw = ImageDraw.Draw(img)
    imgw,imgh = img.size

    column_number = 0
    x,y,x2,y2 = 0,0,0,0
    for col in range(0,imgw,xspacing):
        if column_number == left_column:
            x = col
            y = 0
        elif column_number == right_column:
            x2 = col + xspacing
            y2 = imgh

        column_number +=1

    print(x,y,x2-x,y2-y)
    img = img_rectangle(img,x,y,x2-x,y2-y)

    return img

def img_column(img,xspacing=100,r=255,g=255,b=255,a=127,label=True,**kwargs):
    xspacing = int(xspacing)
    r = int(r)
    g = int(g)
    b = int(b)
    a = int(a)
    draw = ImageDraw.Draw(img)
    imgw,imgh = img.size

    for col in range(0,imgw,xspacing):
        draw.line((col,0,col,imgh), fill=(r,g,b))

    if label:
        column_number = 0
        for col in range(0,imgw,xspacing):
            draw.text((col, 0),str("({}, {})".format(col,0)),(255,255,255))
            column_label = str("{}".format(column_number))
            w, h = draw.textsize(column_label)
            tx = int(round(col+(xspacing/2)-(w/2)))
            ty = int(round((imgh/2)))
            draw.text((tx, ty), column_label, (255,255,255))
            column_number +=1

    return img

def img_rectangle(img, x, y, w, h, r=255,g=255,b=255,a=127,**kwargs):
    x = int(x)
    y = int(y)
    w = int(w)
    h = int(h)
    r = int(r)
    g = int(g)
    b = int(b)
    a = int(a)

    img = img.convert("RGBA")
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((x,y,x+w,y+h),(r,g,b,a))
    img = Image.alpha_composite(img, overlay)
    # return img otherwise composite is not visible
    return img

def img_overlay(img, text, x, y, fontsize, substitions={},**kwargs):
    x = int(x)
    y = int(y)
    fontsize = int(fontsize)

    text = text.format_map(Default(substitions))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSansMono.ttf", fontsize)
        draw.text((x, y),text,(255,255,255),font=font)
    except:
        font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/DejaVuSansMono.ttf", fontsize)
        draw.text((x, y),text,(255,255,255),font=font)

    return img

def img_view(img):
    img.show()
    return img

def view(thing_uuid, field=None, overlay="", prefix="", layers=None):
    # ma-throw slurp _ | ma-dm --overlay "rectangle 10 10 100 100 255 255 255 50" "overlay {ocr_result1} 10 10 30"
    env = {}
    try:
        env['substitutions'] = r.hgetall(thing_uuid)
    except:
        env['substitutions'] = {}

    layers = ["rectangle 10 10 100 100 255 255 255 50","overlay foo 10 10 30"]
    if field is not None:
        field_contents = r.hget(prefix + thing_uuid, field)
        with open_image(prefix + thing_uuid, field) as img:
            img = img_overlay(img,field_contents,1,1,20)
            img = img_overlay(img,overlay,1,100,20)
            img.show()
        #return { field : field_contents }
    else:
        with open_image(thing_uuid) as img:
            img_overlay(img,overlay,1,100,20)
            for layer in layers:
                layer_func = layer.split(" ")[0]
                try:
                    layer_args = layer.split(" ")[1:]
                except:
                    layer_args = []

                try:
                    img = globals()['img_'+layer_func](img,*layer_args,**env)
                except Exception as ex:
                    print(ex)

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

def duplicate(thing_uuid,ttl=600):

    # update uuid field?
    # restore ttl is milliseconds
    ttl *= 1000
    serialized = binary_r.dump(thing_uuid)
    prefix =  thing_uuid.split(":")[0]
    new_uuid = "{}:{}".format(prefix, str(uuid.uuid4()))
    r.restore(new_uuid, ttl, serialized)

    try:
        hashes = r.hgetall(new_uuid)
        # update referenced binaries
        # so they can be modified by
        # pipes
        for k,v in hashes.items():
            if "key" in k and ":" in v:
                hashes[k] = duplicate(v)
                print("updating reference hash: {} to {}".format(v,hashes[k]))
    except Exception as ex:
        print(ex)
        pass

    print("duplicate: {}".format(new_uuid))
    return new_uuid

def retrieve(thing_uuid,prefix=""):

    return r.hgetall(prefix + thing_uuid)