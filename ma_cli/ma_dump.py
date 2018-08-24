#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import argparse
import redis
from lxml import etree

def dump(db_host, db_port, db_conn, dump_name="dump.xml"):
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

    # store in xml with machine as root
    dump = etree.Element("machine")
    
    routes_key = "machinic:routes:{}:{}".format(db_host, db_port)
    routes = db_conn.hgetall(routes_key)
    for route_hash, route_string in routes.items():
        # add note of lings since just dumping route as
        # a raw string instead of xml
        r = etree.Element("route", raw=route_string, ling="pathling")
        dump.append(r)

    scripts_key = "machinic:scripts:{}:{}".format(db_host, db_port)
    scripts = db_conn.hgetall(scripts_key)
    for script_name, script_string in scripts.items():
        s = etree.Element("script", raw=script_string)
        s.set("name", script_name)
        dump.append(s)

    dump_root = etree.ElementTree(dump)
    print(etree.tostring(dump, pretty_print=True).decode())
    dump_root.write(dump_name, pretty_print=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-host",  help="db host ip, requires use of --db-port")
    parser.add_argument("--db-port", type=int, help="db port, requires use of --db-host")
    parser.add_argument("-o", "--output", default="dump.xml", help="output filename")
    args = parser.parse_args()

    if bool(args.db_host) != bool(args.db_port):
        parser.error("--db-host and --db-port values are both required")

    # pass connection into function
    db_settings = {"host" :  args.db_host, "port" : args.db_port}
    binary_r = redis.StrictRedis(**db_settings)
    redis_conn = redis.StrictRedis(**db_settings, decode_responses=True)

    dump(args.db_host, args.db_port, redis_conn, dump_name=args.output)

main()