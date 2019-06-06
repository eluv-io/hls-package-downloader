#!/usr/bin/env python3
#
# Modified from:
# https://gist.github.com/anonymouss/5293c2421b4236fc1a38705fefd4f2e7
#
# Http Live Streaming -- fetcher/downloader
# A simple script to download segments/m3u8 files from given url, including
#   variants and alternative renditions.

import sys
import os
import urllib.request

TEST_URL = "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8"


def isValidUrl(url: str) -> bool:
    if url == "":
        print("Invalid URL: empty url")
        return False
    elif not (url.startswith("http") or url.startswith("https")):
        print("Invalid URL: require 'http/https' url")
        return False
    elif os.path.splitext(url)[1].lower() != ".m3u8":
        print("Invalid URL: not hls source")
        return False
    else:
        return True


def readDataFromUrl(url: str) -> bytes:
    with urllib.request.urlopen(url) as response:
        data = response.read()
    return data


def writeFile(path: str, filename: str, data: bytes) -> None:
    fullPath = os.path.join(path, filename)
    with open(fullPath, "wb") as file:
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
                uri = attrSplit[1].strip(b'"').decode()
                fullUrl = os.path.join(baseUrl, relativePath, uri)
                fetch(fullUrl, baseDir, baseUrl)
        elif extension.lower() == b".m3u8":
            playlistUrl = baseUrl + "/" + line.decode()
            fetch(playlistUrl, baseDir, baseUrl)
        elif len(extension) > 0:
            segUrl = os.path.join(baseUrl, relativePath, line.decode())
            fetch(segUrl, baseDir, baseUrl)


def fetch(url: str, baseDir: str, baseUrl: str) -> None:
    # print("\nfetch", "\nurl:", url, "\nbaseDir:", baseDir, "\nbaseUrl:", baseUrl)
    filename = os.path.basename(url)
    relPath = os.path.dirname(url)[len(baseUrl):].strip('/')
    writeDir = os.path.join(baseDir, relPath)
    if not os.path.exists(writeDir):
        os.makedirs(writeDir)
    print("Downloading", url, "to", writeDir)
    data = readDataFromUrl(url)
    writeFile(writeDir, filename, data)

    extension = os.path.splitext(filename)[1]
    if extension.lower() == ".m3u8":
        parsePlaylist(baseDir, relPath, baseUrl, data)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Invalid arguments: require 1 parameter, but you gave ", len(sys.argv) - 1
        )
        exit(-1)
    url = sys.argv[1]
    # url = TEST_URL
    if isValidUrl(url):
        # http://.../hls-aes/playlist.m3u8
        # http://.../hls-aes
        baseUrl = os.path.dirname(url)
        # /a/b/c
        curPath = os.path.abspath(os.curdir)
        # /a/b/c/hls-aes
        writeDir = os.path.join(curPath, os.path.basename(baseUrl))
        fetch(url, writeDir, baseUrl)
        print("Done")
    else:
        exit(-1)
