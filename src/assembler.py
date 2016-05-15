from parsimonious import Grammar, NodeVisitor
from .utils import function_ranges2, op_uses_values, op_sets_result, simplify_op, printcode, lib_sigs, op_is_comp


op_to_asm = {
    '+': 'add',
    '-': 'sub',
    '*': 'mull',
    '/': 'div',
    '%': 'div',
    '==': 'sete',
    '!=': 'setne',
    '<=': 'setle',
    '>=': 'setge',
    '<': 'setl',
    '>': 'setg',
}

# TODO fundef is unnecessary?
tac_grammar = Grammar('''
    blocks  = block*
    block   = fundef / return / funcall
    fundef = "function:" linenum "," args*
    args    = "pop:" linenum ","
    return  = ("push:" linenum ",")? "return:" linenum ","
    params  = "push:" linenum ","
    funcall = params* "call:" linenum "," ("pop:" linenum ",")?
    linenum = ~"\d+"
''')


class AssemblyHelper(NodeVisitor):
    grammar = tac_grammar

    '''
    def visit_blocks(self, node, childs):
        return childs

    def visit_op(self, node, childs):
        return node.text

    '''

    def visit_block(self, node, childs):
        return childs[0]

    def visit_fundef(self, node, childs):
        start, args = [childs[i] for i in [1, 3]]
        end = start if args is None else max(args)
        return ('fundef', start, end + 1)

    def visit_args(self, node, childs):
        line = childs[1]
        return line

    def visit_return(self, node, childs):
        ret, end = [childs[i] for i in [0, 2]]
        ret = None if ret is None else ret[0][0]
        start = end if ret is None else ret
        return ('return', start, end + 1)

    def visit_params(self, node, childs):
        line = childs[1]
        return line

    def visit_funcall(self, node, childs):
        params, line, ret = [childs[i] for i in [0, 2, 4]]
        ret = None if ret is None else ret[0][0]
        start = line if params is None else min(params)
        end = line if ret is None else max(line, ret)
        return ('funcall', start, end + 1)

    def visit_otherop(self, node, childs):
        line = childs[2]
        return ('normal', line, line + 1)

    def visit_linenum(self, node, childs):
        return int(node.text)

    def generic_visit(self, node, childs):
        res = [x for x in childs if x is not None]
        if len(res) == 0:
            return None
        return res


def is_var_or_temp(arg):
    return type(arg) is str


def fillblocks_with_normal(blocks):
    oldblocks = [el for el in blocks]
    for i in reversed(range(len(oldblocks) - 1)):
        _, _, end = oldblocks[i]
        _, start, _ = oldblocks[i + 1]
        if end < start:
            blocks.insert(i + 1, ('normal', end, start))
    assert(set(range(blocks[-1][2])) == set([el for _, start, end in blocks for el in range(start, end)]))


def gen_reg_mapping(code):
    currmap = {}
    for tac in code:
        op, arg1, arg2, res = tac
        op = simplify_op(op, arg2)
        if op not in op_uses_values and op not in op_sets_result:
            continue
        for argpos in op_uses_values[op] + ([3]if op in op_sets_result else[]):
            arg = tac[argpos]
            if not is_var_or_temp(arg):
                continue
            if arg in currmap:
                continue
            currmap[arg] = len(currmap)
    return currmap


def fun_to_asm(code, assembly):
    register_to_stack = gen_reg_mapping(code)

    def arg_to_asm(arg, offset=0):
        if is_var_or_temp(arg):
            addr = register_to_stack[arg] * 4 + offset
            return '%d(%%esp)' % addr
        else:
            return '$%d' % arg

    def add(op, arg1=None, arg2=None, comment=None, indent=True):
        if op is None:
            assembly.append('\t'.ljust(25) + ('' if comment is None else '\t# ' + comment))
            return
        indent = '\t' if indent else ''
        instr = indent + op.ljust(5) + '\t' + ', '.join([el for el in [arg1, arg2] if el is not None])
        instr = instr.ljust(25)
        if comment is not None:
            instr += '\t# ' + comment
        assembly.append(instr)

    def expand_if_necc(finalop, x, y, comment=None, sort=False):
        need_accum = is_var_or_temp(x) and is_var_or_temp(y)
        x, y = [arg_to_asm(el) for el in [x, y]]
        if sort:
            x, y = sorted([x, y])
        if need_accum:
            add('mov', x, '%eax', comment=comment)
            add(finalop, '%eax', y)
        else:
            add(finalop, x, y, comment=comment)

    def to_assembly_normal(tac):
        op, arg1, arg2, res = tac
        sop = simplify_op(op, arg2)

        if op == 'jump':
            add('jmp', res)
        elif op == 'jumpfalse':
            add('cmp', '$0', arg_to_asm(arg1), comment='if(' + str(arg1) + '==0) goto ' + res)
            add('je', res)
        elif op == 'label':
            add(res + ':', indent=False)
        elif op == 'function':
            raise Exception
        elif op == 'call':
            add('call', res)
        elif op == 'end-fun':
            add(None)
        elif op == 'return':
            raise Exception
        elif op == 'push':
            add('push', arg_to_asm(arg1))
        elif op == 'pop':
            add('push', arg_to_asm(res))
        elif op == 'assign':
            expand_if_necc('movl', arg1, res, comment=res + ' := ' + str(arg1))
        elif op == '*':
            # TODO
            add('imul', arg_to_asm(arg1), arg_to_asm(arg2), arg_to_asm(res))
        elif sop == 'binop':
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
        elif sop == 'unop':
            # TODO
            assembly.append('normal ' + str(tac))
        elif sop == 'unop':
            assembly.append('normal ' + str(tac))
        else:
            assembly.append('normal ' + str(tac))

    def to_assembly_fundef(fun, stack_regs, param_num):
        add(fun + ':', indent=False)
        add('sub', '$' + str(stack_regs * 4), '%esp',
            comment='make space on stack for %d local registers (%d params already on stack)' % (stack_regs, param_num))
        for locs, stacknum in register_to_stack.items():
            add(None, comment=locs.rjust(5) + ' := ' + str(stacknum * 4) + '(%esp)')
        # move pushed arguments into local stack space
        # TODO could use them directly
        for i in range(param_num):
            add('mov', '%d(%%esp)' % ((stack_regs + 1 + i) * 4), '%eax')
            add('mov', '%eax', '%d(%%esp)' % (i * 4))
        add(None)

    def to_assembly_pop_eax(reg):
        add('mov', '%eax', arg_to_asm(reg))

    def to_assembly_push_eax(reg):
        add('mov', arg_to_asm(reg), '%eax', comment='return ' + str(reg))

    def to_assembly_make_frame(callname, args, retval):
        fstr = callname + '(' + ','.join([str(el) for el in args]) + ')'
        comment = fstr if retval is None else (retval + ' := ' + fstr)
        add(None)
        add('push', '%ebp', comment=comment)
        add('mov', '%esp', '%ebp')

    def to_assembly_destroy_frame(param_num):
        if param_num > 0:
            add('add', '$' + str(param_num * 4), '%esp')
        add('pop', '%ebp')

    def to_assembly_return(stack_regs):
        add('add', '$' + str(stack_regs * 4), '%esp')
        add('ret')

    grammarstring = []
    for line, (op, _, _, _) in enumerate(code):
        if op in ['function', 'pop', 'push', 'return', 'call']:
            grammarstring.append(op + ':' + str(line) + ',')
    grammarstring = ''.join(grammarstring)
    parsetree = tac_grammar.parse(grammarstring)
    blocks = AssemblyHelper().visit(parsetree)
    fillblocks_with_normal(blocks)
    # print(blocks)

    btype, fundefstart, fundefend = blocks[0]
    assert(btype == 'fundef')
    param_num = fundefend - fundefstart - 1
    # the parameters of this function are already on the stack (TODO maybe reversed?)
    # stack_registers_needed = len(register_to_stack) - param_num
    stack_registers_needed = len(register_to_stack)
    _, _, _, fname = code[0]
    to_assembly_fundef(fname, stack_registers_needed, param_num)
    for btype, start, end in blocks[1:]:

        if btype == 'normal':
            for tac in code[start:end]:
                to_assembly_normal(tac)

        if btype == 'funcall':
            # gather info about call
            callname, args, retval = None, [], None
            for op, arg1, _, res in code[start:end]:
                if op == 'pop':
                    retval = res
                if op == 'push':
                    args.append(arg1)
                if op == 'call':
                    callname = res

            to_assembly_make_frame(callname, args, retval)
            for tac in code[start:end]:
                op, arg1, _, _ = tac
                if op == 'push':
                    add('push', arg_to_asm(arg1, offset=4))
                elif op != 'pop':
                    to_assembly_normal(tac)
            to_assembly_destroy_frame(len(args))
            if retval is not None:
                to_assembly_pop_eax(retval)
            add(None)

        if btype == 'return':
            for tac in code[start:end]:
                op, reg, _, _ = tac
                if op == 'push':
                    to_assembly_push_eax(reg)
                elif op == 'return':
                    to_assembly_return(stack_registers_needed)


def bbstoassembly(bbs, verbose=0, assemblyfile=None):
    assembly = ['.globl main', '.text']
    code = [tac for bb in bbs for tac in bb]
    if verbose > 0:
        printcode(code)
    fun_ranges = function_ranges2(code)
    for _, start, end in fun_ranges:
        fun_to_asm(code[start:end], assembly)

    if verbose > 0:
        print('\n' + ' GNU Assembly '.center(40, '#'))
        print('\n'.join(assembly))

    if assemblyfile is not None:
        print('Writing assembly to: \'%s\'' % assemblyfile)
        with open(assemblyfile, 'w') as f:
            f.write('\n'.join(assembly))
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
    # TODO convert bbs to code
    assemblyfile = args.filename + '.s'
    bbstoassembly(bbs, args.verbose + 1, assemblyfile)
