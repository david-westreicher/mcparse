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
  * **WhileStmt** (`expression`, `stmt`)
  * **ForStmt** (`initexpr`, `conditionexpr`, `afterexpr`, `stmt`)
  * **DeclStmt** (`type`, `variable`, `expression`)
  * **CompStmt** (`stmts`)
  * **BinOp** (`operation`, `lhs`, `rhs`)
  * **UnaOp** (`operation`, `expression`)
  * **Literal** (`type`, `val`)
  * **Variable** (`name`)

   `expression`, `lhs`, `rhs` can be of type **BinOp**, **UnaOp**, **Literal** or **Variable**
   
   `if_stmt`, `stmt`, `else_stmt`, `stmts (list)` have the type **IfStmt**, **DeclStmt** or **CompStmt**
   
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
# binop can be any of ['+', '-', '*', '/', '%', '==', '!=', '<=', '>=', '<', '>']
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
  * **WhileStmt** (`expression`, `stmt`)
      * generate `startlabel`
      * `label startlabel`
      * generate `tmpvar`
      * generate `expression` code and save into `tmpvar`
      * generate `endlabel`
      * `jumpfalse tmpvar endlabel`
      * generate `stmt` code
      * `jump startlabel`
      * `label endlabel`
  * **ForStmt** (`initexpr`, `conditionexpr`, `afterexpr`, `stmt`)
      * generate `initexpr` code
      * generate `conditionlabel`
      * `label conditionlabel`
      * generate `condvar`
      * generate `conditionexpr` code and save into `condvar`
      * generate `endforlabel`
      * `jumpfalse condvar endforlabel`
      * generate `stmt` code
      * generate `afterexpr` code
      * `jump conditionlabel`
      * `label endforlabel`
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

### cfg.py
creates a control flow graph (`cfg: 'int' -> '[int]'`) from some basic blocks.

### lvn.py
optimizes the 3-addr.-code with **Local Value Numbering** and removes unnecessary assignments to temporary variables.

### dataflow.py
implements the **Worklist algorithm** and does **Liveness Analysis** on the code.

### vm.py
returns the values of the variables after the code was run.

## Build
```shell
$ pip install -r requirements.txt
```

## Run
All the scripts also accept some verbose flags for debugging: `-v / -vv / -vvv`


* Parser (source code to AST)
  ```
  $ python -m src.parser examples/test01.mc
  ```
* Three (AST to 3-address-code)
  ```
  $ python -m src.three examples/test01.mc
  ```
* BB (3-address-code to basic blocks)
  ```
  $ python -m src.bb examples/test01.mc
  ```
* LVN (local value numbering on basic blocks)
  ```
  $ python -m src.lvn examples/test01.mc
  ```
* CFG (control flow graph of basic blocks)
  ```
  $ python -m src.cfg examples/test01.mc graph.dot [--lvn]
  ```
* Dataflow (Live Variable Analysis)
  ```
  $ python -m src.dataflow examples/test23.mc
  ```
* Virtual Machine 
  ```
  $ python -m src.vm examples/test23.mc
  ```

## Example
```
$ python -m src.cfg examples/fib.mc graph.dot --lvn

############# Source code ##############
{
    int nthfib = 10;
    int f1 = 0;
    int f2 = 1;
    int i;
    for(i=0;i<nthfib;i=i+1){
        int nextfib = f1+f2;
        f1 = f2;
        f2 = nextfib;
    }
    int fib = f1;
}

######## Local Value Numbering #########
------------ Basic Block 0 -------------
nthfib	:=	10
f1	:=	0
f2	:=	1
i	:=	default-int
i	:=	0


------------ Basic Block 1 -------------
label		L0
.t4	:=	i	<	nthfib
jumpfalse		.t4	L1


------------ Basic Block 2 -------------
.t7	:=	f1	+	f2
nextfib	:=	.t7
f1	:=	f2
f2	:=	.t7
.t12	:=	i	+	1
i	:=	.t12
jump		L0


------------ Basic Block 3 -------------
label		L1
fib	:=	f1

########## Control Flow Graph ##########
0	->	1
1	->	2, 3
2	->	1
3	->	
```

![Example CFG](/docs/example.png "Example CFG")

The VM computes the 10'th fibonacci number (notice `'fib': 55`)
```
$ python -m src.vm examples/fib.mc 

############# Source code ##############
{
    int nthfib = 10;
    int f1 = 0;
    int f2 = 1;
    int i;
    for(i=0;i<nthfib;i=i+1){
        int nextfib = f1+f2;
        f1 = f2;
        f2 = nextfib;
    }
    int fib = f1;
}

############## VM result ###############
{'f1': 55, 'f2': 89, 'i': 10, 'nthfib': 10, 'fib': 55, 'nextfib': 89}
```

## Tests
```
$ python -m unittest discover -v
```
