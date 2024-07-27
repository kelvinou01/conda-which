import argparse
import json
import os

import conda.plugins
from conda import CondaError
from conda.core.envs_manager import list_all_known_prefixes

PLUGIN_DESCRIPTION = "Which package does this file belong to?"
CONDA_ENVS = set(list_all_known_prefixes())


class NotACondaFile(CondaError):
    def __init__(self, path, conda_envs, **kwargs):
        message = (
            "The file does not belong to any Conda environment: %(path)s\n"
            "Available Conda environments are: %(conda_envs)s"
        )
        super().__init__(message, path=path, conda_envs=conda_envs, **kwargs)


class FileNotFound(CondaError):
    def __init__(self, path, **kwargs):
        message = "The file does not exist: %(path)s"
        super().__init__(message, path=path, **kwargs)


def match_longest_prefix(path, conda_envs):
    while path != "/":
        if path in conda_envs:
            return path
        path = os.path.dirname(path)

    return None


# Don't use str.removeprefix, for python3.8 support
def strip_prefix(path, prefix):
    if path.startswith(prefix):
        return path[len(prefix) :].lstrip("/")
    else:
        return ValueError("")


def find_owner_package(relpath, prefix):
    conda_meta = os.path.join(prefix, "conda-meta")
    metadata_files = [path for path in os.listdir(conda_meta) if path.endswith(".json")]

    for filename in metadata_files:
        json_path = os.path.join(conda_meta, filename)
        with open(json_path, "r") as f:
            data = json.load(f)
            files = data.get("files", [])
            if relpath in files:
                return filename.strip(".json")

    return None


def command(argv: list[str]):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        path = os.path.realpath(args.file[0], strict=True)
    except OSError as e:
        raise FileNotFound(path, cause=e)

    prefix = match_longest_prefix(path, CONDA_ENVS)
    if prefix is None:
        raise NotACondaFile(path, CONDA_ENVS)

    relpath = strip_prefix(path, prefix)
    package = find_owner_package(relpath, prefix)
    package_display = package if package else "No package (user added file)"
    print(f"File '{path}' belongs to")
    print(f"  Package: {package_display}")
    print(f"  Environment: {prefix}")


def build_parser():
    parser = argparse.ArgumentParser(description=PLUGIN_DESCRIPTION)
    parser.add_argument("file", type=str, nargs="+", help="The files to query for")
    return parser


@conda.plugins.hookimpl
def conda_subcommands():
    yield conda.plugins.CondaSubcommand(
        name="which",
        action=command,
        summary=PLUGIN_DESCRIPTION,
    )
