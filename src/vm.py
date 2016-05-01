operations = {
    '<=': lambda x, y: x <= y,
    '>=': lambda x, y: x >= y,
    '==': lambda x, y: x == y,
    '!=': lambda x, y: x != y,
    '<': lambda x, y: x < y,
    '>': lambda x, y: x > y,
    '+': lambda x, y: x + y,
    '-': lambda x, y: x - y,
    '*': lambda x, y: x * y,
    '/': lambda x, y: x // y,
    '%': lambda x, y: x % y,
    'u!': lambda x: not x,
    'u-': lambda x: - x,
    '!': None
}


def run(bbs, verbose=0):
    if len(bbs) == 0:
        return {}

    # program counter [block,line]
    pc = [0, 0]
    end = [len(bbs) - 1, len(bbs[-1]) - 1]
    vals = {'default-int': 0, 'default-float': 0.0}

    def toval(arg):
        if type(arg) is str:
            return vals[arg]
        return arg

    labels = {}
    for blocknum, bb in enumerate(bbs):
        for linenum, (op, _, _, result) in enumerate(bb):
            if op != 'label':
                continue
            labels[result] = (blocknum, linenum)

    while True:
        op, arg1, arg2, result = bbs[pc[0]][pc[1]]
        if op == 'assign':
            vals[result] = toval(arg1)
        if op == 'jump':
            pc = list(labels[result])
            continue
        if op == 'jumpfalse':
            if not toval(arg1):
                pc = list(labels[result])
                continue
        if op in operations:
            isunop = op == '!' or (op == '-' and arg2 is None)
            if isunop:
                vals[result] = operations['u' + op](toval(arg1))
            else:
                vals[result] = operations[op](toval(arg1), toval(arg2))

        if pc == end:
            break
        # next line
        pc[1] += 1
        if pc[1] >= len(bbs[pc[0]]):
            pc[0] += 1
            pc[1] = 0

    tmpvars = [el for el in vals if el.startswith('.t')] + ['default-int', 'default-float']
    vals = {el: vals[el] for el in vals if el not in tmpvars}

    if verbose > 0:
        print('\n' + ' VM result '.center(40, '#'))
        print(vals)
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
    run(bbs, args.verbose + 1)
