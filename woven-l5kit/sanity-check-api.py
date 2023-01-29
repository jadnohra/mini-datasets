import numpy as np
from l5kit.data import ChunkedDataset, LocalDataManager
from l5kit.data.map_api import MapAPI


dm = LocalDataManager()
zarr_dataset = ChunkedDataset("/home/jad/Downloads/prediction-sample/sample.zarr")
zarr_dataset.open()
print(zarr_dataset)

world_to_ecef = np.array([
  [0.846617444,0.323463078,-0.422623402,-2698767.44],
  [-0.532201938,0.514559352,-0.672301845,-4293151.58],
  [-3.05311332e-16,0.794103464,0.6077826,3855164.76],
  [0.0,0.0,0.0,1.0]], 
  dtype=np.float64)
mapAPI = MapAPI("/home/jad/Downloads/prediction-semantic_map/semantic_map.pb", world_to_ecef)
print(mapAPI)
