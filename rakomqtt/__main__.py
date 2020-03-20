#!/usr/bin/python
import argparse
import logging
import sys

from rakomqtt.commander import run_commander
from rakomqtt.const import __version__, REQUIRED_PYTHON_VER
from rakomqtt.watcher import run_watcher


_LOGGER = logging.getLogger(__name__)


def validate_python() -> None:
    """Validate that the right Python version is running."""
    if sys.version_info[:3] < REQUIRED_PYTHON_VER:
        print(
            "Home Assistant requires at least Python {}.{}.{}".format(
                *REQUIRED_PYTHON_VER
            )
        )
        sys.exit(1)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="rakomqtt: bridge between rako bridge and mqtt iot bus"
    )
    parser.add_argument("--version", action="version", version=__version__)

    parser.add_argument(
        "--debug", action="store_true", help="Start rakomqtt debug mode", default=False
    )

    parser.add_argument(
        "--mode",
        dest='mode',
        type=str,
        choices=['watcher', 'commander'],
        required=True,
        help="which mode to start rakomqtt in",
    )

    parser.add_argument(
        "--mqtt-host",
        type=str,
        required=True,
        help="host name/ip of the mqtt server",
    )

    parser.add_argument(
        "--mqtt-user",
        type=str,
        required=True,
        help="username to use when logging into the mqtt server",
    )

    parser.add_argument(
        "--mqtt-password",
        type=str,
        required=True,
        help="password to use when logging into the mqtt server",
    )

    arguments = parser.parse_args()
    return arguments


def setup_logging(rakomqtt_mode, debug: bool = False) -> None:
    fmt = f"%(asctime)s %(levelname)s (%(threadName)s) [{rakomqtt_mode}] [%(name)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format=fmt, datefmt=datefmt, level=log_level)

    # Suppress overly verbose logs from libraries that aren't helpful
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def run():
    validate_python()

    args = get_args()

    setup_logging(args.mode, args.debug)

    _LOGGER.debug(f'Running the rakomqtt {args.mode}')
    if args.mode == "watcher":
        run_watcher(args.mqtt_host, args.mqtt_user, args.mqtt_password)
    if args.mode == "commander":
        run_commander(args.mqtt_host, args.mqtt_user, args.mqtt_password)


if __name__ == '__main__':
    run()






