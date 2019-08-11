#!/usr/bin/python
# coding=utf-8

import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "args error,python manager.py module"
        exit(0)

    server = sys.argv[1]
    run_module = 'app'
    run_func = 'debug_run'
    m = __import__('{}.{}'.format(server, run_module))
    m.__dict__[run_module].__dict__[run_func]()
