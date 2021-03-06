from .utils import makeDotFile


def bbstocfg(bbs, verbose=0, dotfile=None):
    cfg = {i: set() for i in range(len(bbs))}
    labeltoblock = {}
    funblocks = set()
    for i, bb in enumerate(bbs):
        for op, _, _, label in bb:
            if op == 'label':
                labeltoblock[label] = i
            if op == 'function':
                funblocks.add(i)

    for i, bb in enumerate(bbs):
        nextblock = i + 1
        for op, _, _, jumplabel in bb:
            if op in ['jump', 'jumpfalse']:
                cfg[i].add(labeltoblock[jumplabel])
            if op == 'jump':
                nextblock = -1

        if op != 'end-fun' and nextblock > 0 and nextblock < len(bbs) and nextblock not in funblocks:
            cfg[i].add(nextblock)

    if verbose > 0:  # pragma: no cover
        print('\n' + ' Control Flow Graph '.center(40, '#'))
        for el in cfg:
            print(str(el) + '\t->\t' + ', '.join([str(el) for el in cfg[el]]))

    if dotfile is not None:  # pragma: no cover
        makeDotFile(dotfile, bbs, cfg)

    return cfg

if __name__ == '__main__':
    import argparse
    from .parser import parsefile
    from .three import asttothree
    from .bb import threetobbs
    from .lvn import lvn
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The *.mc file to convert into a Control Flow Graph and Basic Blocks")
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
    bbstocfg(bbs, args.verbose + 1, args.dotfile)
