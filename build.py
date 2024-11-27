#!/user/bin/env python3
import logging
import lzma
import os
from pathlib import Path
import shutil
import threading
import zipfile
import concurrent.futures
import json
import zipfile
import requests

PATH_BASE = Path(__file__).parent.resolve()
PATH_BASE_MODULE: Path = PATH_BASE.joinpath("base")
PATH_BUILD: Path = PATH_BASE.joinpath("build")
PATH_BUILD_TMP: Path = PATH_BUILD.joinpath("tmp")
PATH_DOWNLOADS: Path = PATH_BASE.joinpath("downloads")

logger = logging.getLogger()
syslog = logging.StreamHandler()
formatter = logging.Formatter("%(threadName)s : %(message)s")
syslog.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(syslog)


def download_file(url: str, path: Path):
    file_name = url[url.rfind("/") + 1 :]
    logger.info(f"Downloading '{file_name}' to '{path}'")

    if path.exists():
        return

    r = requests.get(url, allow_redirects=True)
    with open(path, "wb") as f:
        f.write(r.content)

    logger.info("Done")


def extract_file(archive_path: Path, dest_path: Path):
    logger.info(f"Extracting '{archive_path.name}' to '{dest_path.name}'")
    print(archive_path)
    with zipfile.ZipFile(archive_path, "r") as zip_ref:
        zip_ref.extractall(dest_path)
        # # file_content = f.read()
        # path = dest_path.parent

        # path.mkdir(parents=True, exist_ok=True)

        # with open(dest_path, "wb") as out:
        #     out.write(zip_ref)


def create_module_prop(path: Path, version: str):
    module_prop = f"""id=magisk-FGGB
name=MagiskFridaGGBridge
version={version}
versionCode={version.replace(".", "").replace("-", "")}
author=XEKEX
description=Run FGGB on boot
updateJson=https://github.com/chihaamin/FGGB-Magisk/releases/latest/download/updater.json"""

    with open(path.joinpath("module.prop"), "w", newline="\n") as f:
        f.write(module_prop)


def create_module(version: str):
    logger.info("Creating module")

    if PATH_BUILD_TMP.exists():
        shutil.rmtree(PATH_BUILD_TMP)

    shutil.copytree(PATH_BASE_MODULE, PATH_BUILD_TMP)
    create_module_prop(PATH_BUILD_TMP, version)


def fill_module(arch: str, version: str):
    threading.current_thread().setName(arch)
    logger.info(f"Filling module for arch '{arch}'")

    FGGB_url = f"https://github.com/chihaamin/FGGB/releases/download/{version}/"
    FGGB = f"FGGB-v{version}.zip"
    FGGB_path = PATH_DOWNLOADS.joinpath(FGGB)
    print(FGGB_url + FGGB)
    download_file(FGGB_url + FGGB, FGGB_path)
    files_dir = PATH_BUILD_TMP.joinpath("files")
    files_dir.mkdir(exist_ok=True)
    extract_file(FGGB_path, files_dir.joinpath(f"FGGB-v{version}"))


def create_updater_json(version: str):
    logger.info("Creating updater.json")

    updater = {
        "version": version,
        "versionCode": int(version.replace(".", "").replace("-", "")),
        "zipUrl": f"https://github.com/chihaamin/FGGB-Magisk/releases/download/{version}/FGGB-Magisk-{version}.zip",
        "changelog": "https://raw.githubusercontent.com/chihaamin/FGGB-Magisk/master/CHANGELOG.md",
    }

    with open(PATH_BUILD.joinpath("updater.json"), "w", newline="\n") as f:
        f.write(json.dumps(updater, indent=4))


def package_module(version: str):
    logger.info("Packaging module")

    module_zip = PATH_BUILD.joinpath(f"FGGB-Magisk-{version}.zip")

    with zipfile.ZipFile(module_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(PATH_BUILD_TMP):
            for file_name in files:
                if file_name == "placeholder" or file_name == ".gitkeep":
                    continue
                zf.write(
                    Path(root).joinpath(file_name),
                    arcname=Path(root).relative_to(PATH_BUILD_TMP).joinpath(file_name),
                )

    shutil.rmtree(PATH_BUILD_TMP)


def do_build(v: str, version: str):
    PATH_DOWNLOADS.mkdir(parents=True, exist_ok=True)
    PATH_BUILD.mkdir(parents=True, exist_ok=True)

    create_module(version)

    archs = ["arm64"]
    executor = concurrent.futures.ProcessPoolExecutor()
    futures = [executor.submit(fill_module, arch, v) for arch in archs]
    for future in concurrent.futures.as_completed(futures):
        if future.exception() is not None:
            raise future.exception()
    # TODO: Causes 'OSError: The handle is invalid' in Python 3.7, revert after update
    # executor.shutdown()

    package_module(version)
    create_updater_json(version)

    logger.info("Done")
