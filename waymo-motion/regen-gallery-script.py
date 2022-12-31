import os
import glob
import itertools
import html
from infra.infra_locals import get_repo_path

def get_data_dirpath():
    return os.path.join(get_repo_path(), "waymo-motion/data")

def get_data_vid_dirpath():
    return os.path.join(get_data_dirpath(), "vid")

def get_data_thumb_dirpath():
    return os.path.join(get_data_dirpath(), "thumb")

def run_main():
    def make_page_name(i, gallery_groups):
        if i < 0 or i >= len(gallery_groups):
            return '#blank'
        return f'gal_{i}.md' if i > 0 else 'README.md'
    def make_thumb_code(filename):
        if filename:
            thumb_filename = '../thumb/' + html.escape(filename)
            vid_filename = '../vid/' + html.escape(filename)
            return f'[![]({thumb_filename})]({vid_filename})'
        return ''
    all_vid_files = []
    for filename in glob.iglob(get_data_vid_dirpath() + '/**/*', recursive=True):
        if filename.endswith('.gif'):
            all_vid_files.append(os.path.abspath(filename)[len(get_data_vid_dirpath())+1:])
    all_thumb_files = []
    for filename in glob.iglob(get_data_thumb_dirpath() + '/**/*', recursive=True):
        if filename.endswith('.gif'):
            all_thumb_files.append(os.path.abspath(filename)[len(get_data_thumb_dirpath())+1:])
    all_gallery_files = list(set(all_vid_files) & set(all_thumb_files))

    group_size = 4*4
    gallery_groups = list(itertools.zip_longest(*(iter(all_gallery_files),) * group_size))

    for i, group in enumerate(gallery_groups):
        md_code = f'''
[prev]({make_page_name(i-1, gallery_groups)}) - [next]({make_page_name(i+1, gallery_groups)})
| {make_thumb_code(group[0])}  | {make_thumb_code(group[1])}  | {make_thumb_code(group[2])}  | {make_thumb_code(group[3])}  |
|---|---|---|---|
| {make_thumb_code(group[4])}  | {make_thumb_code(group[5])}  | {make_thumb_code(group[6])}  | {make_thumb_code(group[7])}  |
| {make_thumb_code(group[8])}  | {make_thumb_code(group[9])}  | {make_thumb_code(group[10])}  | {make_thumb_code(group[11])}  |
| {make_thumb_code(group[12])}  | {make_thumb_code(group[13])}  | {make_thumb_code(group[14])}  | {make_thumb_code(group[15])}  |
'''
        print(md_code)

if __name__ == "__main__":
    run_main()