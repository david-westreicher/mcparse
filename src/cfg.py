def bbstocfg(bbs, verbose=0, dotfile=None):
    cfg = {i: set() for i in range(len(bbs))}
    labeltoblock = {}
    for i, bb in enumerate(bbs):
        for op, _, _, label in bb:
            if op != 'label':
                continue
            labeltoblock[label] = i

    for i, bb in enumerate(bbs):
        jumptonextblock = True
        for op, _, _, jumplabel in bb:
            if op not in ['jump', 'jumpfalse']:
                continue
            cfg[i].add(labeltoblock[jumplabel])
            if op == 'jump':
                jumptonextblock = False

        if jumptonextblock and i + 1 < len(bbs):
            cfg[i].add(i + 1)

    if verbose > 0:
        print('\n' + ' Control Flow Graph '.center(40, '#'))
        for el in cfg:
            print(str(el) + '\t->\t' + ', '.join([str(el) for el in cfg[el]]))

    if dotfile is not None:
        makeDotFile(bbs, cfg, dotfile)

    return cfg


def makeDotFile(bbs, cfg, dotfile):
    import cgi
    from .three import prettythreestr
    with open(dotfile, 'w') as f:
        f.write('digraph R {\n')
        f.write('node [shape=plaintext]\n')
        for i, bb in enumerate(bbs):
            html = ['<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0">']
            for op, arg1, arg2, res in bb:
                html.append('<TR>')
                parts = cgi.escape(prettythreestr(op, arg1, arg2, res)).split('\t')
                for part in parts:
                    html.append('<TD>' + part + '</TD>')
                for _ in range(5 - len(parts)):
                    html.append('<TD></TD>')
                html.append('</TR>')
            html.append('</TABLE>>')
            f.write(str(i) + ' [label=' + '\n'.join(html) + '];\n')
        for el in cfg:
            children = cfg[el]
            for child in children:
                f.write('%s -> %s;\n' % (el, child))
        f.write('}')

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
