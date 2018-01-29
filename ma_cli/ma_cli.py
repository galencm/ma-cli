# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import argparse
import subprocess
import random
import uuid
import queue
import threading
import json
from functools import partialmethod
import redis
from cmd2 import Cmd
import paho.mqtt.client as mosquitto
import zerorpc
from ma_cli import local_tools
from ma_cli import data_models as dm

class ImageFiler(object):
    """Manage images opened from redis key fields
    """
    def __init__(self):
        self.images = {}
        self._active_image = None
        self._active_image_key = None
        self._active_image_source = None

    def clear(self):
        del self.images
        self.images = {}
        self._active_image = None
        self._active_image_key = None
        self._active_image_source = None

    def restore_active(self):
        source = self._active_image_source
        key = self._active_image_key

        del self.images[source][key]
        self.images[source][key] = ImageFile(*dm.open_img(source, key=key), key)
        self._active_image = self.images[source][key].img

    def add_img(self, source):
        if source not in self.images:
            self.images[source] = {}

        #get keys try to open any that look like binary
        fields = dm.retrieve(source)
        for k, v in fields.items():
            if ":" in v:
                print("trying to load key: {} value: {} as image".format(k, v))
                try:
                    self.images[source][k] = ImageFile(*dm.open_img(source, key=k), k)

                    if self._active_image_source is None:
                        self._active_image_source = source

                    if self._active_image_key is None:
                        self._active_image_key = k

                    if self._active_image is None:
                        self._active_image = self.images[source][k].img

                    # use metadata key to store all values
                    self.images[source]['metadata'] = fields

                except Exception as ex:
                    print(ex)

    @property
    def metadata(self):
        return self.images[self._active_image_source]['metadata']

    @property
    def active_image(self):
        return self._active_image

    @active_image.setter
    def active_image(self, value):
        if value:
            self.images[self._active_image_source][self._active_image_key].img = value
            self._active_image = self.images[self._active_image_source][self._active_image_key].img

    @property
    def active_image_source(self):
        return self._active_image_source

    @active_image_source.setter
    def active_image_source(self, value):
        if value in self.images.keys():
            self._active_image_source = value
        else:
            print("{} not in dict".format(value))

    @property
    def active_image_key(self):
        return self._active_image_key

    @active_image_key.setter
    def active_image_key(self, value):
        if value in self.images[self._active_image_source].keys():
            self._active_image_key = value
            # update active image
            self._active_image = self.images[self._active_image_source][value].img
        else:
            print("{} not in dict".format(value))

class ImageFile(object):
    """Store and handle cleanup for pillow images
    """
    def __init__(self, img, file, hash_key=None):
        self.img = img
        self.file = file
        self.hash_key = hash_key

    def __del__(self):
        print("cleanup for {}".format(self))
        print("closing: {}".format(self.img))
        dm.close_img(self.img)
        print("closing: {}".format(self.file))
        self.file.close()

class ImageCLI(Cmd):
    """Interactively load and generated nonpersistent overlays
    on images. Image modification functions loaded from data_models.py
    Use generated material for pipes.
    """

    def __init__(self, host, port):
        #disable,otherwise argparse parsers in main() will interact poorly
        self.allow_cli_args = False
        self.redirector = '--->'
        self.allow_redirection = False
        self.host = host
        self.port = port

        self.source = None
        self.images = ImageFiler()

        self.op_stack = []
        self.pipes = []
        # create pipe on startup
        pipe_name = "tmp{}".format(str(uuid.uuid4())).replace("-", "")
        subprocess.call(["lings-pipe-add", pipe_name, "--expire", "600"])
        self.pipes.append(pipe_name)

        self.prompt = "{}:{}:{}>".format("image", host, port)

        img_funcs = []
        img_funcs.extend([k for (k, v) in dm.__dict__.items() if
                          not k.startswith('_')
                          and callable(dm.__dict__[k])
                          and k.startswith("img_")
                         ])

        for method in img_funcs:
            f = partialmethod(self._generic, method)
            setattr(ImageCLI, 'do_'+method[4:], f)
        Cmd.__init__(self)

    def __del__(self):
        # close open images and files
        del self.images

    def _generic(self, arg, method, *args):
        print(self, arg, method, args)
        args = list(filter(None, args))
        try:
            args = args[0].split(" ")
        except:
            pass
        self.images.active_image = getattr(dm, method)(self.images.active_image, *args)
        self.op_stack.append((method, args))

    def do_use(self, arg):

        #use random image_binary_key

        args = arg.split(" ")
        image_uuid = args[0]
        try:
            image_key = args[1]
            if image_key == '_':
                image_key = None
        except:
            image_key = None

        try:
            pattern = args[2]
        except:
            pattern = "glworb:*"

        if image_uuid == 'random':
            image_uuid = random.choice(dm.enumerate_data(pattern=pattern))

        self.images.clear()
        self.images.add_img(image_uuid)

    def do_using(self, arg):

        print("source: {} field: {}".format(self.images.active_image_source,
                                            self.images.active_image_key))

    def do_key(self, arg):

        self.images.active_image_key = arg

    def do_info(self, arg):

        terminal_colors = True
        color_green = "\033[0;32m"
        color_end = "\033[0;0m"
        pretty_string = ""

        for k, v in self.images.metadata.items():
            if "binary" in v and ":" in v and terminal_colors:
                pretty_string += "{:<30}{}{}{}".format(k, color_green, v, color_end)
            else:
                pretty_string += "{:<30}{}".format(k, v)

            if k == self.images.active_image_key:
                pretty_string += " * (active)"

            pretty_string += "\n"
        print(pretty_string)

    def do_reuse(self, arg):
        self.images.restore_active()
        self.op_stack = []

    def do_ops(self, arg):

        for op_num, op in enumerate(self.op_stack):
            print("{:<5}{}".format(op_num, "{} {}".format(op[0], ' '.join(op[1]))))

    def do_pipe(self, arg):
        # create anonymous temporary pipe, no dashes in name
        pipe_name = "tmp{}".format(str(uuid.uuid4())).replace("-", "")
        subprocess.call(["lings-pipe-add", pipe_name, "--expire", "600"])
        self.pipes.append(pipe_name)

    def do_pipe_append(self, arg):
        """Append args to pipe in
        form of call arg1 arg2 arg3..."""
        pipe_name = self.pipes[-1]
        pipe_string = arg
        subprocess.call(["lings-pipe-modify", pipe_name, pipe_string, "--append", "--expire", "600"])

    def do_pipe_save(self, arg):
        """Save working pipe by copying
        to name specified by arg"""
        pipe_name = self.pipes[-1]
        print(subprocess.check_output(["lings-pipe-modify",pipe_name,"--copy",arg]).decode())

    def do_pipe_info(self, arg):
        """Pretty-print pipe
        """
        pipe_name = self.pipes[-1]
        print(subprocess.check_output(["lings-pipe-modify",pipe_name,"--preview"]).decode())

    def do_dry_route(self, arg):
        pass

    def do_dry_pipe(self, arg):

        # prepare listener for end of pipe message
        q = queue.Queue()
        r_ip, r_port = local_tools.lookup('redis')
        r = redis.StrictRedis(host=r_ip, port=str(r_port), decode_responses=True)
        channel = "/pipe/{}/completed".format(self.pipes[-1])
        print("channel: {}".format(channel))
        t = threading.Thread(target=self.listen_pipe_finish, args=(channel, r, q))
        t.start()

        # duplicate hash and send through pipe
        duplicate = dm.duplicate(self.images.active_image_source)
        # need to pass in env for field/key
        subprocess.call(["lings-pipe-run",
                         self.pipes[-1],
                         duplicate,
                         "--context",
                         json.dumps({"key" : self.images.active_image_key})
                        ])

        # get end of pipe message and show result
        post_pipe = q.get()
        t.join()
        print("post pipe: {}".format(post_pipe))
        dm.view(post_pipe, field=self.images.active_image_key)

    def listen_pipe_finish(self, channel, redis_conn, q):

        pubsub = redis_conn.pubsub()
        pubsub.subscribe([channel])
        for item in pubsub.listen():
            if item['data'] != 1:
                print(item)
                q.put(item['data'])
                pubsub.unsubscribe()
                break

class NomadCLI(Cmd):
    """Given a host and port attempts to connect as client to zerorpc
    server. On connection gets list of remote services and dynamically
    generates attributes to allow tab completion.
    """
    def __init__(self, host, port):
        #disable,otherwise argparse parsers in main() will interact poorly
        self.allow_cli_args = False
        self.redirector = '--->'
        self.allow_redirection = False
        self.host = host
        self.port = "4646"
        self.prompt = "{}:{}:{}>".format("nomad", host, port)
        Cmd.__init__(self)

    @property
    def scheduler_address(self):
        return "-address=http://{}:{}".format(self.host, self.port)

    def call_scheduler(self, call_string, subs, raw=False):
        subs.update({"address" : self.scheduler_address})
        call_string = call_string.format(**subs)
        output = subprocess.check_output(call_string.split(" ")).decode()
        print(output)
        if raw:
            return output
        return None

    def do_status(self, args):
        self.call_scheduler("nomad status {address}", {})

    def do_logs(self, job_id):
        subs = {k : v for k, v in locals().items() if not k == 'self'}
        retry_with_id = False
        try:
            self.call_scheduler("nomad logs {address} {job_id}", subs)
            self.call_scheduler("nomad logs -stderr {address} {job_id}", subs)
        except:
            # Try to scrape for job id
            # this will not work well if a job
            # has multiple ids
            job_id = self.call_scheduler("nomad job status {address} {job_id}", subs, raw=True)
            id_line = False
            for line in job_id.split("\n"):
                print(">>", line)
                if id_line:
                    # overwrite subs jobs_id with scraped
                    subs['job_id'] = line.split(" ", 1)[0]
                    retry_with_id = True
                    break
                if "Node ID" in line:
                    id_line = True

        if retry_with_id is True:
            self.call_scheduler("nomad logs {address} {job_id}", subs)
            self.call_scheduler("nomad logs -stderr {address} {job_id}", subs)

    def do_job(self, job_name):
        subs = {k : v for k, v in locals().items() if not k == 'self'}
        self.call_scheduler("nomad job status {address} {job_name}", subs)

    def do_start(self, job_name):
        # alias for run
        # assumes running on machine that job files
        # were generated on.
        # expects generated job files in:
        # ~/.local/jobs
        import os
        subs = {k : v for k, v in locals().items() if not k == 'self'}
        job_file = os.path.join(os.path.expanduser('~'), ".local/jobs", "{}.hcl".format(job_name))
        print(job_file)
        if os.path.isfile(job_file):
            subs['job_file'] = job_file
            self.call_scheduler("nomad run {address} {job_file}", subs)
        else:
            print("not found: {job_file}".format(**subs))

    def do_stop(self, job_name):
        subs = {k : v for k, v in locals().items() if not k == 'self'}
        self.call_scheduler("nomad stop {address} {job_name}", subs)

    def do_purge(self, job_name):
        subs = {k : v for k, v in locals().items() if not k == 'self'}
        self.call_scheduler("nomad stop -purge {address} {job_name}", subs)

class ZeroRpcCLI(Cmd):
    """Given a host and port attempts to connect as client to zerorpc
    server. On connection gets list of remote services and dynamically
    generates attributes to allow tab completion.
    """
    def __init__(self, host, port):
        #disable,otherwise argparse parsers in main() will interact poorly
        self.allow_cli_args = False
        self.redirector = '--->'
        self.allow_redirection = False
        self.host = host
        self.port = port
        self.prompt = "{}:{}:{}>".format("zrpc", host, port)
        zc = zerorpc.Client()
        zc.connect("tcp://{}:{}".format(self.host, self.port))
        self.client = zc
        #get list of available services from zerorpc
        results = zc._zerorpc_inspect()
        print(results)

        for method in results['methods'].keys():
            #create a method to enable tab completion and pass in method name
            #for rpc call since cmd2 will chomp first string
            f = partialmethod(self._generic, method)
            # docstring is not available in cmd2
            # f.__doc__ = str(results['methods'][method]['doc'])
            # setattr(f,'__doc__',str(results['methods'][method]['doc']))
            setattr(ZeroRpcCLI, 'do_'+method, f)
        Cmd.__init__(self)

    def _generic(self, arg, method, *args):
        #TODO arg is being replaced by self due to partial
        print(self, arg, method, args)
        #cmd was sending an empty arg ('',)
        #which was causing signature errors for rpc function
        args = list(filter(None, args))
        print(self, arg, method, args)
        #args not being correctly parsed?
        #all are being passed as stirng in list
        try:
            args = args[0].split(" ")
        except:
            pass
        print(self, arg, method, args)
        result = getattr(self.client, method)(*args)
        print(result)

class MqttCLI(Cmd):
    """Given a host and port attempts to connect as client to zerorpc
    server. On connection gets list of remote services and dynamically
    generates attributes to allow tab completion.
    """
    def __init__(self, host, port):
        self.allow_cli_args = False
        self.redirector = '--->'
        self.allow_redirection = False
        self.host = host
        self.port = port
        self.prompt = "{}:{}:{}>".format("mqtt", host, port)
        self.client = mosquitto.Client()
        self.client.on_message = self.on_message
        self.client.connect(self.host, int(self.port), 60)
        #subscribe after connect
        self.client.subscribe('#', 0)
        self.client.loop_start()
        Cmd.__init__(self)

    def do_pub(self, arg):
        topic, payload = arg.split(" ", 1)
        print("topic: '{}'' payload: '{}'".format(topic, payload))
        self.client.publish(topic, payload)

    def on_message(self, client, userdata, message):
        print("{} {}".format(message.topic, message.payload.decode()))

def cli_redis(ip, port):

    print("redis-cli...")
    subprocess.call(['redis-cli', '-h', ip, '-p', str(port)])

def cli_image(ip, port):

    #will try for ~10s to connect
    print("image-cli...")
    c = ImageCLI(ip, port)
    c.cmdloop()

def cli_zerorpc(ip, port):

    #will try for ~10s to connect
    print("zerorpc-cli...")
    c = ZeroRpcCLI(ip, port)
    c.cmdloop()

def cli_mqtt(ip, port):

    print("mqtt-cli...")
    c = MqttCLI(ip, port)
    c.cmdloop()

def cli_nomad(ip, port):

    print("nomad-cli...")
    c = NomadCLI(ip, port)
    c.cmdloop()

def main():
    """
    terminals and repls for different services
    """

    parser = argparse.ArgumentParser(description=main.__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("service", default=None, nargs='?', help="service name to connect to")
    parser.add_argument("--cli", choices=("redis", "mqtt", "zerorpc", "nomad", "image"), help="cli type")
    parser.add_argument("--info", action='store_true', help="print service info and quit")

    args = parser.parse_args()
    # if run without any args, list all serivces and exit
    if args.service is None:
        for s in local_tools.fuzzy_lookup(""):
            print("{service:<20}    {ip}:{port}".format(**s))
        return
    elif args.service == "image":
        ip, port = local_tools.lookup('redis')
        cli_image(ip, port)
        return
    else:
        ip, port = local_tools.lookup(args.service)

    # info prints formatted strings for copy / paste
    if args.info:
        print("-h {ip} -p {port} \n--port {port} --host {ip}\n{ip}:{port}".format(ip=ip, port=port))
        try:
            zc = zerorpc.Client()
            zc.connect("tcp://{}:{}".format(ip, port))
            results = zc._zerorpc_inspect()
            for k, v in sorted(results['methods'].items()):
                # coerce all to strings for formatting
                v['function'] = k
                if v['doc']:
                    v['doc'] = v['doc'].replace("\n", " ")
                v = {k:str(v) for k, v in v.items()}
                print("{function:<30}{args:<30}{doc:.20s}".format(**v))

        except Exception as ex:
            print(ex)
        return

    # both redis and mqtt will always connect
    # and then have no functionality

    if args.service == "redis" or args.cli == "redis":
        try:
            cli_redis(ip, port)
        except Exception as ex:
            print(ex)
            cli_zerorpc(ip, port)
    elif args.service == "nomad" or args.cli == "nomad":
        try:
            cli_nomad(ip, port)
        except Exception as ex:
            print(ex)
            cli_zerorpc(ip, port)
    elif args.service == "mqtt" or args.cli == "mqtt":
        try:
            cli_mqtt(ip, port)
        except Exception as ex:
            print(ex)
            cli_zerorpc(ip, port)
    else:
        cli_zerorpc(ip, port)
