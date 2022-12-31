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
import tensorflow.compat.v1 as tf
import matplotlib.pyplot as plt
from waymo_open_dataset.protos import scenario_pb2 
from waymo_open_dataset.protos import map_pb2
from infra.infra_locals import get_repo_path
from google.cloud import storage

tf.enable_eager_execution()

def get_data_dirpath():
    return os.path.join(get_repo_path(), "waymo-motion/data")

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

def read_status_dict():
    status_filepath = get_status_filepath()
    if os.path.exists(status_filepath):
        with open(status_filepath) as infile:
            return json.load(infile)
    else:
        return {}

def write_status_dict(status_dict):
    with open(get_status_filepath(), 'w') as outfile:
        outfile.write(json.dumps(status_dict, indent=4))

def get_relevant_gcloud_blobs(gcloud_proj_name='Test1'):
    logging.info(">> Reading gcloud blobs")
    client = storage.Client('Test1') # You need to have at least some google cloud project, related to your signed-in gcloud user
    file_blobs = []
    for blob in client.list_blobs('waymo_open_dataset_motion_v_1_1_0', prefix='uncompressed/scenario/training'):
        if not blob.name.endswith('/'):
            file_blobs.append(blob)
    return file_blobs

def process_blob(blob, status_dict):
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
        map_centerlines, static_tracks, track_trajectories = simple_scenario_data
        traj_len = len(track_trajectories[0])

        fig_square_size = None
        xlim_center = None
        ylim_center = None
        fig_filenames = []

        idle_states = []
        for track_trajectory in static_tracks:
            idle_states.append(track_trajectory[0])

        for frame_index in range(traj_len):
            progress = int(100 * frame_index / traj_len)
            print('\rGenerating frames: [{0}] {1}%'.format('#'*int(progress/10), progress), end='', flush=True)

            for centerline in map_centerlines:
                plt.plot(*list(zip(*centerline)), '--', color='lightgray', zorder=0)
            
            if len(idle_states) > 0:
                plt.scatter(*list(zip(*idle_states)), facecolors='none', edgecolors='lightgray', zorder=1)

            curr_states = []
            for track_trajectory in track_trajectories:
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
    
        out_vid_fpath = os.path.join(os.path.join(tmp_dirpath, 'vid'), 'fig-anim.gif')
        images = []
        for filename in fig_filenames:
            progress = int(100 * frame_index / traj_len)
            print('\rGenerating animation: [{0}] {1}%'.format('#'*int(progress/10), progress), end='', flush=True)
            images.append(imageio.imread(filename))
        imageio.mimsave(out_vid_fpath, images)
        return out_vid_fpath

    def finalize_blob(status_dict, blob, blob_local_name, vid_fpath):
        vid_final_fname = blob_local_name + '.gif'
        result_fpath = os.path.join(get_data_dirpath(), vid_final_fname)
        shutil.move(vid_fpath, result_fpath)
        status_dict[blob.name] = vid_final_fname

    blob_local_name = blob.name.replace('/', '_')
    tmp_dirpath = get_clean_tmp_dirpath()
    blob_local_fpath = os.path.join(tmp_dirpath, blob_local_name)
    download_blob(blob, blob_local_fpath)
    scenario_data = read_blob_scenario_data(blob_local_fpath)
    
    simple_scenario_data = extract_simple_scenario_data(scenario_data)
    vid_fpath = render_scenario_vid(simple_scenario_data, tmp_dirpath)
    finalize_blob(status_dict, blob, blob_local_name, vid_fpath)

def run_main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--random', action='store_true', help="Randomly select new scenarios to process (as opposed to sequentially)")
    parser.add_argument('-p', '--project', help="A valid gcloud project name associated with the gcloud-cli default user", default='Test1')

    args = parser.parse_args()

    status_dict = read_status_dict()
    relevant_blobs = get_relevant_gcloud_blobs(gcloud_proj_name=args.project)
    blobs_to_process = []
    for blob in relevant_blobs:
        if blob.name not in status_dict:
            blobs_to_process.append(blob)
    
    if args.random:
        random.seed(time.time())
        random.shuffle(blobs_to_process)

    for blob in blobs_to_process:
        process_blob(blob, status_dict)
        write_status_dict(status_dict)

if __name__ == "__main__":
    run_main()