# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import sys
import argparse
from curtsies import Input
import redis
from lxml import etree
from ma_cli import data_models

r_ip, r_port = data_models.service_connection()
binary_r = redis.StrictRedis(host=r_ip, port=r_port)
redis_conn = redis.StrictRedis(host=r_ip, port=r_port, decode_responses=True)
LOOP_EXIT_BINDINGS = (u'<ESC>', u'<Ctrl-d>')

# originally named ma-tree
# expect glworbs to be piped in
# ma-throw slurp | ma-dial --key-xml project:texxt --menu-for part::name
# echo foo:bar | ma-dial --key-xml project:texxt --menu-for part::name


# dynamic keys:
#  uuid(s)
#  increment value
#  decrement value
#  zero value

def create_menu_trees(keys, menu_trees):
    trees = {}
    for key in keys:
        contents = redis_conn.get(key)
        xml = etree.fromstring(contents)
        for item in menu_trees:
            attribs = []
            attribute = "name"
            if "::" in item:
                item, attribute = item.split("::")

            trees[item] = {}

            for record in xml.xpath('//{}'.format(item)):
                try:
                    attribs.append(str(record.xpath("./@{}".format(attribute))[0]))
                except IndexError as ex:
                    pass
                
            trees[item] = sorted(attribs)

    return trees

def confirm_values(key, pair):
    print("for key {}".format(key))
    print("set {} to {}? (y/n)".format(*pair))
    # with Input(keynames='curtsies') as input_generator:
    #     for e in Input():
    while True:
        e = input()
        if e in LOOP_EXIT_BINDINGS:
            break
        elif e in "Yy":
            redis_conn.hmset(key, {pair[0]: pair[1]})
            print("done!")
            break
        elif e in "Nn":
            break

def menu(working_key, trees, key_value_pair=None):
    print("working key: {}".format(working_key))
    dial_key = 0
    dial_menu = {}
    if key_value_pair is None:
        key_value_pair = []

    for k, v in trees.items():
        for leaf in v:
            dial_menu[str(dial_key)] = leaf
            dial_key += 1

    def print_menu():
        print("~~things~~")
        dial_key_num = 0
        for k, v in trees.items():
            print("  {}".format(k))
            for leaf in v:
                print("{}  {}".format(dial_key_num, leaf))
                dial_key_num += 1

    print_menu()

    # with Input(keynames='curtsies') as input_generator:
    #     for e in Input():
    while True:
        e = input()
        if e in LOOP_EXIT_BINDINGS:
            break
        else:
            if e in dial_menu.keys():
                key_value_pair.append(dial_menu[e])
            if len(key_value_pair) == 2:
                confirm_values(working_key, key_value_pair)
                key_value_pair = []
            else:
                print_menu()

def top_loop(keys, trees=None):
    dial_key = 0
    dial_menu = {}
    for key_num, key in enumerate(keys):
        dial_menu[str(key_num)] = key

    def print_keys():
        print("~~keys~~")
        for key_num, key in enumerate(keys):
            print("{} {}".format(key_num, key))

    print_keys()

    # with Input(keynames='curtsies') as input_generator:
    #     for e in Input():
    while True:
        e = input()
        if e in LOOP_EXIT_BINDINGS:
            sys.exit(0)
        elif e in dial_menu.keys():
            menu(dial_menu[e], trees)
        else:
            print_keys()

def main():

    keys = []
    if not sys.stdin.isatty():
        import re
        keys = []
        for line in sys.stdin:
            #quoted_keys = re.findall('(?:\')([^\']*)(?:\')', line)
            #quoted_keys = re.findall(r'\'([^]]*)\'', line)
            keys.extend(line.split(" "))
        keys = [key.strip() for key in keys]

    parser = argparse.ArgumentParser()
    parser.add_argument("--key-xml", nargs='+', default=[], help="keys containing xml strings")
    parser.add_argument("--menu-for", nargs='+', default=["part"], help="")
    parser.add_argument("--key", nargs='+', default=[], help="working keys")
    args, _ = parser.parse_known_args()
    trees = create_menu_trees(args.key_xml, args.menu_for)
    args.key.extend(keys)
    # expected usage involves piping keys in
    # curtsies fails with:
    # termios.error: (25, 'Inappropriate ioctl for device')
    # curtsies is preferrable for input without pressing enter
    # and allowing keys such as escape to exit..,
    #
    # for now clear stdin and use input()
    sys.stdin = open("/dev/tty")
    if args.key:
        top_loop(args.key, trees)
    else:
        print("no keys, exiting...")
        sys.exit()
