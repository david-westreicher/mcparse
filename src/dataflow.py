from .utils import isvar


def liveness(bbs, cfg, verbose=0):
    uevars = {i: set() for i in range(len(bbs))}
    killed = {i: set() for i in range(len(bbs))}
    for i, block in enumerate(bbs):
        for op, arg1, arg2, result in block:
            if op in ['jump', 'label']:
                continue
            uevars[i] |= set([arg for arg in [arg1, arg2] if isvar(arg)]) - killed[i]
            if op == 'jumpfalse' or not isvar(result):
                continue
            killed[i].add(result)

    def transform(b, livein):
        return uevars[b] | (livein - killed[b])
    inb, outb = worklist(bbs, cfg, lambda: set(), transform, backward=True)

    if verbose > 0:
        printinout(bbs, inb, outb, True)
    if verbose > 1:
        print('uevars: %s' % uevars)
        print('killed: %s' % killed)

    return inb, outb


def invertgraph(cfg):
    pred = {el: set() for el in cfg}
    for parent in cfg:
        for child in cfg[parent]:
            pred[child].add(parent)
    return pred


def worklist(bbs, cfg, initer, transform, backward=False):
    inb = {i: initer() for i in range(len(bbs))}
    outb = {i: initer() for i in range(len(bbs))}
    pred = invertgraph(cfg)
    if backward:
        cfg, pred = pred, cfg

    def gatherinput(b):
        res = initer()
        res |= inb[b]
        for parent in pred[b]:
            res |= outb[parent]
        return res

    w = set([el for el in range(len(bbs))])
    while len(w) > 0:
        b = w.pop()
        inb[b] = gatherinput(b)
        newoutb = transform(b, inb[b])
        if outb[b] != newoutb:
            w |= cfg[b]
        outb[b] = newoutb

    return inb, outb


def printinout(bbs, inb, outb, backward):
    print('\n' + ' Live variable analysis '.center(40, '#'))
    from .three import printthree
    for i, block in enumerate(bbs):
        if not backward:
            print('IN: {%s}' % ', '.join(inb[i]))
        else:
            print('OUT: {%s}' % ', '.join(outb[i]))
        print('Basic Block #%i' % i)
        printthree(block)
        if backward:
            print('IN: {%s}' % ', '.join(inb[i]))
        else:
            print('OUT: {%s}' % ', '.join(outb[i]))
        print('\n')

if __name__ == '__main__':
    import argparse
    from .parser import parsefile
    from .three import asttothree
    from .bb import threetobbs
    from .cfg import bbstocfg
    from .lvn import lvn
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The *.mc file to apply Data Flow Analysis to")
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()
    bbs = threetobbs(
        asttothree(
            parsefile(
                args.filename,
                verbose=args.verbose - 3),
            verbose=args.verbose - 2),
        verbose=args.verbose - 1)
    bbs = lvn(bbs, verbose=1)
    cfg = bbstocfg(bbs, verbose=1)
    liveness(bbs, cfg, verbose=args.verbose+1)
