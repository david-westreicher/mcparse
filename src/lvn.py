from .bb import printbbs
from .utils import op_commutative, op_sets_result, op_uses_values, simplify_op


def localvaluenumbering(basicblock):
    values = {}
    for code in basicblock:
        op, arg1, arg2, res = code
        simple_op = simplify_op(op)
        if simple_op not in op_uses_values:
            continue

        # put constants into the map
        for argpos in op_uses_values[simple_op]:
            arg = code[argpos]
            if str(arg) not in values:
                values[str(arg)] = arg

        # replace used arguments with their map-value
        valargs = []
        for arg in op_uses_values[simple_op]:
            valarg = values[str(code[arg])]
            code[arg] = valarg
            valargs.append(valarg)

        newval = None
        if simple_op in ['binop', 'unop']:
            if op in op_commutative:
                valargs.sort(key=lambda x: str(x))
            arghash = (op,) + tuple(valargs)

            if arghash not in values:
                values[arghash] = res
            else:
                newval = values[arghash]
                code[0] = 'assign'
                code[1] = newval
                code[2] = None
                code[3] = res
        if simple_op in ['assign']:
            newval = valargs[0]
        if newval is not None:
            values[res] = newval


def removeunusedlines_block(bb):
    usedtemps = set()
    for code in bb:
        op, _, _, _ = code
        op = simplify_op(op)
        if op not in op_uses_values:
            continue
        for argpos in op_uses_values[op]:
            arg = code[argpos]
            if type(arg) is str and arg.startswith('.t'):
                usedtemps.add(arg)

    unneccesarylines = []
    for i, (op, _, _, res) in enumerate(bb):
        if simplify_op(op) not in op_sets_result:
            continue
        if res.startswith('.t') and res not in usedtemps:
            unneccesarylines.append(i)
    for i in reversed(unneccesarylines):
        del bb[i]
    return len(bb) == 0


def removeunusedlines(bbs):
    unneccesaryblocks = []
    for blocknum, bb in enumerate(bbs):
        if removeunusedlines_block(bb):
            unneccesaryblocks.append(blocknum)
    for blocknum in reversed(unneccesaryblocks):
        del bbs[blocknum]


def lvn(bbs, verbose=0):
    for bb in bbs:
        localvaluenumbering(bb)
        # cleanup
    removeunusedlines(bbs)
    if verbose > 0:
        print('\n' + ' Local Value Numbering '.center(40, '#'))
        printbbs(bbs)
    return bbs

if __name__ == '__main__':
    import argparse
    from .parser import parsefile
    from .three import asttothree
    from .bb import threetobbs, printbbs
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The *.mc file to translate to basic codes")
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()
    bbs = threetobbs(
        asttothree(
            parsefile(
                args.filename,
                verbose=args.verbose - 1),
            verbose=args.verbose),
        verbose=1)
    bbs = lvn(bbs, verbose=1)
