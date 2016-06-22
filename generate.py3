#!/usr/bin/env python3

import sys
import os
import yaml
import json
import re
import base64
from os import path

config = {}

def main(argv):
    if len(argv) < 2:
        print("Usage: %s <main.yml> [config.yaml]" % argv[0])
        exit(1)

    main_file = argv[1]

    if len(argv) >= 3:
        global config
        with open(argv[2]) as file:
            config = yaml.load(file)
        config = process_object(path.dirname(argv[2]), config)

    root_obj = fn_process_file(path.dirname(main_file), path.basename(main_file))
    print(json.dumps(root_obj))

def process_object(cwd, obj):
    if isinstance(obj, dict):
        ret = {}
        for key in obj:
            if key in func_map:
                return func_map[key](cwd, obj[key])
            else:
                ret[key] = process_object(cwd, obj[key])
        return ret

    if isinstance(obj, list):
        return [process_object(cwd, tmp) for tmp in obj]

    return obj


def fn_process_file(cwd, file_name):
    try:
        ret = {}
        with open(path.join(cwd, file_name)) as file:
            ret = yaml.load(file)
        ret = process_object(cwd, ret)
        return ret

    except Exception as e:
        print("Error Processing %s" % path.join(cwd, file_name), file=sys.stderr)
        raise e

def fn_from_folders(cwd, dir_list):
    if not isinstance(dir_list, list):
        return fn_from_folders(cwd, [dir_list])

    ret = {}
    for diritem in dir_list:
        curcwd = path.join(cwd, diritem)

        for file_name in os.listdir(curcwd):
            match = re.search(r'(.*)\.yaml$', file_name)
            if match:
                key = match.group(1)
                if key in ret:
                    raise ValueError("'%s' is already declared" % key)
                ret[key] = fn_process_file(curcwd, file_name)

    return ret

def fn_file_as_base64(cwd, file_name):
    file_name = path.join(cwd, file_name)
    with open(file_name, "rb") as file:
        return base64.b64encode(file.read()).decode("UTF-8")

def fn_get_config(cwd, key_path):
    if not isinstance(key_path, list):
        return fn_get_config(cwd, [key_path])

    ret = config
    for key in key_path:
        ret = ret[key]

    return ret

def fn_merge(cwd, obj_list):
    ret = {}
    for item in obj_list:
        item = process_object(cwd, item)
        for key in item:
            if key in ret:
                raise ValueError("'%s' is already declared" % key)
            ret[key] = item[key]

    return ret

def fn_concat(cwd, item_list):
    item_list = [process_object(cwd, item) for item in item_list]
    return "".join(item_list)


func_map = {
    "TVLK::Fn::FromFile": fn_process_file,
    "TVLK::Fn::FromFolders": fn_from_folders,
    "TVLK::Fn::FileAsBase64": fn_file_as_base64,
    "TVLK::Fn::GetConfig": fn_get_config,
    "TVLK::Fn::Merge": fn_merge,
    "TVLK::Fn::Concat": fn_concat
}


if __name__ == '__main__':
    main(sys.argv)
