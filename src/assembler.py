from .utils import function_ranges2, op_uses_values, op_sets_result, simplify_op, op_is_comp, bin_ops


class ASMInstruction:

    def __init__(self, op, arg1=None, arg2=None, comment=None, indent=True):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.comment = comment
        self.indent = indent

    def __str__(self):
        if self.op is None:
            return '\t'.ljust(25) + ('' if self.comment is None else '\t# ' + self.comment)
        indent = '\t' if self.indent else ''
        instr = indent + self.op.ljust(5) + '\t' + ', '.join([el for el in [self.arg1, self.arg2] if el is not None])
        instr = instr.ljust(25)
        if self.comment is not None:
            instr += '\t# ' + self.comment
        return instr

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (self.op, self.arg1, self.arg2) == (other.op, other.arg1, other.arg2)

op_to_asm = {
    '+': 'add',
    '-': 'sub',
    '*': 'imul',
    '/': 'idivl',
    '%': 'idivl',
    '==': 'sete',
    '!=': 'setne',
    '<=': 'setle',
    '>=': 'setge',
    '<': 'setl',
    '>': 'setg',
}


def is_var_or_temp(arg):
    return type(arg) is str


def gen_stack_mapping(code, params):
    currmap = {}
    for tac in code:
        op, _, _, _ = tac
        op = simplify_op(op)
        if op not in op_uses_values and op not in op_sets_result:
            continue
        for argpos in op_uses_values[op] + ([3]if op in op_sets_result else[]):
            arg = tac[argpos]
            if not is_var_or_temp(arg):
                continue
            if arg in currmap:
                continue
            if arg in params:
                continue
            currmap[arg] = -(len(currmap) + 1) * 4
    for loc, param in enumerate(params):
        currmap[param] = (loc + 2) * 4
    return currmap


def fun_to_asm(code, assembly):

    def arg_to_asm(arg):
        if is_var_or_temp(arg):
            return '%d(%%ebp)' % register_to_stack[arg]
        else:
            return '$%d' % arg

    def add(op, arg1=None, arg2=None, comment=None, indent=True):
        assembly.append(ASMInstruction(op, arg1, arg2, comment, indent))

    def to_assembly(op, arg1, arg2, res):
        if op == 'jump':
            add('jmp', res)
        elif op == 'jumpfalse':
            add('cmp', '$0', arg_to_asm(arg1), comment='if(' + str(arg1) + '==0) goto ' + res)
            add('je', res)
        elif op == 'label':
            add(res + ':', indent=False)
        elif op == 'function':
            raise NotImplementedError
        elif op == 'call':
            raise NotImplementedError
        elif op == 'end-fun':
            add(None)
        elif op == 'return':
            add('mov', '%ebp', '%esp')
            add('pop', '%ebp')
            add('ret')
        elif op == 'push':
            raise NotImplementedError
        elif op == 'pop':
            raise NotImplementedError
        elif op == 'assign':
            comment = res + ' := ' + str(arg1)
            need_accum = is_var_or_temp(arg1) and is_var_or_temp(res)
            arg1, res = [arg_to_asm(el) for el in [arg1, res]]
            if need_accum:
                add('mov', arg1, '%eax', comment=comment)
                add('movl', '%eax', res)
            else:
                add('movl', arg1, res, comment=comment)
        elif op in ['*', '/', '%']:
            comment = res + ' = ' + str(arg1) + ' ' + op + ' ' + str(arg2)
            add('mov', arg_to_asm(arg1), '%eax', comment=comment)
            if op in ['/', '%']:
                add('cdq')
            if is_var_or_temp(arg2):
                add(op_to_asm[op], arg_to_asm(arg2))
            else:
                add('mov', arg_to_asm(arg2), '%ecx')
                add(op_to_asm[op], '%ecx')
            if op == '%':
                add('mov', '%edx', arg_to_asm(res))
            else:
                add('mov', '%eax', arg_to_asm(res))
        elif op in bin_ops:
            comment = res + ' = ' + str(arg1) + ' ' + op + ' ' + str(arg2)
            if op in op_is_comp:
                add('mov', arg_to_asm(arg1), '%ebx', comment=comment)
                add('mov', arg_to_asm(arg2), '%eax')
                add('movl', '$0', arg_to_asm(res))
                add('cmp', '%eax', '%ebx')
                add(op_to_asm[op], arg_to_asm(res))
            else:
                add('mov', arg_to_asm(arg1), '%eax', comment=comment)
                add(op_to_asm[op], arg_to_asm(arg2), '%eax')
                add('mov', '%eax', arg_to_asm(res))
        elif op == 'u-':
            comment = res + ' = ' + op[1:] + str(arg1)
            add('mov', '$0', '%eax', comment=comment)
            add('sub', arg_to_asm(arg1), '%eax')
            add('mov', '%eax', arg_to_asm(res))
        elif op == 'u!':
            comment = res + ' = ' + op[1:] + str(arg1)
            add('mov', arg_to_asm(arg1), '%eax', comment=comment)
            add('movl', '$0', arg_to_asm(res))
            add('cmp', '$0', '%eax')
            add('sete', arg_to_asm(res))
        else:
            raise NotImplementedError

    '''
    Almost all TAC's can be directly mapped to a set of ASM instructions.
    Special care has to be taken in 2 cases:
        * 'pop'
            could be a passed parameter in the beginning of the function
            or a return value of a function call
        * 'push'
            could be a passed argument before a function call
            or a return value at the end of a function

    To mitigate this problem we use a state-machine that operates on 
    the TAC operation (with a lookahead to the next operation):

        'fun-def' state (we start in this state):
            'function','pop'
                don't get mapped to ASM instructions. (but we save the names)
            'any other operation'
                means we are at the end of the function definition. We create
                a new stackframe by allocating the appropriate space on the 
                stack and saving the old base pointer.
                'n' parameters are now on the stack in the range
                    8(%ebp) to ((n+2)*4)(%ebp)
                and 'n' local variables are now in the range 
                    -4(%ebp) to ((n+1)*-4)(%ebp)
                the next and final state is 'fun-body'

        'fun-body' state:
            'push'
                could be a argument push, or return value. Thus we look to the
                next operation. If it is a return operation we know that we
                have to move the result into the '%eax' register. Otherwise we
                just push the argument (and save its name).
            'call'
                we generate a 'call' ASM instruction and reset the stack pointer
                we also generate a nice comment with the arguments we pushed 
                beforehand. By looking at the next operation we also know if
                the function returns a value.
            'pop'
                this has to be a return value from a function call (the other
                type of 'pop' only happens in function definitions). Thus we
                just assign the value of '%eax' to the register.
            'any other operation'
                uses the simple mapping defined in the 'to_assembly' function
    '''
    register_to_stack = None
    state, fname, params = 'fun-def', None, []
    line = 0
    args = []
    while line < len(code):
        tac = code[line]
        op, arg1, _, res = tac

        if state == 'fun-def':
            if op == 'function':
                fname = res
            elif op == 'pop':
                params.append(res)
            else:
                register_to_stack = gen_stack_mapping(code, params)
                registersinframe = len(register_to_stack) - len(params)
                # label
                add(fname + ':\t', indent=False, comment='%d params already on stack' % len(params))
                for var in params:
                    add(None, comment=var.rjust(5) + ' := ' + arg_to_asm(var))
                # stack frame
                add('push', '%ebp')
                add('mov', '%esp', '%ebp')
                add('sub', '$' + str(registersinframe * 4), '%esp',
                    comment='make space on stack for %d local registers' % registersinframe)
                for var in register_to_stack:
                    if var not in params:
                        add(None, comment=var.rjust(5) + ' := ' + arg_to_asm(var))
                add(None)
                state = 'fun-body'
                continue

        elif state == 'fun-body':
            if op == 'push':
                nextop, _, _, _ = code[line + 1]
                if nextop == 'return':
                    add('mov', arg_to_asm(arg1), '%eax', comment='return ' + str(arg1))
                    args = []
                else:
                    args.append(arg1)
                    add('push', arg_to_asm(arg1))
            elif op == 'call':
                nextop, _, _, nextret = code[line + 1]
                retvalue = (nextret + ' := ') if nextop == 'pop' else ''
                comment = retvalue + res + '(' + ','.join([str(el) for el in reversed(args)]) + ')'
                add('call', res, comment=comment)
                if len(args) > 0:
                    add('add', '$' + str(len(args) * 4), '%esp')
                args = []
            elif op == 'pop':
                add('mov', '%eax', arg_to_asm(res))
            else:
                to_assembly(*tac)

        line += 1


def codetoassembly(code, verbose=0, assemblyfile=None):
    assembly = ['.globl main', '.text']
    fun_ranges = function_ranges2(code)
    for _, start, end in fun_ranges:
        fun_to_asm(code[start:end], assembly)

    if verbose > 0:  # pragma: no cover
        print('\n' + ' GNU Assembly '.center(40, '#'))
        print('\n'.join(map(str, assembly)))

    if assemblyfile is not None:  # pragma: no cover
        if verbose > -1:
            print('Writing assembly to: \'%s\'' % assemblyfile)
        with open(assemblyfile, 'w') as f:
            f.write('\n'.join(map(str, assembly)))
            f.write('\n')

    return assembly


if __name__ == '__main__':
    import argparse
    from .parser import parsefile
    from .three import asttothree
    from .bb import threetobbs
    from .lvn import lvn
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The *.mc file to convert to GNU Assembly")
    parser.add_argument('--lvn', '-l', action='count', default=False)
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()
    bbs = threetobbs(
        asttothree(
            parsefile(
                args.filename,
                verbose=args.verbose - 2),
            verbose=args.verbose - 1),
        verbose=0 if args.lvn else args.verbose)
    if args.lvn:
        bbs = lvn(bbs, verbose=args.verbose)
    code = [tac for bb in bbs for tac in bb]
    codetoassembly(code, args.verbose + 1, args.filename + '.s')
