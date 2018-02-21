#!/usr/bin/python3
import sys
import os
sys.path.append('/home/golubev/dev/odoo')
sys.path.append('/home/golubev/dev')
sys.path.append(os.getcwd())
import importlib
import getopt
import inspect
from odoo import fields, models


def print_classes():
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(obj):
            print(obj)


def usage():
    print(
        '''Usage: 
    formgen.py [-h|--help]
    formgen.py <modulename>
    
    -h|--help this screen
    ''')


def main(argv):
    try:
        # opts, args = getopt.getopt(sys.argv[1:], "ho:v", ["help", "output="])
        opts, args = getopt.getopt(sys.argv[1:], "", ["help"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    output = None
    verbose = False
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-o", "--output"):
            output = a
        else:
            assert False, "unhandled option"
    # ...
    if len(args) != 1:
        usage()
        sys.exit(2)
    modname = args[0]
    my_module = importlib.import_module(modname)
    for cls in inspect.getmembers(sys.modules[modname], inspect.isclass):
        if not isinstance(cls[1], models.MetaModel):
            continue
        model = cls[1]._name
        inherit = False
        if not model:
            model = cls[1]._inherit
            inherit = True
        xmlfields = ""
        for member in inspect.getmembers(cls[1]):
            if isinstance(member[1], fields.Field):
                xmlfields += '    <field name="{}"/>\n'.format(member[0])
        xml = '<form model="{model}" {inherits}>\n{fields}</form>'\
            .format(model=model,inherits='inherits=""' if inherit else '', fields=xmlfields)
        print(xml)
    pass


if __name__ == "__main__":
    # execute only if run as a script
    main(sys.argv)