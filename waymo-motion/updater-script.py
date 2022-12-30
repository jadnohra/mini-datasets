import tensorflow.compat.v1 as tf
import matplotlib.pyplot as plt
from waymo_open_dataset.protos import scenario_pb2 
from waymo_open_dataset.protos import map_pb2

tf.enable_eager_execution()

if True:
    from google.cloud import storage
    from tqdm import tqdm

    client = storage.Client('Test1') # You need to have at least some google cloud project.
    print(len(list(client.list_blobs('waymo_open_dataset_motion_v_1_1_0', prefix='uncompressed/scenario/training'))))

if False:
    for blob in client.list_blobs('waymo_open_dataset_motion_v_1_1_0', prefix='uncompressed/scenario/training'):
        print(type(blob))
        print(str(blob))
        if not blob.name.endswith('/'):
            with open('/home/jad/Downloads/' + blob.name.replace('/', '_'), 'wb') as f:
                with tqdm.wrapattr(f, "write", total=blob.size) as file_obj:
                    blob.download_to_file(file_obj)
            break


FILENAME = '/home/jad/LargeData/uncompressed_scenario_training_training.tfrecord-00000-of-01000'
dataset = tf.data.TFRecordDataset(FILENAME)
scenario_data = []
for data in dataset:
    proto_string = data.numpy()
    proto = scenario_pb2.Scenario()
    proto.ParseFromString(proto_string)
    scenario_data.append(proto)