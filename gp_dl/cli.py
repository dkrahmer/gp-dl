import argparse, logging, sys, time
from statistics import median
from .lib import download_albums, login, list_albums

BANNER = """
██████   ██████         ██████  ██
██       ██   ██        ██   ██ ██
██   ███ ██████   █████ ██   ██ ██
██    ██ ██             ██   ██ ██
██████   ██             ██████  ███████

gp-dl — Google Photos Downloader
Download full-resolution albums from Google Photos using Selenium

Author: csd4ni3l  |  GitHub: https://github.com/csd4ni3l
"""

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "ERROR": logging.ERROR,
    "FATAL": logging.FATAL,
    "QUIET": 999999999
}

def parse_cli_args():
    parser = argparse.ArgumentParser(description="Download full-res images from a Google Photos album using Selenium.")
    parser.add_argument("--album-urls", nargs="+", help="Google Photos album URL(s)")
    parser.add_argument("--output-dir", default=None, required=True, help="The directory to save downloaded albums")
    parser.add_argument("--driver-path", default=None, help="Custom Chrome driver path")
    parser.add_argument("--profile-dir", default=None, help="A Chrome user data directory for sessions, set this if you want to open non-shared links.")
    parser.add_argument("--headless", action="store_true", help="Run Chrome headlessly")
    parser.add_argument("--user", default=None, help="Google user login (ie. email address)")
    parser.add_argument("--password", default=None, help="Google user password")
    parser.add_argument("--log-level", default="INFO", help="Specifies what to include in log output. Available levels: debug, info, error, fatal")
    return parser.parse_args()

def configure_logging(log_level: str):
    if not log_level.upper() in LOG_LEVELS:
        print(f"Invalid logging level: {log_level}")
        sys.exit(1)

    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=LOG_LEVELS[log_level.upper()])
    for logger_to_disable in ["selenium", "urllib3"]:
        logging.getLogger(logger_to_disable).propagate = False
        logging.getLogger(logger_to_disable).disabled = True

def run_cli():
    args = parse_cli_args()
    
    if not args.log_level.upper() == "QUIET":
        print(BANNER)

    configure_logging(args.log_level)

    all_start = time.perf_counter()
    album_urls = args.album_urls
    if not args.album_urls:
        album_urls = list_albums(driver_path=args.driver_path, profile_dir=args.profile_dir, headless=args.headless, user=args.user, password=args.password)

    successful_albums, failed_albums, album_times = download_albums(album_urls, args.output_dir, args.driver_path, args.profile_dir, args.headless)

    logging.info("")
    logging.info("===== DOWNLOAD STATISTICS =====")
    logging.info(f"Total albums given: {len(album_urls)}")
    logging.info(f"Successful albums ({len(successful_albums)}): {', '.join(successful_albums) or None}")
    logging.info(f"Failed albums ({len(failed_albums)}): {', '.join(failed_albums) or 'None'}")
    logging.info(f"Median time taken per album: {median(album_times or [0]):.2f} seconds")
    logging.info(f"Average time taken per album: {sum(album_times or [0]) / len(album_times or [0]):.2f} seconds")
    logging.info(f"Total time taken: {time.perf_counter() - all_start:.2f} seconds")
    logging.info("================================")