def toc(bbs, verbose=0):
    allvars = set()
    def tovar(arg):
        if type(arg) is str:
            if arg.startswith('.t'):
                allvars.add('temp'+arg[1:])
                return 'temp'+arg[1:]
            if arg.startswith('default-'):
                return 0
            allvars.add(arg)
        return arg
    ccode = ['int main(){']
    for bb in bbs:
        for op, arg1, arg2, result in bb:
            if op=='label':
                ccode.append('\t%s: ;' % result)
            elif op=='jump':
                ccode.append('\tgoto %s;' % result)
            elif op=='jumpfalse':
                ccode.append('\tif(!(%s))' % tovar(arg1))
                ccode.append('\t\tgoto %s;' % result)
            elif op=='assign':
                ccode.append('\t%s = %s;' % (tovar(result),tovar(arg1)))
            else:
                ccode.append('\t%s = %s %s %s;' % (tovar(result),tovar(arg1),op,tovar(arg2)))
    ccode.append('}')
    ccode.insert(1,'\tint '+', '.join(allvars)+';')
    if verbose > 0:
        print('\n' + ' VM result '.center(40, '#'))
        print('\n'.join(ccode))
    return ccode

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
    toc(bbs, args.verbose + 1)
