import os
import glob
from infra.infra_locals import get_repo_path

def get_data_dirpath():
    return os.path.join(get_repo_path(), "waymo-motion/data")

def get_data_vid_dirpath():
    return os.path.join(get_data_dirpath(), "vid")

def get_data_thumb_dirpath():
    return os.path.join(get_data_dirpath(), "thumb")

def run_main():
    all_vid_files = []
    for filename in glob.iglob(get_data_vid_dirpath() + '/**/*', recursive=True):
        if filename.endswith('.gif'):
            all_vid_files.append(os.path.abspath(filename)[len(get_data_vid_dirpath())+1:])
    all_thumb_files = []
    for filename in glob.iglob(get_data_thumb_dirpath() + '/**/*', recursive=True):
        if filename.endswith('.gif'):
            all_thumb_files.append(os.path.abspath(filename)[len(get_data_thumb_dirpath())+1:])
    all_gallery_files = list(set(all_vid_files) & set(all_thumb_files))

    print(all_gallery_files)

if __name__ == "__main__":
    run_main()