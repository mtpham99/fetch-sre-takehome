# Fetch SRE Take-Home Exercise

This is my submission for [Fetch's](https://fetch.com/) site reliability engineer take-home exercise.


## HTTP Endpoint Health Checker

### 1. About

This python script ("http_endpoint_checkup.py") reads in a set of HTTP(S) endpoints via a path to a YAML file and checks whether the endpoints are "up" every 15 seconds.

Endpoints are considered "up" if they give a response within 500 [ms] and a 2xx status code (i.e. between 200-299 inclusive)

This script utilizes [aiohttp](https://docs.aiohttp.org/en/stable/index.html) to perform asynchronous http requests.


### 2. Usage

This script is written in python and was tested with python 3.9-3.12 on Linux (openSuse Tumebleweed). The instructions below should work on any Unix like OS. Windows users may need to tweak some of the commands below (e.g. virtual environment usage).

***Running this script requires python >= 3.9 and pip for installing dependencies***.


#### 2.1 Dependencies

1. [aiohttp](https://docs.aiohttp.org/en/stable/index.html)
2. [pyyaml](https://pyyaml.org/)


#### 2.2 Install/Setup

First clone this repository:

```
git clone https://github.com/mtpham99/fetch-sre-takehome.git
cd fetch-sre-takehome
```

Next, install the dependencies. Easiest way to install the dependencies is using [pip](https://pypi.org/project/pip/). It is also recommended to install into a virtual environment:

```
# assuming python3 is >= 3.9
python3 -m venv /path/to/virtual-environment  # create virtual environment
source /path/to/virtual-environment/bin/activate  # activate virtual environment
pip install . # install dependencies (aiohttp and pyyaml)
```

#### 2.3 Running

See "help":
```
python3 http_endpoint_checkup.py --help
```

Run the sample inputs:
```
python3 http_endpoint_checkup.py sample.yaml
```

Run your own input file:
```
python3 http_endpoint_checkup.py /path/to/your/input/yaml/file
```

