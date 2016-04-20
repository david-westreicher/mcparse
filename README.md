# mcparse

This is a testbed for code optimizations written in `python`.

It parses the [m(icro)C language](https://github.com/PeterTh/mC) and applies optimizations
discussed in the *Advanced Compiler Construction* class.

## Documentation
The current compiler pipeline looks like this:

![pipeline](/docs/pipeline.png "Pipeline")

### [parsimonious](https://github.com/erikrose/parsimonious) 
is a nice library which generates a parse tree of a grammar defined in EBNF and implements a NodeVisitor pattern

### parser.py
visits the parse tree from the previous stage and creates the AST with the following nodes:
  * **IfStmt** (`expression`, `if_stmt`, `else_stmt`)
  * **DeclStmt** (`type`, `variable`, `expression`)
  * **CompStmt** (`stmts`)
  * **BinOp** (`operation`, `lhs`, `rhs`)
  * **UnaOp** (`operation`, `expression`)
  * **Literal** (`type`, `val`)
  * **Variable** (`name`)

   `expression`, `lhs`, `rhs` can be of type **BinOp**, **UnaOp**, **Literal** or **Variable**
   
   `if_stmt`, `else_stmt`, `stmts (list)` have the type **IfStmt**, **DeclStmt** or **CompStmt**
   
   `type` can be `'int'` or `'float'`

### three.py
generates the 3-address-code by translating AST nodes into quadruples. These are the possible codes:

```
[          QUADRUPLE            ]
DESCRIPTION
EXAMPLE
SIMPLE NOTATION
```

```python
['jump'     , None, None, result]
# Jump to label 'result'
['jump', None, None, 'L3']
jump        L3
```
```python
['jumpfalse', arg1, None, result]
# Jump to label 'result' if value/register 'arg1' equals to false
['jumpfalse', 1, None, 'L2']
jumpfalse   1   L2
```
```python
['label'    , None, None, result]
# A label with the name 'result'
['label', None, None, 'L1']
label       L1
```
```python
['assign'   , arg1, None, result]
# Assigns the value/register 'arg1' to the register 'result'
['assign', 'y', None, 'x']
x   :=      y
```
```python
[binop      , arg1, arg2, result]
# binop can be any of ['+', '-', '*', '/', '==', '!=', '<=', '>=', '<', '>']
# Assigns the result of the operation 'binop' (of the value/register 'arg1' and the value/register 'arg2') to the register 'result'
['+', 4, t1, 'x']
x   :=      4   +   t1
```
```python
[unop       , arg1, None, result]
# unop can be any of ['-', '!']
# Assigns the result of the operation 'unnop' (of the value/register 'arg1') to the register 'result'
['-', 4, None, 'x']
x   :=      -       4
```

The AST nodes get translated by the following rules

  * **IfStmt** (`expression`, `if_stmt`, `else_stmt`)
      * generate `tmpvar`
      * generate `endlabel`
      * generate `elselabel`
      * generate `expression` code and save into `tmpvar`
      * `jumpfalse tmpvar elselabel`
      * generate `if_stmt` code
      * `jump endlabel`
      * `label elselabel`
      * generate `else_stmt` code
      * `label endlabel`
  * **DeclStmt** (`type`, `variable`, `expression`)
      * generate `tmpvar`
      * generate `expression` code and save into `tmpvar`
      * `assign  tmpvar variable`
  * **CompStmt** (`stmts`)
      * for each stmt, generate `stmt` code
  * **BinOp** (`operation`, `lhs`, `rhs`), `result`
      * generate `tmpvarlhs`
      * generate `tmpvarrhs`
      * generate `lhs` code and save into `tmpvarlhs`
      * generate `rhs` code and save into `tmpvarrhs`
      * `operation tmpvarlhs tmpvarrhs result`
  * **UnaOp** (`operation`, `expression`), `result`
      * generate `tmpvar`
      * generate `expression` code and save into `tmpvar`
      * `operation tmpvar result`
  * **Literal** (`type`, `val`), `result`
      * `assign val result`
  * **Variable** (`name`), `result`
      * `assign name result`

There is also a special case where the **BinOp** is actually an assignment (if the left handside is a variable and the operation is a `=`)

### bb.py
transforms the 3-address-code into basic blocks by finding block leaders.

## Build
```shell
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
* LVN (local value numbering on basic blocks)
  ```
  $ python src/lvn.py examples/test01.mc
  ```
* CFG (control flow graph of basic blocks)
  ```
  $ python src/cfg.py examples/test01.mc graph.dot [--lvn]
  ```
* Dataflow (Live Variable Analysis)
  ```
  $ python src/dataflow.py examples/test23.mc
  ```

## Example
```
> python src/cfg.py examples/test01.mc graph.dot --lvn

############# Source code ##############
{
	int _x=1;
	float y = 3.0;
	if(_x > 0) {
		y = y * 1.5;
	} else {
		y = y + 2.0;
	}
}

############# Basic Blocks #############
Basic Block #0
.t0	:=	1
_x	:=	.t0
.t1	:=	3.0
y	:=	.t1
.t3	:=	_x
.t4	:=	0
.t2	:=	.t3	>	.t4
jumpfalse	.t2	L1

Basic Block #1
.t6	:=	y
.t7	:=	1.5
.t5	:=	.t6	*	.t7
y	:=	.t5
jump		L0

Basic Block #2
label		L1
.t9	:=	y
.t10	:=	2.0
.t8	:=	.t9	+	.t10
y	:=	.t8

Basic Block #3
label		L0

######## Local Value Numbering #########
Basic Block #0
_x	:=	1
y	:=	3.0
.t2	:=	1	>	0
jumpfalse	.t2	L1


Basic Block #1
.t5	:=	y	*	1.5
y	:=	.t5
jump		L0


Basic Block #2
label		L1
.t8	:=	y	+	2.0
y	:=	.t8


Basic Block #3
label		L0

########## Control Flow Graph ##########
0	->	1, 2
1	->	3
2	->	3
3	->	
```

![Example CFG](/docs/example.png "Example CFG")


## Tests
```
$ python -m unittest discover -v
```
