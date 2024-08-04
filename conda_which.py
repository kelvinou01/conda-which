import argparse
import json
import logging
import os
import sys
from json.decoder import JSONDecodeError

import conda.plugins
from conda import CondaError
from conda.core.envs_manager import list_all_known_prefixes
from termcolor import colored

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stdout_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stdout_handler)


PLUGIN_DESCRIPTION = "Which package does this file belong to?"
CONDA_ENVS = set(list_all_known_prefixes())


class CondaMetaParseError(CondaError):

    def __init__(self, message, file_name, caused_by=None, **kwargs):
        kwargs["file_name"] = file_name
        super().__init__(message, caused_by=caused_by, **kwargs)


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


# Don't use str.removeprefix, for python <=3.8 support
def strip_prefix(path, prefix):
    if path.startswith(prefix):
        return path[len(prefix) :].lstrip("/")
    else:
        raise ValueError("Path does not start with prefix")


def read_conda_meta(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except JSONDecodeError as e:
        raise CondaMetaParseError(
            "Couldn't parse conda metadata file: %(file_name)s", path, caused_by=e
        )


# Find all packages whose conda-meta contains this relpath
def find_owner_packages(relpath, prefix):
    conda_meta = os.path.join(prefix, "conda-meta")
    metadata_files = [path for path in os.listdir(conda_meta) if path.endswith(".json")]
    results = []

    for filename in metadata_files:
        path_to_json = os.path.join(conda_meta, filename)
        metadata = read_conda_meta(path_to_json)
        files = metadata.get("files", [])
        if relpath in files:
            package = filename.removesuffix(".json")
            results.append(package)

    return results


def which(path):
    try:
        fullpath = os.path.realpath(path, strict=True)
    except OSError:
        return None, None, []

    prefix = match_longest_prefix(fullpath, CONDA_ENVS)
    if prefix is None:
        return fullpath, None, []

    relpath = strip_prefix(fullpath, prefix)
    packages = find_owner_packages(relpath, prefix)

    if len(packages) == 0:
        if is_conda_metadata(fullpath):
            return fullpath, prefix, ["Conda metadata file"]
        else:
            return fullpath, prefix, []

    return fullpath, prefix, packages


def print_for_human(arg, fullpath, prefix, packages):
    if not fullpath:
        print(colored(f"File '{arg}' does not exist", "red"))
        return

    if len(packages) == 0:
        package_display = colored("Does not belong to a conda package", "yellow")
    elif len(packages) > 1:
        pretty_package_list = ", ".join(packages)
        package_display = colored(
            f"One of: {pretty_package_list} (file was clobbered)", "yellow"
        )
    else:
        package_display = colored(packages[0], "green")

    if prefix:
        prefix_display = colored(prefix, "green")
    else:
        prefix_display = colored("Does not belong to a conda environment", "yellow")

    print(f"File '{fullpath}' belongs to")
    print(f"  📦 Package: {package_display}")
    print(f"  🌏 Environment: {prefix_display}")
    print("")


def print_for_machine(fullpath, prefix, packages):
    if not fullpath:
        print("Path not found")
    elif not prefix:
        print(f"'{fullpath}' does not belong to any conda environment")
    elif len(packages) == 0:
        print(
            f"'{fullpath}' belongs to a conda environment, but not to any conda package"
        )
    elif len(packages) > 1:
        print(f"'{fullpath}' belongs to {packages} (file was clobbered)")
    else:
        print(f"'{fullpath}' belongs to {packages[0]}")


def command(argv: list[str]):
    parser = build_parser()
    args = parser.parse_args(argv)
    adhere_to_unix_philosophy = args.unix

    if args.verbose:
        logger.setLevel(logging.INFO)

    logger.info("Environments from ~/.condarc/environments.txt: %s", CONDA_ENVS)

    for path in args.file:
        fullpath, prefix, package = which(path)
        if adhere_to_unix_philosophy:
            print_for_machine(fullpath, prefix, package)
        else:
            print_for_human(path, fullpath, prefix, package)


def build_parser():
    parser = argparse.ArgumentParser(description=PLUGIN_DESCRIPTION)
    parser.add_argument("file", type=str, nargs="+", help="The files to query for.")
    parser.add_argument(
        "--unix",
        "-u",
        action="store_true",
        help="Should we adhere to the unix philosophy?",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        default=False,
        action="store_true",
        help="Print verbose output.",
    )
    return parser


@conda.plugins.hookimpl
def conda_subcommands():
    yield conda.plugins.CondaSubcommand(
        name="which",
        action=command,
        summary=PLUGIN_DESCRIPTION,
    )
