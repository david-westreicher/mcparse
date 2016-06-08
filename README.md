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
  * **FunDef** (`ret_type`, `name`, `params`, `stmts`)
  * **RetStmt** (`expression`)
  * **IfStmt** (`expression`, `if_stmt`, `else_stmt`)
  * **WhileStmt** (`expression`, `stmt`)
  * **ForStmt** (`initexpr`, `conditionexpr`, `afterexpr`, `stmt`)
  * **DeclStmt** (`type`, `variable`, `expression`)
  * **CompStmt** (`stmts`)
  * **FunCall** (`name`, `args`)
  * **BinOp** (`operation`, `lhs`, `rhs`)
  * **UnaOp** (`operation`, `expression`)
  * **Literal** (`type`, `val`)
  * **Variable** (`name`)

   `expression`, `lhs`, `rhs`, `args (list)` can be of type **BinOp**, **UnaOp**, **Literal** or **Variable**
   
   `if_stmt`, `stmt`, `else_stmt`, `stmts (list)` have the type **IfStmt**, **DeclStmt** or **CompStmt**
   
   `type`, `ret_type` can be `'int'` or `'float'`

### three.py
generates the 3-address-code by translating AST nodes into quadruples. These are the possible codes:

```
Operation   Arg1        Arg2        Result      Effect

jump                                label       pc := label
jumpfalse   var                     label       pc := (pc+1) if var else label
label                               label
function                            fname
call                                fname       fp.push(pc), pc := fname
end-fun
return                                          pc := fp.pop() + 1
push        var                                 stack.push(var)
pop                                 var         var := stack.pop()
assign      x                       var         var := x
binop       x           y           var         var := x * y
unop        x                       var         var := -x

    binops are ['+', '-', '*', '/', '%', '==', '!=', '<=', '>=', '<', '>']
    unops are ['-', '!']
```

The AST nodes get translated by the following rules

  * **FunDef** (`ret_type`, `name`, `params`, `stmts`)
      * `function name`
      * for every `pname` in `params`
          * `pop pname`
      * generate `stmts` code
      * `end-fun`
  * **RetStmt** (`expression`):
      * generate `tmpvar`
      * generate `expression` code and save into `tmpvar`
      * `push tmpvar`
      * `return`
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
  * **FunCall** (`name`, `args`), `result`
      * for every `expression` in `args`
          * generate `tmpvar`
          * generate `expression` code and save into `tmpvar`
          * `push tmpvar`
      * `call name`
      * `pop result`
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

Function calls are implemented as follows:
  * Suppose we have the function `int foo(int x, int y){ ... return z;}`
  * When we call `int res = foo(4,5)`:
    * `4` and `5` get pushed onto the stack (`push 4`, `push 5`)
    * we jump into the definition of `foo` (`call foo`)
    * `foo` pops `4` and `5` from the stack (`pop x`, `pop y`)
    * `foo` puts the value of `z` on the stack (`push z`)
    * we pop the stack and set `res` to that value (`pop res`)

### bb.py
transforms the 3-address-code into basic blocks by finding block leaders.

### cfg.py
creates a **Control Flow Graph** (`cfg: 'int' -> '[int]'`) from some basic blocks (ignores function calls).

### lvn.py
optimizes the 3-addr.-code with **Local Value Numbering** and removes unnecessary assignments to temporary variables.

### dataflow.py
implements the **Worklist algorithm** and does **Liveness Analysis** on the code.

### callgraph.py
creates a **Function Call Graph** (`fcg: 'str' -> '[str]'`) from some basic blocks.

### vm.py
returns the values of the variables after the code was run.

### assembler.py
converts the TAC to x86 assembly (AT&T syntax)

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
* CFG (Control Flow Graph of basic blocks)
  ```
  $ python -m src.cfg examples/test01.mc graph.dot [--lvn]
  ```
* Dataflow (Live Variable Analysis)
  ```
  $ python -m src.dataflow examples/test23.mc
  ```
* Callgraph (Function Call Graph of basic blocks)
  ```
  $ python -m src.callgraph examples/funcmutrec.mc graph.dot [--lvn]
  ```
* Virtual Machine 
  ```
  $ python -m src.vm examples/test23.mc
  ```
* Assembler
  ```
  $ python -m src.assembler examples/array_simple.mc [--lvn]
  ```

## Examples
```
$ python -m src.callgraph examples/funcmutrec.mc graph.dot --lvn

############# Source code ##############
{
    int is_even(int n){
        if (n!=0)
            return is_odd(n-1);
        return 1;
    }
    int is_odd(int n){
        if (n!=0)
            return is_even(n-1);
        return 0;
    }
    void main(){
        int ten_even = is_even(10);
        int ten_odd = is_odd(10);
    }
}

######## Local Value Numbering #########
------------ Basic Block 0 -------------
function	is_eve
	pop	n
	.t0	:=	n	!=	0
	jumpfalse	.t0	L0


------------ Basic Block 1 -------------
	.t4	:=	n	-	1
	push	.t4
	call	is_odd
	pop	.t3
	push	.t3
	return


------------ Basic Block 2 -------------
	label	L0
	push	1
	return
	end-fun


------------ Basic Block 3 -------------
function	is_odd
	pop	n
	.t8	:=	n	!=	0
	jumpfalse	.t8	L1


------------ Basic Block 4 -------------
	.t12	:=	n	-	1
	push	.t12
	call	is_eve
	pop	.t11
	push	.t11
	return


------------ Basic Block 5 -------------
	label	L1
	push	0
	return
	end-fun


------------ Basic Block 6 -------------
function	main
	push	10
	call	is_eve
	pop	.t16
	ten_ev	:=	.t16
	push	10
	call	is_odd
	pop	.t18
	ten_od	:=	.t18
	return
	end-fun



############## Call Graph ##############
main      	->	is_odd, is_even
is_even   	->	is_odd
is_odd    	->	is_even

########## Control Flow Graph ##########
0	->	1, 2
1	->	2
2	->	
3	->	4, 5
4	->	5
5	->	
6	->	
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

The Assembler generates x86 assembly and the code is executed
```
$ util/build.py examples/array_dynamic_sum.mc --lvn --execute
python -m src.assembler examples/array_dynamic_sum.mc --lvn

############# Source code ##############
{
    int sum(int n){
        int[n] arr;
        for(int i=0;i<n;i=i+1){
            arr[i] = i;
        }
        int sum = 0;
        for(i=0;i<n;i=i+1){
            sum = sum + arr[i];
        }
        return sum;
    }
    int main(){
        print_int(sum(read_int()));
        return 0;
    }
}

############# GNU Assembly #############
.globl main
.text
sum:		                   	# 1 params already on stack
	                        	#     n := 8(%ebp)
	push 	%ebp              
	mov  	%esp, %ebp        
	sub  	$36, %esp         	# make space on stack for 9 local registers
	                        	#   arr := -4(%ebp)
	                        	#     i := -8(%ebp)
	                        	#   sum := -20(%ebp)
	                        	#   .t2 := -12(%ebp)
	                        	#   .t7 := -16(%ebp)
	                        	#  .t15 := -32(%ebp)
	                        	#  .t17 := -28(%ebp)
	                        	#  .t12 := -24(%ebp)
	                        	#  .t19 := -36(%ebp)
	                        
	movl 	8(%ebp), %ebx     	# new int arr[n]
	leal 	(,%ebx, 4), %ebx  
	sub  	%ebx, %esp        
	movl 	%esp, -4(%ebp)    
	movl 	$0, -8(%ebp)      	# i := 0
L0:  	                   
	mov  	-8(%ebp), %ebx    	# .t2 = i < n
	mov  	8(%ebp), %eax     
	movl 	$0, -12(%ebp)     
	cmp  	%eax, %ebx        
	setl 	-12(%ebp)         
	cmp  	$0, -12(%ebp)     	# if(.t2==0) goto L1
	je   	L1                
	movl 	-8(%ebp), %eax    	# arr[i] = i
	movl 	-8(%ebp), %ebx    
	movl 	-4(%ebp), %ecx    
	movl 	%eax, -4(%ecx,%ebx,4)
	mov  	-8(%ebp), %eax    	# .t7 = i + 1
	add  	$1, %eax          
	mov  	%eax, -16(%ebp)   
	mov  	-16(%ebp), %eax   	# i := .t7
	movl 	%eax, -8(%ebp)    
	jmp  	L0                
L1:  	                   
	movl 	$0, -20(%ebp)     	# sum := 0
	movl 	$0, -8(%ebp)      	# i := 0
L2:  	                   
	mov  	-8(%ebp), %ebx    	# .t12 = i < n
	mov  	8(%ebp), %eax     
	movl 	$0, -24(%ebp)     
	cmp  	%eax, %ebx        
	setl 	-24(%ebp)         
	cmp  	$0, -24(%ebp)     	# if(.t12==0) goto L3
	je   	L3                
	movl 	-8(%ebp), %ebx    	# .t17 = arr[i]
	movl 	-4(%ebp), %ecx    
	movl 	-4(%ecx,%ebx,4), %eax
	movl 	%eax, -28(%ebp)   
	mov  	-20(%ebp), %eax   	# .t15 = sum + .t17
	add  	-28(%ebp), %eax   
	mov  	%eax, -32(%ebp)   
	mov  	-32(%ebp), %eax   	# sum := .t15
	movl 	%eax, -20(%ebp)   
	mov  	-8(%ebp), %eax    	# .t19 = i + 1
	add  	$1, %eax          
	mov  	%eax, -36(%ebp)   
	mov  	-36(%ebp), %eax   	# i := .t19
	movl 	%eax, -8(%ebp)    
	jmp  	L2                
L3:  	                   
	mov  	-20(%ebp), %eax   	# return sum
	mov  	%ebp, %esp        
	pop  	%ebp              
	ret  	                  
	                        
main:		                  	# 0 params already on stack
	push 	%ebp              
	mov  	%esp, %ebp        
	sub  	$8, %esp          	# make space on stack for 2 local registers
	                        	#  .t24 := -4(%ebp)
	                        	#  .t23 := -8(%ebp)
	                        
	call 	read_int          	# .t24 := read_int()
	mov  	%eax, -4(%ebp)    
	push 	-4(%ebp)          
	call 	sum               	# .t23 := sum(.t24)
	add  	$4, %esp          
	mov  	%eax, -8(%ebp)    
	push 	-8(%ebp)          
	call 	print_int         	# print_int(.t23)
	add  	$4, %esp          
	mov  	$0, %eax          	# return 0
	mov  	%ebp, %esp        
	pop  	%ebp              
	ret  	                  
	                        
Writing assembly to: 'examples/array_dynamic_sum.mc.s'
gcc -gdwarf-3 -o examples/array_dynamic_sum.mc.bin examples/array_dynamic_sum.mc.s assembler/lib.c -m32
examples/array_dynamic_sum.mc.bin
Enter an integer: 10
      45

```

## Tests
```
$ python -m unittest discover -v
```
