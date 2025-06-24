"""
Drive System Print
==================

A common printing statement to be used by all modules, in case the CLI is being used...
"""

def dsprint(*args, sep=' ', end='\n', file=None, flush=False):
    import drivesystemcli as dscli
    cli = dscli.GET_CLI()
    if cli.is_initialised:
        cli.print_to_terminal(sep.join(map(str,args)), end=end)
        return

    print(*args, sep=sep,end=end,file=file,flush=flush)