# Deterministic Build

Only a few manual steps are needed. The rest is handled through bazel and other infrastructure tools.

1. Install bazel. To install bazel on linux, see instructions below.
2. Add any Python pip requirements into infra/python/requirements.txt. Do a Python requirements update, see instructions below. Rerun this step whenver the requirements change.

## Install bazel on Linux

```
> wget https://github.com/bazelbuild/bazelisk/releases/download/v1.14.0/bazelisk-linux-amd64
> chmod +x bazelisk-linux-amd64
> sudo mv bazelisk-linux-amd64 /usr/local/bin/bazel
> which bazel
```

## Update python requirements
Add the requirement to requirements.txt and run `bazel run //infra/python:compile_pip_requirements.update` 

