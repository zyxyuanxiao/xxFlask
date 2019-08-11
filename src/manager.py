#!/usr/bin/python
# coding=utf-8

import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "args error,python manager.py module"
        exit(0)

    server = sys.argv[1]
    run_mode = 'local_run' if len(sys.argv) < 3 else sys.argv[3]
    m = __import__('{}.{}'.format(server, run_mode))
    m.__dict__[run_mode].__dict__[run_mode]()
