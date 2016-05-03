opcode = [
    'assign',     # 00
    'jump',       # 01
    'jumpfalse',  # 02
    '<=',         # 03
    '>=',         # 04
    '==',         # 05
    '!=',         # 06
    '<',          # 07
    '>',          # 08
    '+',          # 09
    '-',          # 10
    '*',          # 11
    '/',          # 12
    '%',          # 13
    'u-',         # 14
    '!',          # 15
]


def bbs_to_bytecode(bbs):
    # flatten basic blocks
    code = [instr for bb in bbs for instr in bb]

    # remove label instructions but remember line number of labels
    label_to_line = {}
    linestoremove = []
    for linenum, (op, _, _, result) in enumerate(code):
        if op != 'label':
            continue
        label_to_line[result] = linenum - len(linestoremove)
        linestoremove.append(linenum)
    code = [instr for linenum, instr in enumerate(code) if linenum not in linestoremove]

    mem = []
    arg_to_mem = {}

    def memloc(arg):
        if arg is None:
            return None
        if arg in arg_to_mem:
            return arg_to_mem[arg]
        arg_to_mem[arg] = len(arg_to_mem)
        if type(arg) is str:
            if arg.startswith('default-'):
                mem.append(0)
            else:
                mem.append(None)
        else:
            mem.append(arg)
        return arg_to_mem[arg]

    # rewrite instructions with opcodes
    # line number for jumps instead of labels
    # memlocations instead of registernames
    for i, (op, arg1, arg2, result) in enumerate(code):
        if op == 'jump' or op == 'jumpfalse':
            result = label_to_line[result]
            arg1, arg2 = (memloc(el) for el in [arg1, arg2])
        else:
            arg1, arg2, result = (memloc(el) for el in [arg1, arg2, result])
        if op == '-' and arg2 is None:
            op = opcode.index('u-')
        else:
            op = opcode.index(op)
        code[i][0], code[i][1], code[i][2], code[i][3] = op, arg1, arg2, result

    return code, mem, arg_to_mem

def generate_bytecode(bbs, bcfile, verbose=0):
    if len(bbs) == 0:
        return
    code, mem, arg_to_mem = bbs_to_bytecode(bbs)
    mem_to_arg = {k: v for v, k in arg_to_mem.items()}

    with open(bcfile,'w') as f:
        f.write('%d %d\n' % (len(mem), len(code)))
        for i in range(len(mem)):
            name = str(mem_to_arg[i])
            val = 0 if mem[i] is None else mem[i]
            f.write('%s %s\n' % (name,val))
        for op, arg1, arg2, result in code:
            f.write(' '.join([str(-1 if el is None else el) for el in [op,arg1,arg2,result]])+'\n')


def run(bbs, verbose=0):
    if len(bbs) == 0:
        return {}

    code, mem, arg_to_mem = bbs_to_bytecode(bbs)

    pc = 0
    end = len(code) - 1
    while pc <= end:
        op, arg1, arg2, result = code[pc]
        if op == 0:
            mem[result] = mem[arg1]
        elif op == 1:
            pc = result
            continue
        elif op == 2:
            if not mem[arg1]:
                pc = result
                continue
        elif op == 3:
            mem[result] = mem[arg1] <= mem[arg2]
        elif op == 4:
            mem[result] = mem[arg1] >= mem[arg2]
        elif op == 5:
            mem[result] = mem[arg1] == mem[arg2]
        elif op == 6:
            mem[result] = mem[arg1] != mem[arg2]
        elif op == 7:
            mem[result] = mem[arg1] < mem[arg2]
        elif op == 8:
            mem[result] = mem[arg1] > mem[arg2]
        elif op == 9:
            mem[result] = mem[arg1] + mem[arg2]
        elif op == 10:
            mem[result] = mem[arg1] - mem[arg2]
        elif op == 11:
            mem[result] = mem[arg1] * mem[arg2]
        elif op == 12:
            mem[result] = mem[arg1] // mem[arg2]
        elif op == 13:
            mem[result] = mem[arg1] % mem[arg2]
        elif op == 14:
            mem[result] = -mem[arg1]
        elif op == 15:
            mem[result] = not mem[arg1]
        pc += 1

    vals = {arg: mem[mempos] for arg, mempos in arg_to_mem.items()
            if type(arg) is str and not arg.startswith('.t')}
    if verbose > 0:
        print('\n' + ' VM result '.center(40, '#'))
        print(vals)
    if verbose > 1:
        print('\n' + ' VM bytecode '.center(40, '#'))
        mem_to_arg = {k: v for v, k in arg_to_mem.items()}
        for linenum, (op, arg1, arg2, res) in enumerate(code):
            op = opcode[op]
            if op == 'assign':
                res = mem_to_arg[res]
                arg1 = mem_to_arg[arg1]
            elif op == 'jumpfalse':
                arg1 = mem_to_arg[arg1]
            elif op == 'jump':
                pass
            else:
                res = mem_to_arg[res]
                arg1 = mem_to_arg[arg1]
                arg2 = mem_to_arg[arg2]
            if res is None:
                res = ''
            if arg1 is None:
                arg1 = ''
            if arg2 is None:
                arg2 = ''
            res, arg1, arg2 = str(res), str(arg1), str(arg2)
            print('{:>3}\t{:10}\t{:10}\t{:10}\t{:10}'.format(str(linenum), op, arg1, arg2, res))
    return vals

if __name__ == '__main__':
    import argparse
    from .parser import parsefile
    from .three import asttothree
    from .bb import threetobbs
    from .lvn import lvn
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The *.mc file to run.")
    parser.add_argument('--lvn', '-l', action='count', default=False)
    parser.add_argument('--bcfile', '-b', default=None)
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()
    bbs = threetobbs(
        asttothree(
            parsefile(
                args.filename,
                verbose=args.verbose - 2),
            verbose=args.verbose - 1),
        verbose=args.verbose)
    if args.lvn:
        bbs = lvn(bbs, verbose=1)
    if args.bcfile is not None:
        generate_bytecode(bbs, args.bcfile, args.verbose + 1)
    else:
        run(bbs, args.verbose + 1)
