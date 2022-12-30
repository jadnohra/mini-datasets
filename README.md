# simplified-datasets

## Waymo Motion Data

A single tensorflow protobuf record from the [Waymo Open Dataset](https://github.com/waymo-research/waymo-open-dataset) for [Motion Data](https://waymo.com/open/data/motion/) is around 400 MB. For motion data analysis, really just a need a tiny fraction of that: Map centerlines, borders, traffic light status, and track trajectories, that would amount to few kilobytes. In this repository, we extract this much smaller data representation for ease of iteration. 

As we do that, we also provide visual animations from the dataset [here](./waymo-motion/data), they are around 10 MB per scenario. 
![](./waymo-motion/data/uncompressed_scenario_training_20s_training_20s.tfrecord-00975-of-01000.gif)

To add some more, run `bazel run waymo-motion:updater-script -- -r -p <project>` for a while and do a pull request.
`<project>` must be a valid gcloud project under your gcloud username. It takes around a minute to download and process a record.
