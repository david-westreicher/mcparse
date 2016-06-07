from .utils import function_ranges


def bbstocallgraph(bbs, verbose=0, dotfile=None):
    # create callgraph
    fun_ranges = function_ranges(bbs, asDic=True)
    callgraph = {name: set() for name in fun_ranges}
    for currfun, (start, end) in fun_ranges.items():
        for bb in bbs[start:end]:
            for op, _, _, fname in bb:
                if op == 'call':
                    callgraph[currfun].add(fname)

    # global implicitly calls main in the end
    if 'main' in fun_ranges and '__global__' in fun_ranges:
        callgraph['__global__'].add('main')

    if verbose > 0:  # pragma: no cover
        print('\n' + ' Call Graph '.center(40, '#'))
        for el in callgraph:
            print(str(el).ljust(10) + '\t->\t' + (', '.join([str(el) for el in callgraph[el]])))

    if dotfile is not None:  # pragma: no cover
        from .utils import makeDotFile
        makeDotFile(dotfile, bbs)

    return callgraph

if __name__ == '__main__':
    import argparse
    from .parser import parsefile
    from .three import asttothree
    from .bb import threetobbs
    from .lvn import lvn
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The *.mc file to convert into a Call Graph")
    parser.add_argument('dotfile', default=None)
    parser.add_argument('--lvn', '-l', action='count', default=False)
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()
    bbs = threetobbs(
        asttothree(
            parsefile(
                args.filename,
                verbose=args.verbose - 2),
            verbose=args.verbose - 1),
        verbose=1 if not args.lvn else 0)
    if args.lvn:
        bbs = lvn(bbs, verbose=1)
    bbstocallgraph(bbs, args.verbose + 1, args.dotfile)
