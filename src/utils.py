def isvar(arg):
    if arg is None:
        return False
    if type(arg) is not str:
        return False
    if arg.startswith('.t'):
        return False
    return True
