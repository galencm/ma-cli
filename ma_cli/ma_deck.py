# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import sys
import argparse
import pathlib
import subprocess
from ruamel.yaml import YAML
from curtsies import Input

class Default(dict):
    def __missing__(self, key):
        #return "{"+key+"}"
        return "_"

def bind(yaml_files):
    bound = {}
    configuration = {}
    yaml = YAML(typ='safe')

    for file in yaml_files:
        print("loading yaml from {}".format(file))
        conf = yaml.load(pathlib.Path(file))
        for key,call in conf['bindings'].items():
            if len(key) > 1:
                curtsie_key = "<{}>".format(key)
            else:
                curtsie_key = key
            bound[curtsie_key] = call
        try:
            configuration['bound'].update(bound)
        except KeyError:
            configuration['bound'] = bound

        configuration.update(conf)

    return configuration

def cli_previous_attribute(configuration):
    print("previous")

def cli_next_attribute(configuration):
    print("next")

def prepare(call_string, configuration, lookup_attribute):
    try:
        attribute = configuration['attributes'][lookup_attribute]
    except:
        attribute={}
    # have to get to check min/max logic
    formatted = call_string.format_map(Default(attribute))
    return formatted

def input_loop(bindings):
    loop_exit_bindings = (u'q', u'Q', u'<ESC>', u'<Ctrl-d>')
    active_attribute = "zoom"
    with Input(keynames='curtsies') as input_generator:
        for e in Input():

            if e in loop_exit_bindings:
                sys.exit(0)

            try:
                print(bindings['bound'][e])
                try:
                    call = bindings['bound'][e]
                    try:
                        # try to call as global func, 
                        # then as subprocess string
                        globals()[call](bindings)
                    except Exception as ex:
                        # print(type(ex).__name__, ex)
                        call_formatted = prepare(bindings['calls'][call], bindings, active_attribute)
                        # if pipe in string, use shell=True
                        # problematic since yaml could be any
                        # string
                        if "|" in call_formatted:
                            print(subprocess.check_output(call_formatted,shell=True).decode())
                        else:
                            print(subprocess.check_output(call_formatted.split(" ")).decode())
                except Exception as ex:
                    print(type(ex).__name__, ex)
            except KeyError:
                pass

def main():
    """
    bind stuff, press stuff, throw code, set state
    """

    parser = argparse.ArgumentParser(description=main.__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--yaml", nargs='+', default=[], help = "yaml files to use for configuration and binding")
    args = parser.parse_args()

    if not args.yaml:
        yaml = [pathlib.PurePath(pathlib.Path(__file__).parents[0], 'cameras.yaml')]
        print("using default: {}".format(yaml))
    else:
        yaml = []
        for file in args.yaml:
            yaml.append(pathlib.PurePath(file))

    input_loop(bind(yaml))

