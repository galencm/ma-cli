# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import argparse
import subprocess
import zerorpc
from cmd2 import Cmd
from functools import wraps,partialmethod
import paho.mqtt.client as mosquitto
from ma_cli import local_tools

class CmdLineApp(Cmd):
    """Given a host and port attempts to connect as client to zerorpc
    server. On connection gets list of remote services and dynamically
    generates attributes to allow tab completion.
    """
    def __init__(self, host,port):
        #disable,otherwise argparse parsers in main() will interact poorly
        self.allow_cli_args = False
        self.redirector = '--->'
        self.allow_redirection = False
        self.host = host
        self.port = port
        zc = zerorpc.Client()
        zc.connect("tcp://{}:{}".format(self.host,self.port))
        self.client = zc
        #get list of available services from zerorpc
        results = zc._zerorpc_inspect()
        print(results)

        for method in results['methods'].keys():
            #create a method to enable tab completion and pass in method name
            #for rpc call since cmd2 will chomp first string
            f = partialmethod(self._generic,method)
            #setattr(CmdLineApp,'do_'+method,f)
            setattr(CmdLineApp,'do_'+method, f)
        Cmd.__init__(self)

    def _generic(self,arg,method,*args):
        #TODO arg is being replaced by self due to partial
        print(self,arg,method,args)
        #cmd was sending an empty arg ('',)
        #which was causing signature errors for rpc function
        args = list(filter(None, args))
        print(self,arg,method,args)
        #args not being correctly parsed?
        #all are being passed as stirng in list
        try:
            args=args[0].split(" ")
        except:
            pass
        print(self,arg,method,args)
        result = getattr(self.client, method)(*args)
        print(result)

class MqttCLI(Cmd):
    """Given a host and port attempts to connect as client to zerorpc
    server. On connection gets list of remote services and dynamically
    generates attributes to allow tab completion.
    """
    def __init__(self, host,port):
        self.allow_cli_args = False
        self.redirector = '--->'
        self.allow_redirection = False
        self.host = host
        self.port = port
        self.client = mosquitto.Client()
        self.client.on_message = self.on_message
        self.client.connect(self.host, int(self.port), 60)
        #subscribe after connect
        self.client.subscribe('#',0)
        self.client.loop_start()
        Cmd.__init__(self)

    def do_pub(self,arg):
        topic,payload = arg.split(" ",1)
        print("topic: '{}'' payload: '{}'".format(topic,payload))
        self.client.publish(topic,payload)

    def on_message(self,client, userdata, message):
        print("{} {}".format(message.topic, message.payload.decode()))

def cli_redis(ip,port):

    print("redis-cli...")
    subprocess.call(['redis-cli','-h',ip,'-p',str(port)])

def cli_zerorpc(ip,port):

    #will try for ~10s to connect
    print("zerorpc-cli...")
    c = CmdLineApp(ip,port)
    c.cmdloop()

def cli_mqtt(ip,port):

    print("mqtt-cli...")
    c = MqttCLI(ip,port)
    c.cmdloop()

def main():
    """
    terminals and repls for different services
    """

    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("service", help="service name to connect to")
    parser.add_argument("--cli", choices=("redis","mqtt","zerorpc"), help="cli type")
    parser.add_argument("--info", action='store_true', help="print service info and quit")

    args = parser.parse_args()
    ip,port = local_tools.lookup(args.service)

    # info prints formatted strings for copy / paste
    if args.info:
        print("-h {ip} -p {port} \n--port {port} --host {ip}\n{ip}:{port}".format(ip=ip, port=port))
        return

    # both redis and mqtt will always connect
    # and then have no functionality

    if args.service == "redis" or args.cli == "redis":
        try:
            cli_redis(ip,port)
        except:
            cli_zerorpc(ip,port)
    elif args.service == "mqtt" or args.cli == "mqtt":
        try:
            cli_mqtt(ip,port)
        except:
            cli_zerorpc(ip,port)
    else:
        cli_zerorpc(ip,port)
