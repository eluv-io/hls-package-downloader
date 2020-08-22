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
#   * BYTERANGE (multiple segments per file)
#   * Absolute URIs - Would have to modify playlist
#   * Additional HTTP headers - If needed

import argparse
import logging
import os
import threading
import urllib.request

_auth_header = ""
_bytes_downloaded = 0
_bytes_total = 0
_counter_lock = threading.Lock()
_fetched_dict = dict()
_files_downloaded = 0
_files_total = 0
_max_concurrent_downloads = 10
_out_dir = ""
_threads = list()
_threads_lock = threading.Lock()


def fetch(url: tuple, out_dir: str) -> None:
    global _bytes_total
    global _fetched_dict
    global _files_total

    if not os.path.exists(out_dir):
        try:
            os.makedirs(out_dir)
        except Exception as e:
            logging.debug(f"Failed to make directory {out_dir}: {e}")

    is_playlist, _ = is_playlist_url(url)
    filename = os.path.basename(url.path)
    out_path = os.path.join(out_dir, filename)

    with _counter_lock:
        if out_path in _fetched_dict:
            logging.debug(f"Skipping {out_path} (already fetched)")
            return
        else:
            _fetched_dict[out_path] = True

    if os.path.exists(out_path) and not is_playlist:
        logging.debug(f"Skipping {out_path} (already exists)")
        with _counter_lock:
            _bytes_total += os.path.getsize(out_path)
            _files_total += 1
    else:
        if is_playlist:
            logging.info(f"Downloading playlist to {out_path}")
        else:
            logging.debug(f"Downloading to {out_path}")
        data = read_data_from_url(url)
        write_file(out_path, data)
        if is_playlist:
            parse_playlist(url, out_dir, data)


def fetch_threaded(url: tuple, out_dir: str) -> None:
    global _threads

    t = None
    while True:
        with _threads_lock:
            if len(_threads) < _max_concurrent_downloads:
                t = threading.Thread(target=fetch, args=(url, out_dir))
                _threads.append(t)
                t.start()
                return
            else:
                t = _threads.pop(0)
        t.join()


def fetch_uri_in_playlist(uri: str, playlist_url: tuple, playlist_out_dir: str) -> None:
    uri = uri.strip().strip(b'"').decode()
    url_path = urllib.parse.urlparse(uri)
    if len(url_path.scheme) != 0:
        logging.warning(f"Only relative URIs supported, skipping {uri}")
        return
    playlist_dir = os.path.dirname(playlist_url.path)
    out_dir = os.path.normpath(os.path.join(playlist_out_dir, os.path.dirname(url_path.path.replace("../", ""))))
    path = os.path.normpath(os.path.join(playlist_dir, url_path.path))
    url_path = urllib.parse.ParseResult(
        playlist_url.scheme, playlist_url.netloc, path, "", url_path.query, ""
    )
    if is_playlist_url(url_path)[0]:
        fetch(url_path, out_dir)
    else:
        fetch_threaded(url_path, out_dir)


def is_playlist_url(url: tuple) -> tuple:
    if len(url.path) == 0:
        return False, "Empty url"
    elif not (url.scheme == "http" or url.scheme == "https"):
        return False, "Missing http/https scheme"
    elif os.path.splitext(url.path)[1].lower() != ".m3u8":
        return False, "Extension is not m3u8"
    else:
        return True, None


def parse_playlist(url: tuple, out_dir: str, content: str) -> None:
    for line in content.splitlines():
        line = line.strip()
        if len(line) == 0:
            continue

        # tag
        if line.startswith(b"#EXT"):
            tag_split = line.split(b":", 1)
            if len(tag_split) != 2:
                continue
            # attribute list
            for attr in tag_split[1].split(b","):
                if not attr.startswith(b"URI"):
                    continue
                if b"BYTERANGE" in line:
                    break
                    # raise Exception(f"BYTERANGE not supported: {line}")
                attr_split = attr.split(b"=", 1)
                if len(attr_split) != 2:
                    break
                fetch_uri_in_playlist(attr_split[1], url, out_dir)
                break
            continue

        # comment
        if line.startswith(b"#"):
            continue

        # URI
        fetch_uri_in_playlist(line, url, out_dir)


def read_data_from_url(url: tuple) -> bytes:
    headers = {}
    if len(_auth_header) > 0:
        headers["authorization"] = _auth_header
    request = urllib.request.Request(url=url.geturl(), headers=headers)
    with urllib.request.urlopen(request) as response:
        data = response.read()
    return data


def write_file(path: str, data: bytes) -> None:
    global _bytes_downloaded
    global _bytes_total
    global _files_downloaded
    global _files_total

    with open(path, "wb") as file:
        file.write(data)
    with _counter_lock:
        _bytes_downloaded += len(data)
        _bytes_total += len(data)
        _files_downloaded += 1
        _files_total += 1
    return None


def main():
    global _auth_header
    global _max_concurrent_downloads
    global _out_dir

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
    url_tuple = urllib.parse.urlparse(args.url)
    if args.auth:
        _auth_header = "Bearer " + args.auth
    if args.threads:
        _max_concurrent_downloads = args.threads
    if args.output:
        _out_dir = os.path.abspath(args.output)

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%H:%M:%S",
    )

    is_playlist, message = is_playlist_url(url_tuple)
    if not is_playlist:
        raise Exception(f"Invalid playlist URL: {url_tuple}")

    # Use the "directory" name of the playlist by default
    if len(_out_dir) == 0:
        dirname = os.path.basename(os.path.dirname(url_tuple.path))
        _out_dir = os.path.normpath(os.path.join(os.getcwd(), dirname))
        logging.info(f"Using default output directory: {_out_dir}")
    fetch(url_tuple, _out_dir)

    logging.info(f"Waiting for {len(_threads)} threads to finish")
    while True:
        thread = None
        with _threads_lock:
            if len(_threads) == 0:
                break
            else:
                thread = _threads.pop(0)
                logging.debug(f"{len(_threads)}")
        thread.join()
    logging.info(
        f"Done\n  {_bytes_downloaded} bytes downloaded\n  {_bytes_total} bytes total\n  {_files_downloaded} files downloaded\n  {_files_total} files total")
    os.system(f"echo {_bytes_downloaded} bytes downloaded | numfmt --to=iec-i")
    os.system(f"echo {_bytes_total} bytes total | numfmt --to=iec-i")

    return None


if __name__ == "__main__":
    main()
