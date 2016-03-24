from three import printthree


def threetobbs(threes, verbose=0):
    # find leaders by instruction line
    leaders = set([0])
    for line, three in enumerate(threes):
        op = three[0]
        if op == 'label':
            leaders.add(line)
        if op in ['jump', 'jumpfalse']:
            leaders.add(line + 1)

    # generate basic blocks for every leader
    bbs = []
    currentblock = []
    for line, three in enumerate(threes):
        if line in leaders and len(currentblock) > 0:
            bbs.append(currentblock)
            currentblock = []
        currentblock.append(three)
    bbs.append(currentblock)

    if verbose > 0:
        print('\n' + ' Basic Blocks '.center(40, '#'))
        printbbs(bbs)
    return bbs


def printbbs(bbs, nice=True):
    for i, bb in enumerate(bbs):
        print('Basic Block #%i' % i)
        printthree(bb, nice)
        print('\n')

if __name__ == '__main__':
    import argparse
    from parser import parsefile
    from three import asttothree
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The *.mc file to translate to basic blocks")
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()
    bbs = threetobbs(
        asttothree(
            parsefile(
                args.filename,
                verbose=args.verbose - 1),
            verbose=args.verbose),
        verbose=1)
