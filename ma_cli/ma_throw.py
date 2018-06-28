# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import argparse
import subprocess
from ma_cli import local_tools
import zerorpc
import pprint
import sys

def main():
    """
    throw stuff and see what responds
    """

    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("throwables", default=[], nargs='+', help="stuff to throw")
    parser.add_argument("-s", "--service", default=[], nargs='+', help="specific service names to connect to")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose")
    parser.add_argument("--pretty", action="store_true", help="pretty print")

    args = parser.parse_args()

    if args.throwables is None:
        for s in local_tools.fuzzy_lookup("zerorpc-"):
            print("{service:<30}    {ip}:{port}".format(**s))
        return
    else:

        results = []

        if args.service:
            services = []
            for service in args.service:
                services.extend(local_tools.fuzzy_lookup(service))
        else:
            services = local_tools.fuzzy_lookup("zerorpc-")

        for s in services:
            zc = zerorpc.Client()
            zc.connect("tcp://{ip}:{port}".format(**s))
            try:
                result = getattr(zc, args.throwables[0])(*args.throwables[1:])
                results.append(result)
                if args.verbose:
                    print("{:<30} \u2713".format(s['service']))
                    for r in result:
                        print(" " * 4 + "{}".format(str(r)))
            except Exception as ex:
                if args.verbose:
                    print("{:<30} \u2717  {}".format(s['service'], ex.name))
            if args.verbose:
                print()

        if args.pretty:
            print()
            pprint.pprint(results,indent=4)
            print()
            return
        elif args.verbose:
            return
        else:
            for result in results:
                if isinstance(result, list):
                    for result_item in result:
                        sys.stdout.write(str(result_item) +  '\n')
                        sys.stdout.flush()
                else:
                    sys.stdout.write(str(result))
                    sys.stdout.flush()

