# ma-cli

_a collection of higher-level commandline tools for the machinic ecosystem_

**An example:**

Slurp from a source and view the output after it has been processed by a pipe:
```
ma-throw slurp | lings-route-gather --collect 2 --pattern glworb:* | uniq | ma-dm
```

* ma-cli: terminals for stuff
    ```
    $ ma-cli -h
    usage: ma-cli [-h] [--cli {redis,mqtt,zerorpc,nomad,image}] [--info] [service]

        terminals and repls for different services


    positional arguments:
      service               service name to connect to

    optional arguments:
      -h, --help            show this help message and exit
      --cli {redis,mqtt,zerorpc,nomad,image}
                            cli type
      --info                print service info and quit
    ```

* ma-deck: bind stuff, press stuff, throw code, set state
    ```
    $ ma-deck -h
    usage: ma-deck [-h]

        bind stuff, press stuff, throw code, set state


    optional arguments:
      -h, --help  show this help message and exit
    ```

* ma-dm: inspect stuff
    ```
    $ ma-dm -h
    usage: ma-dm [-h] [--see SEE] [--see-all] [--prefix PREFIX]
                 [--pattern PATTERN]
                 [uuid]

        data model(s): work with glworbs


    positional arguments:
      uuid               hash or uuid of thing

    optional arguments:
      -h, --help         show this help message and exit
      --see SEE          field to dereference and show
      --see-all          dereference all fields and show with display
      --prefix PREFIX    set retrieval prefix for hash/uuid
      --pattern PATTERN  list all matching pattern
    ```

* ma-throw: throw stuff and see what responds
    ```
    $ ma-throw -h
    usage: ma-throw [-h] [-s SERVICE [SERVICE ...]] [-v] [--pretty]
                    throwables [throwables ...]

        throw stuff and see what responds


    positional arguments:
      throwables            stuff to throw

    optional arguments:
      -h, --help            show this help message and exit
      -s SERVICE [SERVICE ...], --service SERVICE [SERVICE ...]
                            specific service names to connect to
      -v, --verbose         verbose
      --pretty              pretty print
    ```

* ma-vis: visualize stuff
    ```
    $ ma-vis -h
    usage: ma-vis [-h] [--pattern PATTERN] [--self-document]

        Visualize state of running lings, services, machines...


    optional arguments:
      -h, --help         show this help message and exit
      --pattern PATTERN  filter generated graph
      --self-document    generates sanitized svg for README
    ```
![partial map][rel-ma-vis-svg]

[rel-ma-vis-svg]: ma-vis-screenshot.svg?sanitize=true


## Contributing
This project uses the C4 process 

[https://rfc.zeromq.org/spec:42/C4/](https://rfc.zeromq.org/spec:42/C4/
)

## License
Mozilla Public License, v. 2.0

[http://mozilla.org/MPL/2.0/](http://mozilla.org/MPL/2.0/)

