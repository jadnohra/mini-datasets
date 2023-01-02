from pathlib import Path


def get_repo_path():
    return Path(__file__).resolve().parent.parent