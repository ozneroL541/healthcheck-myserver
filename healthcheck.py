#!/usr/bin/env python3

import os
import logging

from healthchecker import HealthChecker

def load_dotenv_file(path:str=".env") -> None:
    '''
    Load environment variables from a .env file if present.
    '''
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except OSError:
        logging.error("Unable to read .env file.")

def main() -> None:
    load_dotenv_file()
    hc_uuid:str = os.environ.get("HC_UUID")
    ''' UUID for Healthchecks.io'''
    req_timeout_env = os.environ.get("REQUEST_TIMEOUT")
    ''' HTTP request timeout in seconds, as a string from the environment variable'''
    req_timeout:float = float(req_timeout_env) if req_timeout_env else None
    ''' HTTP request timeout in seconds'''
    sleep_minutes = os.environ.get("SLEEP_MINUTES")
    ''' Time to sleep between pings in minutes'''
    sleep_time:int = int(sleep_minutes) * 60 if sleep_minutes else None
    ''' Time to sleep between pings in seconds'''
    health_checker = HealthChecker(hc_uuid=hc_uuid, req_timeout=req_timeout, sleep_time=sleep_time)
    ''' HealthChecker instance initialized with the specified parameters '''
    # Start the healthcheck loop, which will run indefinitely until a termination signal is received
    health_checker.run_pings()

if __name__ == "__main__":
    main()
