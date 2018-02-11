# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import argparse
from ma_cli import data_models
import redis

class Default(dict):
    def __missing__(self, key):
        return "{"+key+"}"

def main():
    """
    Export glworbs in different forms 
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-o", "--output-directory", default="/tmp", help = "output directory")
    parser.add_argument("--project", nargs='+', help = "project(s) to draw from")
    parser.add_argument("--no-exit", action="store_true", help = "continue running")

    args = parser.parse_args()
    
    r_ip, r_port = data_models.service_connection()
    redis_conn = redis.StrictRedis(host=r_ip, port=str(r_port), decode_responses=True)
    binary_redis_conn = redis.StrictRedis(host=r_ip, port=str(r_port))

    if args.project:
        for project in args.project:
            #'project:some name'
            print(redis_conn.zrangebyscore(project, "-inf", "inf"))

    # get list of glworbs
        # key(s) to write as binaries
        # enumeration / numering schemes for key(s)
        # manifest file
        # dotfile .written lists already written
        # (optional) category granularity
        # some sort of file / project schema key
            # key -> binary -> file
            # key -> text -> file