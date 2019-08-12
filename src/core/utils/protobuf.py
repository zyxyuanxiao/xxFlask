#!/usr/bin/python

from common import utility as u
from common import defaults as d
import re
import sys


def do_compile(app):
    bin_path = u.get_script('./utils/protoc')
    input_path = u.get_temp_path('all_protos')
    python_out = u.get_script('./{}/protocol/'.format(app))
    pb_out = u.get_script(python_out + '/descriptor/')
    app_dir = u.get_script('./{}/'.format(app))
    proto_dir = u.get_script('../proto/')
    proto_ctl = u.get_script('./{}/proto/'.format(app))

    u.clean_dir(input_path)

    for path, recursive in [(proto_dir, True), (proto_ctl, True)]:
        u.sync_folder(path, input_path,
                      src_files=u.get_files(path, ['proto'], recursive=recursive),
                      remove_diff=False)

    proto_files = u.get_files(input_path, ['proto'], recursive=True)
    tag = u.gen_tag('protobuf' + str(u.string_hash(input_path)))
    if u.is_ci_mode() or u.compare_mtime(tag, proto_files + [__file__, bin_path]):
        u.clean_dir(python_out)

        cmd_args_path = u.get_temp_path("cmd_args")
        u.write(cmd_args_path, "\n".join(proto_files))
        u.execute(bin_path,
                  '--python_out=' + python_out,
                  '--proto_path=' + input_path,
                  '-o', pb_out,
                  "@" + cmd_args_path)

        u.write(u.join_path(python_out, '__init__.py'), '\n'.join(['import {}'.format(
            u.import_name(f, python_out)) for f in u.get_files(python_out, ['py'])]))

        u.touch(tag)


def main(app_name):
    do_compile(app_name)


if __name__ == '__main__':
    u.initialize(u.dir_name(__file__))
    u.init_env(d.defaults)

    main(sys.argv[1])
