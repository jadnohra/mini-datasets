import os
import json

def _get_this_script_path():
    return os.path.split(os.path.realpath(__file__))[0]

infra_locals_dict = {
    "repo_path": _get_this_script_path()
}

json.dump(infra_locals_dict, open("infra/infra_locals.json", "w"), indent=4)