#!/usr/bin/env python3
#
# Modified from:
# https://gist.github.com/anonymouss/5293c2421b4236fc1a38705fefd4f2e7
#
# Http Live Streaming -- fetcher/downloader
# A simple script to download segments/m3u8 files from given url, including
#   variants and alternative renditions.
#
# TODO
#   * Support packages with all segments in a single file with byte range requests
#   * Add output directory option
#   * Add logging verbosity option

import argparse
import logging
import os
import threading
import urllib.request

auth_header = ""
lock = threading.Lock()
threads = list()
max_threads = 10


def isValidUrl(url: str) -> bool:
    if url == "":
        logging.error("Invalid URL: empty url")
        return False
    elif not (url.startswith("http") or url.startswith("https")):
        logging.error("Invalid URL: require 'http/https' url")
        return False
    elif os.path.splitext(url)[1].lower() != ".m3u8":
        logging.error("Invalid URL: not hls source")
        return False
    else:
        return True


def readDataFromUrl(url: str) -> bytes:
    headers = {}
    if len(auth_header) > 0:
        headers["authorization"] = auth_header
    request = urllib.request.Request(url=url, headers=headers)
    with urllib.request.urlopen(request) as response:
        data = response.read()
    return data


def writeFile(path: str, data: bytes) -> None:
    with open(path, "wb") as file:
        file.write(data)
    return None


def parsePlaylist(baseDir: str, relativePath: str, baseUrl: str, data: bytes) -> None:
    for line in data.splitlines():
        line = line.strip()
        extension = os.path.splitext(line)[1]
        if line.startswith(b"#"):
            extSplit = line.split(b":", 1)
            if len(extSplit) != 2:
                continue
            for attr in extSplit[1].split(b","):
                if not attr.startswith(b"URI"):
                    continue
                attrSplit = attr.split(b"=", 1)
                if len(attrSplit) != 2:
                    break
                # TODO Only handles relative paths right now
                uri = attrSplit[1].strip().strip(b'"').decode()
                fullUrl = os.path.join(baseUrl, relativePath, uri)
                fetch(fullUrl, baseDir, baseUrl)
        elif extension.lower() == b".m3u8":
            playlistUrl = baseUrl + "/" + line.decode()
            fetch(playlistUrl, baseDir, baseUrl)
        elif len(extension) > 0:
            segUrl = os.path.join(baseUrl, relativePath, line.decode())
            threadedFetch(segUrl, baseDir, baseUrl)


def threadedFetch(url: str, baseDir: str, baseUrl: str) -> None:
    thread = None
    while True:
        with lock:
            if len(threads) >= max_threads:
                thread = threads.pop(0)
            else:
                thread = threading.Thread(target=fetch, args=(url, baseDir, baseUrl))
                threads.append(thread)
                break
        thread.join()
    thread.start()


def fetch(url: str, baseDir: str, baseUrl: str) -> None:
    # print("\nfetch", "\nurl:", url, "\nbaseDir:", baseDir, "\nbaseUrl:", baseUrl)
    filename = os.path.basename(url)
    extension = os.path.splitext(filename)[1]
    relPath = os.path.dirname(url)[len(baseUrl) :].strip("/")
    outDir = os.path.join(baseDir, relPath)
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    outPath = os.path.join(outDir, filename)
    if os.path.exists(outPath) and extension.lower() != ".m3u8":
        logging.debug("Skipping %s, %s already exists", url, outPath)
        return
    logging.debug("Downloading %s to %s", url, outDir)
    data = readDataFromUrl(url)
    writeFile(outPath, data)
    if extension.lower() == ".m3u8":
        parsePlaylist(baseDir, relPath, baseUrl, data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "url",
        help="the HLS playlist/manifest URL, e.g. https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_ts/master.m3u8",
        type=str,
    )
    parser.add_argument(
        "-a",
        "--auth",
        help="set a bearer token authorization header with each HTTP request",
        type=str,
    )
    parser.add_argument(
        "-t", "--threads", help="the maximum number of concurrent downloads", type=int
    )
    args = parser.parse_args()
    url = args.url
    if args.auth:
        auth_header = "Bearer " + args.auth
    if args.threads:
        max_threads = args.threads

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=logging.DEBUG,
        datefmt="%H:%M:%S",
    )

    if isValidUrl(url):
        # url:       http://.../hls-aes/playlist.m3u8
        # baseUrl:   http://.../hls-aes
        baseUrl = os.path.dirname(url)

        # curPath:   /a/b/c
        curPath = os.path.abspath(os.curdir)

        # outDir:    /a/b/c/hls-aes
        outDir = os.path.join(curPath, os.path.basename(baseUrl))

        fetch(url, outDir, baseUrl)

        while True:
            thread = None
            with lock:
                if len(threads) == 0:
                    break
                else:
                    thread = threads.pop(0)
            thread.join()
        logging.info("Done")
    else:
        exit(-1)
