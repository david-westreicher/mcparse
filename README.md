# mcparse

is a testbed for code optimizations written in `python`.

It parses the [m(icro)C language](https://github.com/PeterTh/mC) and applies optimizations
discussed in the *Advanced Compiler Construction* class.

# installation
```
pip install -r requirements.txt
```

# run
Parser: source code to AST

```
python src/parser.py examples/test01.mc
```

Three: AST to 3-address-code

```
python src/three.py examples/test01.mc
```

Basic Blocks: 3-address-code to basic blocks

```
python src/bb.py examples/test01.mc
```

# unittests
```
python -m unittest discover -v
```
