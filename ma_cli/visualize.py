from lings import pipeling
from lings import routeling
import subprocess
import zerorpc

def graph_ecosystem(title="",sanitize=False):

    graph_key = """
    subgraph cluster_key {
        label="Key";
        fillcolor=blue
        rpc_example[label="rpc\n[host]\n[port]", style="dotted"];
        pipe_example[label="pipe", style=filled, fillcolor=lightskyblue3];
        route_example[label="route", style=filled, fillcolor=lightskyblue1];
        call_example[label="call"];
        call2_example[label="another call"];
        route_example->call_example[label="[left compare] [value] [right compare] [args..]",color=lightskyblue1];
        pipe_example->call_example[label="[arg1, arg2 ... ]"]
        pipe_example->call2_example[label=""]

    }
    """

    graph = "digraph graphname {\n"
    route_calls = []

    routes = routeling.get_routes("*")
    for route in routes:
        for r in route.route_rules:
            args = ""
            if r.args:
                for arg in r.args:
                    args += arg.arg+"\n"
            args = args.strip()

            lcompare_string = "T"
            rcompare_string = "T"
            if r.left_compare:
                print(r.left_compare.comparator_value,r.left_compare.comparator_symbol.symbol)
                lcompare_string = "{0}{1}".format(r.left_compare.comparator_value,r.left_compare.comparator_symbol.symbol)
            if r.right_compare:
                print(r.right_compare.comparator_value,r.right_compare.comparator_symbol.symbol)
                rcompare_string = "{1}{0}".format(r.right_compare.comparator_value,r.right_compare.comparator_symbol.symbol)

            channel_node = r.channel.replace("/","FSLASH")

            lnode = "{0}{1}".format(channel_node,hash(lcompare_string))
            rnode = "{0}{1}".format(channel_node,hash(rcompare_string))
            graph += '{0} [label="{1}", style=filled, fillcolor=lightskyblue1]\n'.format(channel_node,r.channel)
            #graph += '{0} [label="{1}"]\n'.format(hash(args),args)
            if r.action == "pipe":
                graph += '{0} -> {1} [label="{2}", color=lightskyblue1]\n'.format(channel_node,args.split("\n")[0],lcompare_string + " x " + rcompare_string + " "+args)
            else:
                graph += '{} -> {} [label="{}", color=lightskyblue1]\n'.format(channel_node,r.action,lcompare_string + " x " + rcompare_string + " "+args)
            route_calls.append(r.action)

    pipes = pipeling.get_pipes("*")

    for p in pipes:
        print(p.name)
        graph += '{0} [label="{0}", style=filled, fillcolor=lightskyblue3]\n'.format(p.name)
        for step in p.pipe_steps:
            print(step.call)
            route_calls.append(step.call)
            graph += '{0} [label="{0}"]\n'.format(step.call,step.call)
            args = [arg.arg for arg in step.args]
            graph += '{} -> {} [label="{}"]\n'.format(p.name,step.call,args)

            #graph += '{0} [label="{0}"]\n'.format(step.call,step.call)
        print(args)

    for service in routeling.fuzzy_lookup('zerorpc-'):
        try:
            zc = zerorpc.Client()
            print(service)
            zc.connect("tcp://{}:{}".format(service['ip'],service['port']))
            result = zc("_zerorpc_inspect")
            #print(result)
            for k,v in result['methods'].items():
                if k in route_calls:
                    #print(v['args'])
                    if sanitize is True:
                        ip = "".join([ s if s == "." else "x" for s in service['ip'] ])
                        port = "".join([ s if s == "." else "x" for s in str(service['port']) ])
                        graph += '{0} [label="{1}",style="dotted"]\n'.format("rpc"+k,k+"\n{}\n{}\n".format(ip,port))
                    else:
                        graph += '{0} [label="{1}",style="dotted"]\n'.format("rpc"+k,k+"\n{}\n{}\n".format(service['ip'],service['port']))

                    graph += '{0} -> {1} [label="rpc",style="dotted"]\n'.format(k,"rpc"+k)

        except Exception as ex:
            print(ex)

    # func -> rpc -> machine
    graph+= 'labelloc="t";'
    graph+= 'label="{}";'.format(title)

    graph += graph_key
    graph += "}"

    return graph

def graph_display(file=None,**kwargs):
    graph = graph_ecosystem(**kwargs)

    with open("/tmp/graph.dot","w+") as f:
        f.write(graph)

    subprocess.call("dot /tmp/graph.dot -Grankdir=LR -Tsvg -o /tmp/graph.svg".split(" "))

    subprocess.call(["display","/tmp/graph.svg"])

    if file is not None:
        subprocess.call("dot /tmp/graph.dot -Grankdir=LR -Tsvg -o {}.svg".format(file).split(" "))
