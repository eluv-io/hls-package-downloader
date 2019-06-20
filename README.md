# hls-package-downloader
Download an HLS playlist and segment files for all renditions and variant streams

```
usage: hpd.py [-h] [-a AUTH] [-t THREADS] url

positional arguments:
  url                   the HLS playlist/manifest URL, e.g.
                        https://devstreaming-cdn.apple.com/videos/streaming/ex
                        amples/img_bipbop_adv_example_ts/master.m3u8

optional arguments:
  -h, --help            show this help message and exit
  -a AUTH, --auth AUTH  set a bearer token authorization header with each HTTP
                        request
  -t THREADS, --threads THREADS
                        the maximum number of concurrent downloads
```
