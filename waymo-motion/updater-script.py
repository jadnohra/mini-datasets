import os
import json
import logging
import argparse
import random
import time
from pathlib import Path
import shutil
from tqdm import tqdm
import imageio
from PIL import Image
import tensorflow.compat.v1 as tf
import matplotlib.pyplot as plt
from waymo_open_dataset.protos import scenario_pb2 
from waymo_open_dataset.protos import map_pb2
from infra.infra_locals import get_repo_path
from google.cloud import storage

tf.enable_eager_execution()

def get_data_dirpath():
    return os.path.join(get_repo_path(), "waymo-motion/data")

def get_data_vid_dirpath():
    return os.path.join(get_data_dirpath(), "vid")

def get_data_thumb_dirpath():
    return os.path.join(get_data_dirpath(), "thumb")

def get_status_filename():
    return 'status.json'

def get_status_filepath():
    return os.path.join(get_repo_path(), "waymo-motion/status.json")

def get_tmp_dirpath():
    return os.path.join(get_repo_path(), "waymo-motion/tmp/")

def clear_tmp_dir():
    for path in Path(get_tmp_dirpath()).glob("**/*"):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)

def get_clean_tmp_dirpath():
    clear_tmp_dir()
    return get_tmp_dirpath()

def read_status_file(status_filepath, dflt):
    if os.path.exists(status_filepath):
        with open(status_filepath) as infile:
            return json.load(infile)
    else:
        return dflt

def write_status_file(status_obj, status_filepath):
    with open(status_filepath, 'w') as outfile:
        outfile.write(json.dumps(status_obj, indent=4))

def get_relevant_gcloud_blobs(gcloud_proj_name='Test1'):
    logging.info(">> Reading gcloud blobs")
    client = storage.Client(gcloud_proj_name) # You need to have at least some google cloud project, related to your signed-in gcloud user
    file_blobs = []
    for blob in client.list_blobs('waymo_open_dataset_motion_v_1_1_0', prefix='uncompressed/scenario/training'):
        if not blob.name.endswith('/'):
            file_blobs.append(blob)
    return file_blobs

def download_blob(blob, blob_local_fpath):
    logging.info(f">> Downloading blob: {blob.name}")
    with open(blob_local_fpath, 'wb') as f:
        with tqdm.wrapattr(f, "write", total=blob.size) as file_obj:
            blob.download_to_file(file_obj)

def read_blob_scenario_data(blob_fpath):
    logging.info(f">> Reading scenario from blob")
    dataset = tf.data.TFRecordDataset(blob_fpath)
    scenario_data = []
    for data in dataset:
        proto_string = data.numpy()
        proto = scenario_pb2.Scenario()
        proto.ParseFromString(proto_string)
        scenario_data.append(proto)
    return scenario_data

def extract_simple_scenario_data(scenario_data):
    logging.info(f">> Extracting relevant data")
    map_centerlines = []
    for map_feature in scenario_data[0].map_features:
        data = getattr(map_feature, map_feature.WhichOneof('feature_data'))
        centerline = []
        if isinstance(data, map_pb2.LaneCenter):
            lane_center = data
            for polyline_pt in lane_center.polyline:
                centerline.append([polyline_pt.x, polyline_pt.y])
            map_centerlines.append(centerline)
    
    all_trajectories = []
    for track in scenario_data[0].tracks:
        track_trajectory = []
        last_valid_state = None
        if track.object_type == scenario_pb2.Track.TYPE_VEHICLE or True:
            for state in track.states:
                if state.valid:
                    if last_valid_state is None:
                        track_trajectory = [(val if val else [state.center_x, state.center_y]) for val in track_trajectory]
                    last_valid_state = [state.center_x, state.center_y]
                    track_trajectory.append(last_valid_state)
                else:
                    track_trajectory.append(last_valid_state)
        if len(track_trajectory):
            all_trajectories.append(track_trajectory)

    static_tracks = []
    track_trajectories = []
    for track_trajectory in all_trajectories:
        first_pos = track_trajectory[0]
        is_static = all([xy == first_pos for xy in track_trajectory])
        if is_static:
            static_tracks.append([first_pos]) 
        else:
            track_trajectories.append(track_trajectory)

    return (map_centerlines, static_tracks, track_trajectories)

def render_scenario_vid(simple_scenario_data, tmp_dirpath):
    traj_len = len(simple_scenario_data['dynamic_tracks'][0])

    fig_square_size = None
    xlim_center = None
    ylim_center = None
    fig_filenames = []

    idle_states = []
    for track_trajectory in simple_scenario_data['static_tracks']:
        idle_states.append(track_trajectory[0])

    for frame_index in range(traj_len):
        progress = int(100 * frame_index / traj_len)
        print('\rGenerating frames: [{0}] {1}%'.format('#'*int(progress/10), progress), end='', flush=True)

        for centerline in simple_scenario_data['centerlines']:
            plt.plot(*list(zip(*centerline)), '--', color='lightgray', zorder=0)
        
        if len(idle_states) > 0:
            plt.scatter(*list(zip(*idle_states)), facecolors='none', edgecolors='lightgray', zorder=1)

        curr_states = []
        for track_trajectory in simple_scenario_data['dynamic_tracks']:
            plt.plot(*list(zip(*track_trajectory[:frame_index])), zorder=2)
            curr_states.append(track_trajectory[frame_index])
            
        plt.scatter(*list(zip(*curr_states)), facecolors='none', edgecolors='r', zorder=3)
        
        if fig_square_size is None:
            xlim = plt.gca().get_xlim() 
            ylim = plt.gca().get_ylim() 
            xlim_center = (xlim[1] + xlim[0]) / 2
            ylim_center = (ylim[1] + ylim[0]) / 2
            xlim_size = xlim[1] - xlim[0]
            ylim_size = ylim[1] - ylim[0]
            fig_square_size = max(xlim_size, ylim_size)

        plt.gca().set_aspect(1, adjustable='box')
        plt.axis('off')
        plt.gca().set_xlim(xlim_center - fig_square_size/2, xlim_center + fig_square_size / 2)
        plt.gca().set_ylim(ylim_center - fig_square_size/2, ylim_center + fig_square_size / 2)

        fig_filename = os.path.join(tmp_dirpath, 'frame-' + f"{frame_index:05}" + '.jpg')
        fig_filenames.append(fig_filename)
        plt.savefig(fig_filename, bbox_inches='tight', dpi=180)
        plt.close()

    out_vid_fpath = os.path.join(tmp_dirpath, 'fig-anim.gif')
    out_thumb_fpath = os.path.join(tmp_dirpath, 'fig-anim-thumb.gif')
    images = []
    thumb_images = []
    for filename in fig_filenames:
        progress = int(100 * frame_index / traj_len)
        print('\rGenerating animation: [{0}] {1}%'.format('#'*int(progress/10), progress), end='', flush=True)
        images.append(imageio.imread(filename))
        thumb_images.append(Image.fromarray(images[-1]).resize((256, 256),  Image.ANTIALIAS))
    imageio.mimsave(out_vid_fpath, images)
    imageio.mimsave(out_thumb_fpath, thumb_images)
    return out_vid_fpath, out_thumb_fpath


class BlobCache:
    def __init__(self, blob, blob_local_fpath, blob_local_name):
        self._blob = blob
        self._blob_local_fpath = blob_local_fpath
        self._blob_local_name = blob_local_name
        self._cache_dict = {}

    def get_blob(self):
        return self._blob

    def get_blob_local_name(self):
        return self._blob_local_name

    def download(self):
        if 'download' in self._cache_dict:
            return self._cache_dict['download']
        download_blob(self._blob, self._blob_local_fpath)
        self._cache_dict['download'] = self._blob_local_fpath
        return self.download()

    def get_scenario_data(self):
        if 'scenario_data' in self._cache_dict:
            return self._cache_dict['scenario_data']
        blob_fpath = self.download()
        scenario_data = read_blob_scenario_data(blob_fpath)
        self._cache_dict['scenario_data'] = scenario_data
        return self.get_scenario_data()

    def get_simple_scenario_data(self):
        if 'simple_scenario_data' in self._cache_dict:
            return self._cache_dict['simple_scenario_data']
        scenario_data = self.get_scenario_data()
        map_centerlines, static_tracks, track_trajectories = extract_simple_scenario_data(scenario_data)
        simple_scenario_data = {'centerlines': map_centerlines, 'static_tracks': static_tracks, 'dynamic_tracks': track_trajectories}
        self._cache_dict['simple_scenario_data'] = simple_scenario_data
        return self.get_simple_scenario_data()
        
class BlobProcessor:
    def needs_processing(self, blob):
        return False
    def process(self, blob_cache):
        return False

class BlobProcessorVid:
    def __init__(self, tmp_dirpath):
        self._tmp_dirpath = tmp_dirpath
        self._status = read_status_file(os.path.join(get_data_vid_dirpath(), get_status_filename()), [])

    def needs_processing(self, blob):
        return blob.name not in self._status

    def process(self, blob_cache):
        vid_fpath, thumb_fpath = render_scenario_vid(blob_cache.get_simple_scenario_data(), self._tmp_dirpath)
        
        vid_final_fname = blob_cache.get_blob_local_name() + '.gif'
        vid_result_fpath = os.path.join(get_data_vid_dirpath(), vid_final_fname)
        shutil.move(vid_fpath, vid_result_fpath)
        thumb_result_fpath = os.path.join(get_data_thumb_dirpath(), vid_final_fname)
        shutil.move(thumb_fpath, thumb_result_fpath)
        
        self._status.append(blob_cache.get_blob().name)
        write_status_file(self._status, os.path.join(get_data_vid_dirpath(), get_status_filename()))
        write_status_file(self._status, os.path.join(get_data_thumb_dirpath(), get_status_filename()))

def process_blob(blob, processors):
    blob_local_name = blob.name.replace('/', '_')
    tmp_dirpath = get_clean_tmp_dirpath()
    blob_local_fpath = os.path.join(tmp_dirpath, blob_local_name)
    blob_cache = BlobCache(blob, blob_local_fpath, blob_local_name)

    for processor in processors:
        if processor.needs_processing(blob_cache.get_blob()):
            processor.process(blob_cache)

def run_main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--random', action='store_true', help="Randomly select new scenarios to process (as opposed to sequentially)")
    parser.add_argument('-p', '--project', help="A valid gcloud project name associated with the gcloud-cli default user", default='Test1')

    args = parser.parse_args()

    relevant_blobs = get_relevant_gcloud_blobs(gcloud_proj_name=args.project)
    processors = [BlobProcessorVid(get_tmp_dirpath())]

    blobs_to_process = []
    for blob in relevant_blobs:
        needs_processing = any([processor.needs_processing(blob) for processor in processors])
        if needs_processing:
            blobs_to_process.append(blob)
    
    if args.random:
        random.seed(time.time())
        random.shuffle(blobs_to_process)

    for blob in blobs_to_process:
        process_blob(blob, processors)

if __name__ == "__main__":
    run_main()