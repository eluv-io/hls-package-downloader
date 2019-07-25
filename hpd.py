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
#   * BYTERANGE
#   * Absolute URIs - Would have to modify playlist
#   * HTTP headers - If needed

import argparse
import logging
import os
import threading
import urllib.request

_authHeader = ""
_bytesDownloaded = 0
_bytesTotal = 0
_counterLock = threading.Lock()
_fetchedDict = dict()
_filesDownloaded = 0
_filesTotal = 0
_maxConcurrentDownloads = 10
_outDir = ""
_threads = list()
_threadsLock = threading.Lock()

def fetch(url: tuple, outDir: str) -> None:
    global _bytesTotal
    global _fetchedDict
    global _filesTotal

    if not os.path.exists(outDir):
        os.makedirs(outDir)

    isPlaylist, _ = isPlaylistUrl(url)
    filename = os.path.basename(url.path)
    outPath = os.path.join(outDir, filename)

    with _counterLock:
        if outPath in _fetchedDict:
            logging.debug(f"Skipping {outPath} (already fetched)")
            return
        else:
            _fetchedDict[outPath] = True

    if os.path.exists(outPath) and not isPlaylist:
        logging.debug(f"Skipping {outPath} (already exists)")
        with _counterLock:
            _bytesTotal += os.path.getsize(outPath)
            _filesTotal += 1
    else:
        if isPlaylist:
            logging.info(f"Downloading playlist to {outPath}")
        else:
            logging.debug(f"Downloading to {outPath}")
        data = readDataFromUrl(url)
        writeFile(outPath, data)
        if isPlaylist:
            parsePlaylist(url, outDir, data)
        
def fetchThreaded(url: tuple, outDir: str) -> None:
    global _threads

    thread = None
    while True:
        with _threadsLock:
            if len(_threads) < _maxConcurrentDownloads:
                thread = threading.Thread(target=fetch, args=(url, outDir))
                _threads.append(thread)
                thread.start()
                return
            else:
                thread = _threads.pop(0)
        thread.join()

def fetchUriInPlaylist(uri: str, playlistUrl: tuple, playlistOutDir: str) -> None:
    uri = uri.strip().strip(b'"').decode()
    url = urllib.parse.urlparse(uri)
    if len(url.scheme) != 0:
        logging.warning(f"Only relative URIs supported, skipping {uri}")
        return
    playlistDir = os.path.dirname(playlistUrl.path)
    outDir = os.path.normpath(os.path.join(playlistOutDir, os.path.dirname(url.path)))
    path = os.path.normpath(os.path.join(playlistDir, url.path))
    url = urllib.parse.ParseResult(
        playlistUrl.scheme, playlistUrl.netloc, path, "", url.query, ""
    )
    if isPlaylistUrl(url)[0]:
        fetch(url, outDir)
    else:
        fetchThreaded(url, outDir)

def isPlaylistUrl(url: tuple) -> tuple:
    if len(url.path) == 0:
        return False, "Empty url"
    elif not (url.scheme == "http" or url.scheme == "https"):
        return False, "Missing http/https scheme"
    elif os.path.splitext(url.path)[1].lower() != ".m3u8":
        return False, "Extension is not m3u8"
    else:
        return True, None

def parsePlaylist(url: tuple, outDir: str, content: str) -> None:
    for line in content.splitlines():
        line = line.strip()
        if len(line) == 0:
            continue

        # tag
        if line.startswith(b"#EXT"):
            tagSplit = line.split(b":", 1)
            if len(tagSplit) != 2:
                continue
            # attribute list
            for attr in tagSplit[1].split(b","):
                if not attr.startswith(b"URI"):
                    continue
                if b"BYTERANGE" in line:
                    raise Exception(f"BYTERANGE not supported: {line}")
                attrSplit = attr.split(b"=", 1)
                if len(attrSplit) != 2:
                    break
                uri = attrSplit[1].strip().strip(b'"').decode()
                fetchUriInPlaylist(attrSplit[1], url, outDir)
                break
            continue
        
        # comment
        if line.startswith(b"#"):
            continue

        # URI
        fetchUriInPlaylist(line, url, outDir)

def readDataFromUrl(url: tuple) -> bytes:
    headers = {}
    if len(_authHeader) > 0:
        headers["authorization"] = _authHeader
    request = urllib.request.Request(url=url.geturl(), headers=headers)
    with urllib.request.urlopen(request) as response:
        data = response.read()
    return data

def writeFile(path: str, data: bytes) -> None:
    global _bytesDownloaded
    global _bytesTotal
    global _filesDownloaded
    global _filesTotal

    with open(path, "wb") as file:
        file.write(data)
    with _counterLock:
        _bytesDownloaded += len(data)
        _bytesTotal += len(data)
        _filesDownloaded += 1
        _filesTotal += 1
    return None

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
    parser.add_argument("-o", "--output", help="the output directory path", type=str)
    parser.add_argument(
        "-t", "--threads", help="the maximum number of concurrent downloads", type=int
    )
    parser.add_argument("-v", "--verbose", help="verbose logging", action="store_true")
    args = parser.parse_args()
    url = urllib.parse.urlparse(args.url)
    if args.auth:
        _authHeader = "Bearer " + args.auth
    if args.threads:
        _maxConcurrentDownloads = args.threads
    if args.output:
        _outDir = os.path.abspath(args.output)

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%H:%M:%S",
    )

    isPlaylist, message = isPlaylistUrl(url)
    if not isPlaylist:
        raise Exception(f"Invalid playlist URL: {url}")

    # Use the "directory" name of the playlist by default
    if len(_outDir) == 0:
        dirname = os.path.basename(os.path.dirname(url.path))
        _outDir = os.path.normpath(os.path.join(os.getcwd(), dirname))
        logging.info(f"Using default output directory: {_outDir}")
    fetch(url, _outDir)

    logging.info(f"Waiting for {len(_threads)} threads to finish")
    while True:
        thread = None
        with _threadsLock:
            if len(_threads) == 0:
                break
            else:
                thread = _threads.pop(0)
                logging.debug(f"{len(_threads)}")
        thread.join()
    logging.info(f"Done\n  {_bytesDownloaded} bytes downloaded\n  {_bytesTotal} bytes total\n  {_filesDownloaded} files downloaded\n  {_filesTotal} files total")
    os.system(f"echo {_bytesDownloaded} bytes downloaded | numfmt --to=iec-i")
    os.system(f"echo {_bytesTotal} bytes total | numfmt --to=iec-i")
