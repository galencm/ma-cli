# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import argparse
from ma_cli import data_models

def main():
    """
    data model(s): work with glworbs 
    """

    # TODO extend to hydra data model
    # call redis-cli for sorting etc...
    # this displays all glworbs on commandline:
    # redis-cli -h _ -p _ keys \glworb:*
    # use here or ma-cli?

    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("uuid", help = "hash or uuid of thing")
    parser.add_argument("--see", help = "field to dereference and show")
    parser.add_argument("--see-all", action="store_true", help = "dereference all fields and show with display")
    parser.add_argument("--prefix", default= "glworb:", help = "set retrieval prefix for hash/uuid")

    args = parser.parse_args()
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
            if general_prefix in v:
                data_models.view(args.uuid,
                                k,
                                overlay = data_model_string,
                                prefix = args.prefix)