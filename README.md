# mcparse

This is a testbed for code optimizations written in `python`.

It parses the [m(icro)C language](https://github.com/PeterTh/mC) and applies optimizations
discussed in the *Advanced Compiler Construction* class.

## Documentation
The current pipeline looks like this:

![pipeline](/docs/pipeline.png "Pipeline")


## Installation
```
$ pip install -r requirements.txt
```

## Run
All the scripts also accept some verbose flags for debugging: `-v / -vv / -vvv`


* Parser (source code to AST)

```
$ python src/parser.py examples/test01.mc
```

* Three (AST to 3-address-code)

```
$ python src/three.py examples/test01.mc
```

* BB (3-address-code to basic blocks)

```
$ python src/bb.py examples/test01.mc
```

## Tests
```
$ python -m unittest discover -v
```
