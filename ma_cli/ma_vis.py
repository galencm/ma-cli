# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import argparse
from lings import pipeling
from lings import routeling
from ma_cli import visualize
import subprocess

def main():
    """
    Visualize state of running lings, services, machines...
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pattern", required=False,help="filter generated graph")
    parser.add_argument("--self-document", action='store_true', required=False,help="generates sanitized svg for README")

    args = parser.parse_args()

    if args.self_document:
        git_rev = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode()
        title="ma-vis@{}".format(git_rev)
        visualize.graph_display(file="ma-vis-screenshot", **{'sanitize':True,'title':title })

    visualize.graph_display()