load("@py_deps//:requirements.bzl", pip_req="requirement")

py_binary(
    name = "updater-script",
    srcs = ["updater-script.py"],
    deps = [
        pip_req("waymo-open-dataset-tf-2-6-0"),
        pip_req("tensorflow"),
        pip_req("matplotlib"),
        pip_req("imageio"),
        pip_req("google-cloud-storage"),
        pip_req("tqdm"),
        "//infra:infra_locals_lib",
    ],
)