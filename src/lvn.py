from .bb import printbbs


def localvaluenumbering(basicblock):
    values = {}
    for code in basicblock:
        op, arg1, arg2, res = code
        if op in ['jump', 'label']:
            continue
        if op == 'jumpfalse':
            code[1] = values[str(arg1)]
            continue

        valueargs = []
        for arg in [arg1, arg2]:
            if str(arg) not in values:
                values[str(arg)] = arg
            valueargs.append(values[str(arg)])

        e = (op, valueargs[0], valueargs[1])
        if op in ['+', '*', '==', '!=']:
            if str(valueargs[0]) > str(valueargs[1]):
                e = (op, valueargs[0], valueargs[1])
            else:
                e = (op, valueargs[1], valueargs[0])
        elif op == 'assign':
            e = str(arg1)

        if e not in values:
            values[res] = res
            values[e] = res
            if op != 'assign':
                code[1] = valueargs[0]
                code[2] = valueargs[1]
        else:
            # for el in values:
                # print(el,values[el])
            # print('replace: [%s,%s,%s,%s] with %s' % (op,arg1,arg2,res,values[e]))
            values[res] = values[e]
            if op != 'assign':
                code[0] = 'assign'
                code[2] = None
            code[1] = values[e]


def removeunusedlines(bb):
    usedtemps = []
    for op, arg1, arg2, res in bb:
        if op in ['jump', 'label']:
            continue
        for arg in [arg1, arg2]:
            if arg is None:
                continue
            if type(arg) is not str:
                continue
            if not arg.startswith('.t'):
                continue
            usedtemps.append(arg)

    unneccesarylines = []
    for i, (op, arg1, arg2, res) in enumerate(bb):
        if op in ['jump', 'jumpfalse', 'label']:
            continue
        if not res.startswith('.t'):
            continue
        if res in usedtemps:
            continue
        unneccesarylines.append(i)
    for i in reversed(unneccesarylines):
        del bb[i]


def lvn(bbs, verbose=0):
    for bb in bbs:
        localvaluenumbering(bb)
        # cleanup
        removeunusedlines(bb)
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
