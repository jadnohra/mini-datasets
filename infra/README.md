# Deterministic Build

Only a few manual steps are needed. The rest is handled through bazel and other infrastructure tools.

1. Install bazel. To install bazel on linux, see instructions. below
2. Add any python pip requirements into infra/python/requirements.txt. Do a python requirements update, see insturctions below. Rerun this step whenver the requirements change.
3. Run `python ./init_infra_locals.py` once, and rerun everytime the root of this repo changes.
  - This allows correctly accessing data files in this repo when running code under bazel. Use `from bazel.infra_locals import get_repo_path` to import `get_repo_path`, and then call that function to obtain an absolute path to the repo's directory (outside of the bazel sandbox). Include `//infra:infra_locals_lib` as a dependency in your BUILD file.

## Install bazel on Linux

> wget https://github.com/bazelbuild/bazelisk/releases/download/v1.14.0/bazelisk-linux-amd64
> chmod +x bazelisk-linux-amd64
> sudo mv bazelisk-linux-amd64 /usr/local/bin/bazel
> which bazel

## Update python requirements
Add the requirement to requirements.txt and run `bazel run //infra/python:compile_pip_requirements.update` 

