import os
import json

def _get_this_script_path():
    return os.path.split(os.path.realpath(__file__))[0]

def _get_infra_locals_path():
    return os.path.join(_get_this_script_path(), "infra_locals.json")

def get_repo_path():
    return json.load(open(_get_infra_locals_path()))["repo_path"]