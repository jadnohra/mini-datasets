load("@rules_python//python:pip.bzl", "compile_pip_requirements")

compile_pip_requirements(
    name = "compile_pip_requirements",
    requirements_in = "//infra/python:requirements.txt",
    requirements_txt = "//infra/python:requirements_lock.txt",
)