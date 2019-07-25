# hls-package-downloader
Download an HLS playlist and segment files for all renditions and variant
streams. Currently does not support absolute and byte range URIs.

```
usage: hpd.py [-h] [-a AUTH] [-o OUTPUT] [-t THREADS] [-v] url

positional arguments:
  url                   the HLS playlist/manifest URL, e.g.
                        https://devstreaming-cdn.apple.com/videos/streaming/ex
                        amples/img_bipbop_adv_example_ts/master.m3u8

optional arguments:
  -h, --help            show this help message and exit
  -a AUTH, --auth AUTH  set a bearer token authorization header with each HTTP
                        request
  -o OUTPUT, --output OUTPUT
                        the output directory path
  -t THREADS, --threads THREADS
                        the maximum number of concurrent downloads
  -v, --verbose         verbose logging



./hpd.py -t 10 https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_ts/master.m3u8
16:53:00 INFO Using default output directory: /temp/img_bipbop_adv_example_ts
16:53:00 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/master.m3u8
16:53:00 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/v5/prog_index.m3u8
16:53:00 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/v9/prog_index.m3u8
16:53:00 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/v8/prog_index.m3u8
16:53:00 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/v7/prog_index.m3u8
16:53:01 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/v6/prog_index.m3u8
16:53:01 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/v4/prog_index.m3u8
16:53:01 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/v3/prog_index.m3u8
16:53:01 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/v2/prog_index.m3u8
16:53:01 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/v7/iframe_index.m3u8
16:53:01 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/v6/iframe_index.m3u8
16:53:01 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/v5/iframe_index.m3u8
16:53:01 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/v4/iframe_index.m3u8
16:53:01 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/v3/iframe_index.m3u8
16:53:01 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/v2/iframe_index.m3u8
16:53:01 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/a1/prog_index.m3u8
16:53:01 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/a2/prog_index.m3u8
16:53:01 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/a3/prog_index.m3u8
16:53:01 INFO Downloading playlist to /temp/img_bipbop_adv_example_ts/s1/en/prog_index.m3u8
16:53:01 INFO Waiting for 10 threads to finish
16:53:01 INFO Done
  2015634578 bytes downloaded
  2015634578 bytes total
  1222 files downloaded
  1222 files total
187Ki bytes downloaded
1.9Gi bytes total
```
