# mcparse

This is a testbed for code optimizations written in `python`.

It parses the [m(icro)C language](https://github.com/PeterTh/mC) and applies optimizations
discussed in the *Advanced Compiler Construction* class.

## Documentation
The current compiler pipeline looks like this:

![pipeline](/docs/pipeline.png "Pipeline")

* [parsimonious](https://github.com/erikrose/parsimonious) is a nice library which generates a parse tree and implements a NodeVisitor pattern
* `parser.py` visits the parse tree from the previous stage and creates the AST with the following nodes:
  * **IfStmt** (`expression`, `if_stmt`, `else_stmt`)
  * **DeclStmt** (`type`, `variable`, `expression`)
  * **CompStmt** (`stmts`)
  * **BinOp** (`operation`, `lhs`, `rhs`)
  * **UnaOp** (`operation`, `expression`)
  * **Literal** (`type`, `val`)
  * **Variable** (`name`)<br/>
   `expression`, `lhs`, `rhs` can be of type **BinOp**, **UnaOp**, **Literal** or **Variable**<br/>
   `if_stmt`, `else_stmt`, `stmts (list)` have the type **IfStmt**, **DeclStmt** or **CompStmt**<br/>
   `type` can be `'int'` or `'float'`

* `three.py` 


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
