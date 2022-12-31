# simplified-datasets

## Waymo Motion Data

A single tensorflow protobuf record from the [Waymo Open Dataset](https://github.com/waymo-research/waymo-open-dataset) ([License](https://github.com/waymo-research/waymo-open-dataset#license)) for [Motion Data](https://waymo.com/open/data/motion/) is around 400 MB. 

For motion data analysis, we need a tiny fraction of that: map centerlines, borders, traffic light status, and track trajectories. That would amount to few kilobytes. In this repository, we extract this smaller data representation for ease of iteration. As we do that, we also provide visual animations from the dataset [here](./waymo-motion/data), they are around 10 MB per scenario. 
![](./media/Peek-2022-12-31-15-50.gif)

To contribute with more animations:
*  Run `bazel run waymo-motion:updater-script -- -r -p <project>` for a while (interrupt at will with ctrl-c), followed by a pull request.
* `<project>` must be a valid gcloud project under your gcloud username. It takes around a minute to download and process a record on a powerful machine with good internet connection. 
* To initialize the repo, you also need to run `python3 ./init_infra_locals.py` once.

