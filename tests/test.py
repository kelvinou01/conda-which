import os
from os.path import abspath, dirname

import pytest

import conda_which
from conda_which import (
    CondaMetaParseError,
    build_parser,
    find_owner_packages,
    is_conda_metadata,
    match_longest_prefix,
    read_conda_meta,
    strip_prefix,
    strip_suffix,
    which,
)


@pytest.fixture
def conda_metas():
    parent_dir = dirname(abspath(__file__))
    results = [
        os.path.join(
            parent_dir, "data", "conda-meta", "decodable-1.0.0-pyhd8ed1ab_0.json"
        ),
        os.path.join(
            parent_dir, "data", "conda-meta", "notdecodable-1.0.0-pyhd9ed1ab.json"
        ),
    ]
    yield results


@pytest.fixture
def temp_set_conda_envs_list():
    original_value = conda_which.CONDA_ENVS

    parent_dir = dirname(abspath(__file__))
    envs = [
        os.path.join(parent_dir, "data", "environments", "normal"),
        os.path.join(parent_dir, "data", "environments", "clobbered"),
    ]
    conda_which.CONDA_ENVS = envs
    yield envs

    conda_which.CONDA_ENVS = original_value


def test_match_longest_prefix():
    conda_envs = {"/envs", "/envs/conda"}
    assert match_longest_prefix("/envs/conda/file.txt", conda_envs) == "/envs/conda"
    assert match_longest_prefix("/envs/file.txt", conda_envs) == "/envs"
    assert match_longest_prefix("/other/path/file.txt", conda_envs) is None


def test_is_conda_metadata():
    assert is_conda_metadata("/path/to/conda-meta/something.json")
    assert is_conda_metadata("/path/to/conda-meta/history")
    assert not is_conda_metadata("/path/to/conda-meta/something.txt")
    assert not is_conda_metadata("/path/to/bin/something.json")


def test_strip_prefix():
    assert strip_prefix("/path/to/file", "/path/to") == "file"
    assert strip_prefix("/path/to/file", "/other/path") == "/path/to/file"
    assert strip_prefix("/path/to/path/to/file", "/path/to") == "path/to/file"


def test_strip_suffix():
    assert strip_suffix("/path/to/file", ".json") == "/path/to/file"
    assert strip_suffix("/path/to/file.json", ".json") == "/path/to/file"
    assert strip_suffix("/path/to/file.json.json", ".json") == "/path/to/file.json"


def test_read_conda_meta(conda_metas):
    decodable, not_decodable = conda_metas
    assert read_conda_meta(decodable)

    # Assert correct exception is thrown, and error message contains file path for easy troubleshooting
    with pytest.raises(CondaMetaParseError, match=not_decodable):
        read_conda_meta(not_decodable)


def test_find_owner_packages(temp_set_conda_envs_list):
    _, clobbered_prefix = temp_set_conda_envs_list
    normal_path = os.path.join("bin", "flask")
    clobbered_path = os.path.join("lib", "clobbered")

    assert find_owner_packages(normal_path, clobbered_prefix) == [
        "flask-1.0.0-pyhd8ed1ab_0"
    ]
    assert sorted(find_owner_packages(clobbered_path, clobbered_prefix)) == sorted(
        [
            "flask-1.0.0-pyhd8ed1ab_0",
            "numpy-1.0.0-pyhd2dzjjafs",
        ]
    )


def test_which_for_normal_environment(temp_set_conda_envs_list):
    normal, _ = temp_set_conda_envs_list

    flask_file_path = os.path.join(normal, "bin", "flask")
    fullpath, prefix, packages = which(flask_file_path)
    assert fullpath == flask_file_path
    assert prefix == normal
    assert packages == ["flask-1.0.0-pyhd8ed1ab_0"]

    user_added_path = os.path.join(normal, "user-added.txt")
    fullpath, prefix, packages = which(user_added_path)
    assert fullpath == user_added_path
    assert prefix == normal
    assert packages == []

    nonexistent_path = os.path.join(normal, "nonexistent-file")
    fullpath, prefix, packages = which(nonexistent_path)
    assert fullpath == None
    assert prefix == None
    assert packages == []


def test_which_for_clobbered_environment(temp_set_conda_envs_list):
    _, clobbered = temp_set_conda_envs_list

    clobbered_path = os.path.join(clobbered, "lib", "clobbered")
    fullpath, prefix, packages = which(clobbered_path)
    assert fullpath == clobbered_path
    assert prefix == clobbered
    assert sorted(packages) == sorted(
        ["flask-1.0.0-pyhd8ed1ab_0", "numpy-1.0.0-pyhd2dzjjafs"]
    )

    user_added_path = os.path.join(clobbered, "bin", "flask")
    fullpath, prefix, packages = which(user_added_path)
    assert fullpath == user_added_path
    assert prefix == clobbered
    assert packages == ["flask-1.0.0-pyhd8ed1ab_0"]


def test_build_parser():
    parser = build_parser()
    args = parser.parse_args(["--unix", "/path/to/file.txt"])
    assert args.unix
    assert args.file == ["/path/to/file.txt"]

def test_symlink(temp_set_conda_envs_list):
    normal, _ = temp_set_conda_envs_list
    symlink_path = os.path.join(normal, "lib", "python3.12", "site-packages", "flask-1.0.0-pyhd8ed1ab_0", "symlink-to-abc")
    fullpath, prefix, packages = which(symlink_path)

    assert fullpath == symlink_path
    assert prefix == normal
    assert packages == ["flask-1.0.0-pyhd8ed1ab_0"]
