#!/usr/bin/python

from common import utility as u
import re


def do_compile():
    if u.is_client():
        bin_path = u.get_bin('protoc')
        input_path = u.get_res('Sources/Proto')
        python_out = u.get_script('res/pb')
        pb_out = u.get_res('AssetBundle/Data/descriptor.bytes')
    else:
        bin_path = u.get_script('../install/protoc')
        if u.is_darwin_server():
            bin_path = u.get_bin_in_os_path('protoc')
        input_path = u.get_temp_path('all_protos')
        python_out = u.get_script('../../protocol')
        pb_out = u.get_script('../../protocol/descriptor')

        u.clean_dir(input_path)

        for path, recursive in [
            (u.get_script('../../proto'), False),
            (u.get_script('../../proto/proto_clt'), True)
        ]:
            u.sync_folder(path, input_path, src_files=u.get_files(path, ['proto'], recursive=recursive),
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
            u.import_name(file, python_out)) for file in u.get_files(python_out, ['py'])]))

        if u.is_client():
            csharp_out = u.get_res('Scripts/Client/Message/generated')

            u.mkdir(csharp_out)
            u.del_files(u.get_files(csharp_out, ['cs']))

            tmp_input_path = u.get_temp_path('proto')
            u.clean_dir(tmp_input_path)

            u.sync_folder(input_path, tmp_input_path, src_files=u.get_files(input_path, ['proto']))
            proto_files = u.get_files(tmp_input_path, ['proto'], recursive=False)
            field_regex = re.compile(r'''\[\((fc|evc)\)[^\]]+\]''')
            message_regex = re.compile(r'''option\s+\(ec\)[^;]+;''')
            for proto_file in u.get_files(tmp_input_path, ['proto'], recursive=False):
                content = u.read(proto_file)
                content = field_regex.sub("", content)
                content = message_regex.sub("", content)
                u.write(proto_file, content)

            cmd_args_path = u.get_temp_path("cmd_args")
            u.write(cmd_args_path, "\n".join(proto_files))
            u.execute(bin_path,
                      '--csharp_out=' + csharp_out,
                      '--proto_path=' + tmp_input_path,
                      '-o', pb_out,
                      "@" + cmd_args_path)

        u.touch(tag)


def main():
    do_compile()


if __name__ == '__main__':
    main()
