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

class NomadCLI(Cmd):
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
        self.port = "4646"
        Cmd.__init__(self)

    @property
    def scheduler_address(self):
        return "-address=http://{}:{}".format(self.host,self.port)

    def call_scheduler(self,call_string,subs,raw=False):
        subs.update({"address" : self.scheduler_address})
        call_string = call_string.format(**subs)
        output = subprocess.check_output(call_string.split(" ")).decode()
        print(output)
        if raw:
            return output

    def do_status(self,args):
        self.call_scheduler("nomad status {address}",{})

    def do_logs(self, job_id):
        subs =  {k : v for k, v in locals().items() if not k == 'self'}
        retry_with_id = False
        try:
            self.call_scheduler("nomad logs {address} {job_id}" ,subs)
            self.call_scheduler("nomad logs -stderr {address} {job_id}" ,subs)
        except:
            # Try to scrape for job id
            # this will not work well if a job
            # has multiple ids
            job_id = self.call_scheduler("nomad job status {address} {job_id}" ,subs,raw=True)
            id_line = False
            for line in job_id.split("\n"):
                print(">>",line)
                if id_line:
                    # overwrite subs jobs_id with scraped
                    subs['job_id'] = line.split(" ",1)[0]
                    retry_with_id = True
                    break
                if "Node ID" in line:
                    id_line = True

        if retry_with_id is True:
            self.call_scheduler("nomad logs {address} {job_id}" ,subs)
            self.call_scheduler("nomad logs -stderr {address} {job_id}" ,subs)

    def do_job(self,job_name):
        subs =  {k : v for k, v in locals().items() if not k == 'self'}
        self.call_scheduler("nomad job status {address} {job_name}" ,subs)

    def do_start(self,job_name):
        # alias for run
        # assumes running on machine that job files
        # were generated on.
        # expects generated job files in:
        # ~/.local/jobs
        import os
        subs =  {k : v for k, v in locals().items() if not k == 'self'}
        job_file  = os.path.join(os.path.expanduser('~'),".local/jobs","{}.hcl".format(job_name))
        print(job_file)
        if os.path.isfile(job_file):
            subs['job_file'] = job_file
            self.call_scheduler("nomad run {address} {job_file}" ,subs)
        else:
            print("not found: {job_file}".format(**subs))

    def do_stop(self,job_name):
        subs =  {k : v for k, v in locals().items() if not k == 'self'}
        self.call_scheduler("nomad stop {address} {job_name}" ,subs)

    def do_purge(self,job_name):
        subs =  {k : v for k, v in locals().items() if not k == 'self'}
        self.call_scheduler("nomad job stop -purge {address} {job_name}" ,subs)

class ZeroRpcCLI(Cmd):
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
            setattr(ZeroRpcCLI,'do_'+method, f)
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
    c = ZeroRpcCLI(ip,port)
    c.cmdloop()

def cli_mqtt(ip,port):

    print("mqtt-cli...")
    c = MqttCLI(ip,port)
    c.cmdloop()

def cli_nomad(ip,port):

    print("nomad-cli...")
    c = NomadCLI(ip,port)
    c.cmdloop()

def main():
    """
    terminals and repls for different services
    """

    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("service", default=None, nargs='?', help="service name to connect to")
    parser.add_argument("--cli", choices=("redis","mqtt","zerorpc","nomad"), help="cli type")
    parser.add_argument("--info", action='store_true', help="print service info and quit")

    args = parser.parse_args()
    # if run without any args, list all serivces and exit
    if args.service is None:
        for s in local_tools.fuzzy_lookup(""):
            print("{service:<20}    {ip}:{port}".format(**s))
        return
    else:
        ip,port = local_tools.lookup(args.service)

    # info prints formatted strings for copy / paste
    if args.info:
        print("-h {ip} -p {port} \n--port {port} --host {ip}\n{ip}:{port}".format(ip=ip, port=port))
        try:
            zc = zerorpc.Client()
            zc.connect("tcp://{}:{}".format(ip,port))
            results = zc._zerorpc_inspect()
            for k,v in sorted(results['methods'].items()):
                # coerce all to strings for formatting
                v['function'] = k
                if v['doc']:
                    v['doc'] = v['doc'].replace("\n"," ")
                v = {k:str(v) for k,v in v.items()}
                print("{function:<30}{args:<30}{doc:.20s}".format(**v))

        except Exception as ex:
            print(ex)
        return

    # both redis and mqtt will always connect
    # and then have no functionality

    if args.service == "redis" or args.cli == "redis":
        try:
            cli_redis(ip,port)
        except Exception as ex:
            print(ex)
            cli_zerorpc(ip,port)
    elif args.service == "nomad" or args.cli == "nomad":
        try:
            cli_nomad(ip,port)
        except Exception as ex:
            print(ex)
            cli_zerorpc(ip,port)
    elif args.service == "mqtt" or args.cli == "mqtt":
        try:
            cli_mqtt(ip,port)
        except Exception as ex:
            print(ex)
            cli_zerorpc(ip,port)
    else:
        cli_zerorpc(ip,port)
