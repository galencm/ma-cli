# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import argparse
from ma_cli import data_models
import subprocess
import shlex
import sys

def main():
    """
    data model(s): work with glworbs 
    """

    keys = None
    if not sys.stdin.isatty():
        import re
        keys = []
        for line in sys.stdin:
            # match anything that looks like a key?
            # glworb:123456 | ma-dm <ocr call> <show with overlay>
            #  ^^ or ma-throw glworb glworb:123456 ocr
            # glworb_binary:123456 | ma-dm <create-glworb> -> stdout glworb:123456
            quoted_keys = re.findall(r'\'([^]]*)\'', line)
            keys.extend(quoted_keys)
            if not quoted_keys and ":" in line:
                keys.extend([line.strip()])

    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("uuid", nargs='?', help = "hash or uuid of thing")
    parser.add_argument("--see", help = "field to dereference and show")
    parser.add_argument("--see-all", action="store_true", help = "dereference all fields and show with display")
    parser.add_argument("--prefix", default= "glworb:", help = "set retrieval prefix for hash/uuid")
    parser.add_argument("--pattern", default= "*", help = "list all matching pattern")
    parser.add_argument("--modify", nargs='+', default=[], help = "nonpermanent image modifications, a series of quoted strings ie 'img_grid 500 500'")
    parser.add_argument("--add-field", help = "add empty field to all matching ---pattern")
    parser.add_argument("--remove-field", help = "remove field from all matching ---pattern")
    parser.add_argument("--field-values", nargs='+', default=[], help = "list of values to be randomly selected as value to field created by --add-field")
    parser.add_argument("--field-range", help = "populate field of all matching --pattern with increasing integers 1, 2, 3...")

    args = parser.parse_args()

    if keys:
        data_models.view_concatenate(keys, args.modify)
        # for key in keys:
        #     data_models.view(key,overlay = "")
        return

    if args.uuid is None:
        if args.add_field:
            print(data_models.add_field(args.add_field, data_models.enumerate_data(args.pattern),values=args.field_values))
            return
        elif args.remove_field:
            print(data_models.remove_field(args.remove_field, data_models.enumerate_data(args.pattern)))
            return
        elif args.field_range:
            print(data_models.range_field(args.field_range, data_models.enumerate_data(args.pattern)))
            return
        else:
            data_models.enumerate_data(args.pattern)
            return

    # chomp prefix from uuid if necessary
    if args.uuid.startswith(args.prefix):
        args.uuid = args.uuid[len(args.prefix):]

    data_thing = data_models.retrieve(args.uuid,prefix = args.prefix)
    data_model_string =  data_models.pretty_format(data_thing, args.uuid)
    pretty = data_models.pretty_format(data_thing, args.uuid,terminal_colors=True)
    print(pretty)

    if args.see: 
        data_models.view(args.uuid,
                        args.see,
                        overlay = data_model_string,
                        prefix = args.prefix)
    elif args.see_all:
        data_model =  data_models.pretty_format(data_thing, args.uuid)
        general_prefix = args.prefix.strip(":")
        for k,v in data_thing.items():
            if general_prefix in v or "binary:" in v or "_key" in k:
                data_models.view(args.uuid,
                                k,
                                overlay = data_model_string,
                                prefix = args.prefix)