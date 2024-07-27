import argparse
import json
import os

import conda.plugins
from conda.core.envs_manager import list_all_known_prefixes
from termcolor import colored

PLUGIN_DESCRIPTION = "Which package does this file belong to?"
CONDA_ENVS = set(list_all_known_prefixes())


def match_longest_prefix(path, conda_envs):
    while path != "/":
        if path in conda_envs:
            return path
        path = os.path.dirname(path)

    return None


def is_conda_metadata(fullpath):
    if os.path.basename(os.path.dirname(fullpath)) == "conda-meta":
        filename = os.path.basename(fullpath)
        if filename.endswith(".json") or filename == "history":
            return True
    return False


# Don't use str.removeprefix, for python3.8 support
def strip_prefix(path, prefix):
    if path.startswith(prefix):
        return path[len(prefix) :].lstrip("/")
    else:
        return ValueError("Path does not start with prefix")


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


def which(path):
    try:
        fullpath = os.path.realpath(path, strict=True)
    except OSError:
        return None, None, None

    prefix = match_longest_prefix(fullpath, CONDA_ENVS)
    if prefix is None:
        return fullpath, None, None

    relpath = strip_prefix(fullpath, prefix)
    package = find_owner_package(relpath, prefix)
    if package is None:
        if is_conda_metadata(fullpath):
            return fullpath, prefix, "Conda metadata file"
        else:
            return fullpath, prefix, None

    return fullpath, prefix, package


def print_for_human(arg, fullpath, prefix, package):
    if not fullpath:
        print(colored(f"File '{arg}' does not exist", "red"))
        return

    if package:
        package_display = colored(package, "green")
    else:
        package_display = colored("Does not belong to a conda package", "yellow")

    if prefix:
        prefix_display = colored(prefix, "green")
    else:
        prefix_display = colored("Does not belong to a conda environment", "yellow")

    print(f"File '{fullpath}' belongs to")
    print(f"  📦 Package: {package_display}")
    print(f"  🌏 Environment: {prefix_display}")
    print("")


def print_for_machine(fullpath, prefix, package):
    if not fullpath:
        print("Path not found")
    elif not prefix:
        print(f"'{fullpath}' does not belong to any conda environment")
    elif not package:
        print(
            f"'{fullpath}' belongs to a conda environment, but not to any conda package"
        )
    else:
        print(f"'{fullpath}' belongs to {package}")


def command(argv: list[str]):
    parser = build_parser()
    args = parser.parse_args(argv)
    adhere_to_unix_philosophy = args.unix
    for path in args.file:
        fullpath, prefix, package = which(path)
        if adhere_to_unix_philosophy:
            print_for_machine(fullpath, prefix, package)
        else:
            print_for_human(path, fullpath, prefix, package)


def build_parser():
    parser = argparse.ArgumentParser(description=PLUGIN_DESCRIPTION)
    parser.add_argument("file", type=str, nargs="+", help="The files to query for")
    parser.add_argument(
        "--unix",
        "-u",
        action="store_true",
        help="Should we adhere to the unix philosophy?",
    )
    return parser


@conda.plugins.hookimpl
def conda_subcommands():
    yield conda.plugins.CondaSubcommand(
        name="which",
        action=command,
        summary=PLUGIN_DESCRIPTION,
    )
