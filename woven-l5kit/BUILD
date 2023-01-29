load("@py_deps2//:requirements.bzl", pip_req="requirement")

py_binary(
    name = "sanity-check-api",
    srcs = ["sanity-check-api.py"],
    deps = [
        pip_req("l5kit"),
    ],
    env={"PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION": "python", 
         "L5KIT_DATA_FOLDER": "dummy"}
)