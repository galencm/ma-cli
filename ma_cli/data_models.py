# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import io
import subprocess
import uuid
import random
from contextlib import contextmanager
import redis
from PIL import Image, ImageDraw, ImageFont, ImageShow
from ma_cli import local_tools

try:
    r_ip, r_port = local_tools.lookup('redis')
    redis_conn = redis.StrictRedis(host=r_ip, port=str(r_port), decode_responses=True)
    binary_redis_conn = redis.StrictRedis(host=r_ip, port=str(r_port))
except:
     r_ip, r_port = None, None

class FehImageViewer(ImageShow.UnixViewer):
    def show_file(self, filename, **options):
        # -F opens fullscreen with image scaled
        # to fit
        subprocess.Popen(['feh', filename, '-F'])
        return 1

#prefer feh
ImageShow.register(FehImageViewer, order=-1)

class Default(dict):
    def __missing__(self, key):
        return "{"+key+"}"

@contextmanager
def open_image(address_uuid, key=None):
    if key is not None:
        bytes_key = redis_conn.hget(address_uuid, key)
    else:
        bytes_key = address_uuid

    key_bytes = binary_redis_conn.get(bytes_key)
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

def add_field(field_name, uuids, values=None):

    if not values:
        values = [""]

    modified = []
    for u in uuids:
        redis_conn.hset(u, field_name, random.choice(values))
        modified.append(u)

    return modified

def range_field(field_name, uuids):

    # roman / other numerals ?
    increment = 0
    step = 1
    modified = []

    for i, u in enumerate(uuids):
        redis_conn.hset(u, field_name, increment)
        increment += step
        modified.append(u)

    return modified

def remove_field(field_name, uuids):

    modified = []

    for u in uuids:
        redis_conn.hdel(u, *[field_name])
        modified.append(u)

    return modified

def filter_data(filter_key,pattern):

    data = enumerate_data(pattern=pattern)
    data_filtered = []
    for d in data:
        has_key = redis_conn.hget(d, filter_key)
        if has_key:
            data_filtered.append((d, has_key))
    data_filtered = sorted(data_filtered, key=lambda x: x[1])
    data = [d[0] for d in data_filtered]

    return data

def filter_data_to_dict(filter_key,pattern,subsort=None,whitelist=None):

    data = enumerate_data(pattern=pattern)
    data_filtered = {}
    whitelist_passes = None

    for d in data:
        has_key = redis_conn.hget(d, filter_key)
        if has_key:
            if not has_key in data_filtered:
                data_filtered[has_key] = []

            if whitelist:
                check = []
                for k,v in whitelist.items():
                    value = redis_conn.hget(d, k)
                    if value in v and value is not None:
                        check.append(True)
                    elif value not in v and value is not None:
                        check.append(False)
                    else:
                        check.append(True)

                if True in set(check) and len(set(check)) == 1:
                    whitelist_passes = True
                else:
                    whitelist_passes = False

            if subsort and whitelist_passes is True or whitelist_passes is None:
                data_filtered[has_key].append((d,redis_conn.hget(d, subsort)))
            elif not subsort and whitelist_passes is True or whitelist_passes is None:
                data_filtered[has_key].append(d)
            else:
                pass

    if subsort:
        for key in data_filtered.keys():
            try:
                subsorted = sorted(data_filtered[key], key=lambda x: int(x[1]))
            except Exception as ex:
                subsorted = sorted(data_filtered[key], key=lambda x: x[1])
            data_filtered[key] = [d[0] for d in subsorted]
    else:
        for key in data_filtered.keys():
            data_filtered[key] = [d[0] for d in data_filtered[key]]

    data = data_filtered
    return data

def enumerate_data(pattern):

    # terminal equivalent $ redis-cli -h {ip} -p {port} keys {pattern}

    # for key in redis_conn.scan_iter(match=pattern):
    #     print(key)

    return list(redis_conn.scan_iter(match=pattern))

def sort_by(pattern, field):

    field_values = []
    for key in redis_conn.scan_iter(match=pattern):
        try:
            value = redis_conn.hget(key, field)
            if value:
                field_values.append((key, value))
        except redis.exceptions.ResponseError as ex:
            print(ex)

    return sorted(field_values, key=lambda x: x[1])

def service_connection():

    return (r_ip, r_port)

def open_img(address_uuid, key=None):
    if key is not None:
        bytes_key = redis_conn.hget(address_uuid, key)
    else:
        bytes_key = address_uuid

    key_bytes = binary_redis_conn.get(bytes_key)
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
    except Exception as ex:
        print(ex)

def img_rotate(img, rotation):
    rotation = int(rotation)
    img = img.rotate(rotation, expand=1)
    return img

def img_geometry_rectangle_grid(
        img,
        xspacing=100,
        yspacing=100,
        upper_left_square=0,
        lower_right_square=0,
        geometry_only=True):
    return img_rectangle_grid(img,
                              xspacing,
                              yspacing,
                              upper_left_square,
                              lower_right_square,
                              geometry_only)

def img_rectangle_grid(
        img,
        xspacing=100,
        yspacing=100,
        upper_left_square=0,
        lower_right_square=0,
        geometry_only=False):
    xspacing = int(xspacing)
    yspacing = int(yspacing)
    upper_left_square = int(upper_left_square)
    lower_right_square = int(lower_right_square)

    imgw, imgh = img.size

    grid_number = 0
    x, y, x2, y2 = 0, 0, 0, 0
    for col in range(0, imgw, xspacing):
        for row in range(0, imgh, yspacing):
            if grid_number == upper_left_square:
                x = col
                y = row

            if grid_number == lower_right_square:
                x2 = col + xspacing
                y2 = row + yspacing

            grid_number += 1

    print(x, y, x2 - x, y2 - y)
    img = img_rectangle(img, x, y, x2 - x, y2 - y)

    if geometry_only is True:
        return (x, y, x2 - x, y2 - y)
    else:
        return img

def img_grid(
        img,
        xspacing=100,
        yspacing=100,
        r=255,
        g=255,
        b=255,
        a=127,
        label=True):
    xspacing = int(xspacing)
    yspacing = int(yspacing)
    r = int(r)
    g = int(g)
    b = int(b)
    a = int(a)
    draw = ImageDraw.Draw(img)
    imgw, imgh = img.size

    for col in range(0, imgw, xspacing):
        draw.line((col, 0, col, imgh), fill=(r, g, b))

    for row in range(0, imgh, yspacing):
        draw.line((0, row, imgw, row), fill=(r, g, b))

    if label:
        grid_number = 0
        for col in range(0, imgw, xspacing):
            for row in range(0, imgh, yspacing):
                draw.text((col, row), str("({}, {})".format(col, row)), (255, 255, 255))
                grid_label = str("{}".format(grid_number))
                w, h = draw.textsize(grid_label)
                tx = int(round(col + (xspacing / 2) - (w / 2)))
                ty = int(round(row + (yspacing / 2) - (h / 2)))
                # print(tx,ty)
                # #draw.text(tx, ty, grid_label, (255,255,255))
                draw.text((tx, ty), grid_label, (255, 255, 255))
                grid_number += 1

    #del draw
    return img

def img_geometry_rectangle_column(
        img,
        xspacing=100,
        left_column=0,
        right_column=0,
        geometry_only=True):
    return img_rectangle_column(img,
                                xspacing,
                                left_column,
                                right_column,
                                geometry_only)

def img_rectangle_column(
        img,
        xspacing=100,
        left_column=0,
        right_column=0,
        geometry_only=False):
    xspacing = int(xspacing)
    left_column = int(left_column)
    right_column = int(right_column)

    imgw, imgh = img.size

    column_number = 0
    x, y, x2, y2 = 0, 0, 0, 0
    for col in range(0, imgw, xspacing):
        if column_number == left_column:
            x = col
            y = 0

        if column_number == right_column:
            x2 = col + xspacing
            y2 = imgh

        column_number += 1

    print(x, y, x2 - x, y2 - y)
    img = img_rectangle(img, x, y, x2 - x, y2 - y)

    if geometry_only is True:
        return (x, y, x2 - x, y2 - y)
    else:
        return img

def img_column(
        img,
        xspacing=100,
        r=255,
        g=255,
        b=255,
        a=127,
        label=True):
    xspacing = int(xspacing)
    r = int(r)
    g = int(g)
    b = int(b)
    a = int(a)
    draw = ImageDraw.Draw(img)
    imgw, imgh = img.size

    for col in range(0, imgw, xspacing):
        draw.line((col, 0, col, imgh), fill=(r, g, b))

    if label:
        column_number = 0
        for col in range(0, imgw, xspacing):
            draw.text((col, 0), str("({}, {})".format(col, 0)), (255, 255, 255))
            column_label = str("{}".format(column_number))
            w, h = draw.textsize(column_label)
            tx = int(round(col + (xspacing / 2) - (w / 2)))
            ty = int(round((imgh / 2)))
            draw.text((tx, ty), column_label, (255, 255, 255))
            column_number += 1

    return img

def img_geometry_rectangle_row(
        img,
        yspacing=100,
        upper_row=0,
        lower_row=0,
        geometry_only=True):
    return img_rectangle_row(img,
                             yspacing,
                             upper_row,
                             lower_row,
                             geometry_only)

def img_rectangle_row(
        img,
        yspacing=100,
        upper_row=0,
        lower_row=0,
        geometry_only=False):
    yspacing = int(yspacing)
    upper_row = int(upper_row)
    lower_row = int(lower_row)

    imgw, imgh = img.size

    row_number = 0
    x, y, x2, y2 = 0, 0, 0, 0
    for row in range(0, imgh, yspacing):
        if row_number == upper_row:
            x = 0
            y = row

        if row_number == lower_row:
            x2 = imgw
            y2 = row + yspacing

        row_number += 1

    print(x, y, x2 - x, y2 - y)
    img = img_rectangle(img, x, y, x2 - x, y2 - y)

    if geometry_only is True:
        return (x, y, x2 - x, y2 - y)
    else:
        return img

def img_row(
        img,
        yspacing=100,
        r=255,
        g=255,
        b=255,
        a=127,
        label=True):
    yspacing = int(yspacing)
    r = int(r)
    g = int(g)
    b = int(b)
    a = int(a)
    draw = ImageDraw.Draw(img)
    imgw, imgh = img.size

    for row in range(0, imgh, yspacing):
        draw.line((0, row, imgw, row), fill=(r, g, b))

    if label:
        row_number = 0
        for row in range(0, imgh, yspacing):
            draw.text((0, row), str("({}, {})".format(0, row)), (255, 255, 255))
            row_label = str("{}".format(row_number))
            w, h = draw.textsize(row_label)
            tx = int(round(imgw / 2))
            ty = int(round(row + (yspacing / 2) - (h / 2)))
            draw.text((tx, ty), row_label, (255, 255, 255))
            row_number += 1

    return img

def img_geometry_rectangle(
        img, x, y, w, h,
        r=255,
        g=255,
        b=255,
        a=127,
        geometry_only=True):
    return img_rectangle(img, x, y, w, h, r, g, b, a, geometry_only)

def img_rectangle(
        img, x, y, w, h,
        r=255,
        g=255,
        b=255,
        a=127,
        geometry_only=False,
        **kwargs):
    x = int(x)
    y = int(y)
    w = int(w)
    h = int(h)
    r = int(r)
    g = int(g)
    b = int(b)
    a = int(a)

    img = img.convert("RGBA")
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((x, y, x + w, y + h), (r, g, b, a))
    img = Image.alpha_composite(img, overlay)
    # return img otherwise composite is not visible
    if geometry_only is True:
        return (x, y, x + w, y + h)
    else:
        return img

def img_overlay(img, text, x, y, fontsize, substitutions=None, **kwargs):
    if substitutions is None:
        substitutions = {}
    x = int(x)
    y = int(y)
    fontsize = int(fontsize)

    text = text.format_map(Default(substitutions))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSansMono.ttf", fontsize)
        draw.text((x, y), text, (255, 255, 255), font=font)
    except:
        font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/DejaVuSansMono.ttf", fontsize)
        draw.text((x, y), text, (255, 255, 255), font=font)

    return img

def img_view(img):
    img.show()
    return img

def view_concatenate(uuids, modifications):

    images = []

    for thing in uuids:
        fields = redis_conn.hgetall(thing)
        for k, v in fields.items():
            if ":" in v or "binary:" in v or "glworb_binary:" in v or "_key" in k:
                try:
                    # append (pil image, file object, fields)
                    images.append((*open_img(thing, key=k), fields))
                except Exception as ex:
                    pass

    border = 50
    landscape_width = sum([img.size[0] + border for img, _, _ in images])
    landscape_height = max([img.size[1] for img, _, _ in images])
    landscape = Image.new('RGBA', (landscape_width, landscape_height))

    offset = 0

    for img, file, fields in images:
        for m in modifications:
            m = m.split(" ")
            try:
                img = globals()[m[0]](img, *m[1:])
            except Exception as ex:
                print(ex)
        img = img_overlay(img, pretty_format(fields), 100, 100, 30)
        landscape.paste(img, (offset, 0))
        offset += img.size[0] + border

    landscape.show()

    # cleanup
    for img, file, _ in images:
        img.close()
        file.close()

def view(thing_uuid, field=None, overlay="", prefix="", layers=None, output=None):
    env = {}
    try:
        env['substitutions'] = redis_conn.hgetall(thing_uuid)
    except:
        env['substitutions'] = {}

    layers = ["rectangle 10 10 100 100 255 255 255 50",
              "overlay foo 10 10 30"
             ]
    if field is not None:
        field_contents = redis_conn.hget(prefix + thing_uuid, field)
        with open_image(prefix + thing_uuid, field) as img:
            img = img_overlay(img, field_contents, 1, 1, 20)
            img = img_overlay(img, overlay, 1, 100, 20)
            img.show()
            if output is not None:
                img.save(output, img.format)
        #return { field : field_contents }
    else:
        with open_image(thing_uuid) as img:
            img_overlay(img, overlay, 1, 100, 20)
            for layer in layers:
                layer_func = layer.split(" ")[0]
                try:
                    layer_args = layer.split(" ")[1:]
                except:
                    layer_args = []

                try:
                    img = globals()['img_' + layer_func](img, *layer_args, **env)
                except Exception as ex:
                    print(ex)

            img.show()


def pretty_format(dictionary, title="", terminal_colors=False):

    color_green = "\033[0;32m"
    color_end = "\033[0;0m"
    pretty_string = ""

    pretty_string += "{}\n".format(title)
    for k, v in dictionary.items():
        if "glworb" in v and ":" in v and terminal_colors:
            pretty_string += "{:<30}{}{}{}\n".format(k, color_green, v, color_end)
        else:
            pretty_string += "{:<30}{}\n".format(k, v)

    return pretty_string

def duplicate(thing_uuid, ttl=600):

    # update uuid field?
    # restore ttl is milliseconds
    ttl *= 1000
    serialized = binary_redis_conn.dump(thing_uuid)
    prefix = thing_uuid.split(":")[0]
    new_uuid = "{}:{}".format(prefix, str(uuid.uuid4()))
    redis_conn.restore(new_uuid, ttl, serialized)

    try:
        hashes = redis_conn.hgetall(new_uuid)
        # update referenced binaries
        # so they can be modified by
        # pipes
        for k, v in hashes.items():
            # need better or more consistent
            # method for discovering referenced
            # keys
            if "key" in k and ":" in v:
                hashes[k] = duplicate(v)
                print("updating reference hash: {} to {}".format(v, hashes[k]))
    except Exception as ex:
        print(ex)

    print("duplicate: {}".format(new_uuid))
    return new_uuid

def retrieve(thing_uuid, prefix=""):

    return redis_conn.hgetall(prefix + thing_uuid)
