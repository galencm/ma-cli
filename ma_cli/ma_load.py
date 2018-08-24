#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import argparse
import hashlib
import redis
from lxml import etree

def load(filename, db_host, db_port, db_conn):
    # for light (uses a more centralized key structure):
    #     routes:
    #     machinic:routes:{}:{} (hash key)
    #     scripts:
    #     machinic:scripts:{}:{} (hash key)
    #
    #     env vars?
    #     conditionling?
    #
    # for heavy:
    #     not implemented

    routes_key = "machinic:routes:{}:{}".format(db_host, db_port)
    scripts_key = "machinic:scripts:{}:{}".format(db_host, db_port)
    xml = etree.parse(filename)

    for route in xml.xpath('//route'):
        route_string = route.get("raw")
        # calculate route hash
        route_hash = hashlib.sha224(route_string.encode()).hexdigest()
        db_conn.hmset(routes_key, {route_hash : route_string})

    for script in xml.xpath('//script'):
        script_string = script.get("raw")
        script_name = script.get("name")
        db_conn.hmset(scripts_key, {script_name : script_string})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="xml file to load")
    parser.add_argument("--db-host",  help="db host ip, requires use of --db-port")
    parser.add_argument("--db-port", type=int, help="db port, requires use of --db-host")
    args = parser.parse_args()

    if bool(args.db_host) != bool(args.db_port):
        parser.error("--db-host and --db-port values are both required")

    # pass connection into function
    db_settings = {"host" :  args.db_host, "port" : args.db_port}
    binary_r = redis.StrictRedis(**db_settings)
    redis_conn = redis.StrictRedis(**db_settings, decode_responses=True)

    load(args.filename, args.db_host, args.db_port, redis_conn)

main()