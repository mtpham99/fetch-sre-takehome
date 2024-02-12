import argparse
import asyncio
import enum
import logging
import os
import sys
from typing import Optional, TypedDict
from urllib.parse import urlparse

import aiohttp
import yaml

CHECKUP_FREQUENCY_S = 15.0  # number of seconds between each endpoint checkup
ENDPOINT_UP_TIMELIMIT = 0.5  # respone timelimit to be considered up


class EndpointStatus(enum.Enum):
    UP = "up"
    DOWN = "down"


class HTTPEndpointData(TypedDict):
    name: str
    url: str
    method: str  # defaults to "GET"
    headers: Optional[dict[str, str]]  # key:value pairs (or None)
    body: Optional[str]  # JSON encoded string (or None)


def url_to_domain(url: str) -> str:
    return urlparse(url).netloc  # scheme://netloc/path...


def parse_input(configfile: str) -> list[HTTPEndpointData]:
    endpoints: list[HTTPEndpointData] = []
    with open(configfile, "r") as f:  # pylint: disable=unspecified-encoding
        for entry in yaml.safe_load(f):
            endpoints.append(
                HTTPEndpointData(
                    {
                        "name": entry["name"],
                        "url": entry["url"],
                        "method": entry.get(
                            "method", "GET"  # defaults to "GET" method)
                        ),
                        "headers": entry.get("headers", None),
                        "body": entry.get("body", None),
                    }
                )
            )
    return endpoints


async def check_endpoint(
    endpoint: HTTPEndpointData,
    session: aiohttp.ClientSession,
) -> tuple[str, EndpointStatus]:

    url = endpoint["url"]
    method = endpoint["method"]
    headers = endpoint["headers"]
    body = endpoint["body"]

    status: EndpointStatus
    try:
        async with session.request(
            method=method,
            url=url,
            headers=headers,
            json=body,
            timeout=aiohttp.ClientTimeout(total=ENDPOINT_UP_TIMELIMIT),
        ) as resp:
            # endpoint is up if status code [200, 299]
            if 200 <= resp.status <= 299:
                status = EndpointStatus.UP
            else:
                status = EndpointStatus.DOWN

    # endpoint is down in case of timeout
    except asyncio.TimeoutError:
        status = EndpointStatus.DOWN

    return (url, status)


async def mainloop(endpoints: list[HTTPEndpointData]) -> None:
    # create aiohttp client session
    connector = aiohttp.TCPConnector(limit=None)  # type: ignore [arg-type]
    timeout = aiohttp.ClientTimeout(total=None)
    async with aiohttp.ClientSession(
        connector=connector, timeout=timeout
    ) as session:

        # keep track of up counts/availability
        domains_up_counts = {
            url_to_domain(ep["url"]): {"ups": 0, "total": 0}
            for ep in endpoints
        }

        # main loop
        while True:

            # check endpoints
            coros = [check_endpoint(ep, session) for ep in endpoints]
            for task in asyncio.as_completed(coros):

                # get url, url/endpoint's status, and domain
                url, status = await task
                domain = url_to_domain(url)

                # update counts
                domains_up_counts[domain]["total"] += 1
                if status is EndpointStatus.UP:
                    domains_up_counts[domain]["ups"] += 1

            # print/log counts
            for domain, counts in domains_up_counts.items():
                ups = counts["ups"]
                total = counts["total"]
                logging.log(
                    level=logging.INFO,
                    msg=(
                        f"{domain} has {round(100.0 * ups / total)}%"
                        " availability percentage"
                    ),
                )

            # sleep until next iteration
            await asyncio.sleep(CHECKUP_FREQUENCY_S)


if __name__ == "__main__":

    # logging (stdout)
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # parse arg(s)
    parser = argparse.ArgumentParser(
        prog="HTTP Endpoint Checkup",
        description=(
            "Script to parse a yaml file with a set of endpoints and "
            "check whether the endpoints are up or down every 15 sesconds."
        ),
    )
    parser.add_argument(
        "configfile",
        help="Path to yaml config file containing set of http(s) endpoints",
        type=str,
    )
    args = parser.parse_args()

    # check input
    if not os.path.isfile(args.configfile):
        raise ValueError(
            f'Config file path ("{args.configfile}") is not a file. Aborting.'
        )

    # parse input
    endpoints_list: list[HTTPEndpointData] = parse_input(args.configfile)

    # run main until user interrupt
    try:
        asyncio.run(mainloop(endpoints_list))

    # user interrupt
    except KeyboardInterrupt:
        pass
