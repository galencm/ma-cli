# ma-cli

_a collection of higher-level commandline tools for the machinic ecosystem_

## Installation

Pip:

```
pip3 install git+https://github.com/galencm/ma-cli --user --process-dependency-links
```

Develop while using pip:

```
git clone https://github.com/galencm/ma-cli
cd ma-cli/
pip3 install --editable ./ --user
```

## Usage

**Examples:**

```
ma-throw slurp | ma-dm
```
Slurps from source(s) and views the output after it has been processed by a pipe...

```
ma-throw discover
```
Discover things such as cameras or primitives

```
ma-dm | grep ca3c | ma-dm --see-all
```
Find a glworb by substring `ca3c` and see a montage of all referenced images in glworb

```
ma-cli image
image>
image>use glworb:some_uuid
image>highlight_regions
image>view
```
(1) Loads glworb and finds associated images, (2) highlights any ocr-ed regions by adding colored rectangles and (3) displays image with overlaid rectangles

**Tools:**

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
    usage: ma-deck [-h] [--yaml YAML [YAML ...]]

        bind stuff, press stuff, throw code, set state


    optional arguments:
      -h, --help            show this help message and exit
      --yaml YAML [YAML ...]
                            yaml files to use for configuration and binding
    ```

* ma-dm: inspect stuff
    ```
    $ ma-dm -h
    usage: ma-dm [-h] [--see SEE] [--see-all] [--prefix PREFIX]
                 [--pattern PATTERN] [--modify MODIFY [MODIFY ...]]
                 [--add-field ADD_FIELD] [--remove-field REMOVE_FIELD]
                 [--field-values FIELD_VALUES [FIELD_VALUES ...]]
                 [uuid]

        data model(s): work with glworbs


    positional arguments:
      uuid                  hash or uuid of thing

    optional arguments:
      -h, --help            show this help message and exit
      --see SEE             field to dereference and show
      --see-all             dereference all fields and show with display
      --prefix PREFIX       set retrieval prefix for hash/uuid
      --pattern PATTERN     list all matching pattern
      --modify MODIFY [MODIFY ...]
                            nonpermanent image modifications, a series of quoted
                            strings ie 'img_grid 500 500'
      --add-field ADD_FIELD
                            add empty field to all matching ---pattern
      --remove-field REMOVE_FIELD
                            remove field from all matching ---pattern
      --field-values FIELD_VALUES [FIELD_VALUES ...]
                            list of values to be randomly selected as value to
                            field created by --add-field
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

