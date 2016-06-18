#!/usr/bin/python

from subprocess import call

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The *.mc file to compile")
    parser.add_argument('--lvn', '-l', action='count', default=False)
    parser.add_argument('--verbose', '-v', action='count', default=0)
    parser.add_argument('--execute', '-e', action='count', default=0)
    parser.add_argument('--debug', '-d', action='count', default=False)
    args = parser.parse_args()
    lvn = ['--lvn'] if args.lvn else []
    verbose = ['-' + ('v' * args.verbose)] if args.verbose else []
    pycall = ['python', '-m', 'src.assembler', args.filename] + lvn + verbose
    gcc = ['gcc', '-o', args.filename + '.bin', args.filename + '.s', 'assembler/lib.c', '-m32']
    if args.debug:
        gcc.insert(1, '-gdwarf-3')
    run = [args.filename + '.bin']
    cmds = [pycall, gcc] + ([run] if args.execute else [])
    for cmd in cmds:
        print(' '.join(cmd))
        call(cmd)
