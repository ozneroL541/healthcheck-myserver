#!/bin/python3

import logging
import os
import time
import requests
import threading
import signal

hc_uuid:str = os.environ.get("HC_UUID")
''' UUID for Healthchecks.io'''
req_timeout:float = float(os.environ.get("REQUEST_TIMEOUT", 10))
''' HTTP request timeout in seconds'''
sleep_time:int = int(os.environ.get("SLEEP_MINUTES"))*60
''' Time to sleep between pings in minutes'''
ping_number:int = 0
''' Number of pings sent to Healthchecks.io from the start'''
ping_number_lock = threading.Lock()
''' Lock to ensure thread-safe increment of the ping counter'''

def set_logging() -> None:
    '''
    Configure logging settings for the healthcheck script.
    '''
    logging.basicConfig(level=logging.INFO)

def check_env_set() -> None:
    '''
    Check if the required environment variables are set and log an error if any are missing.
    If any required environment variable is missing, the function will log an error and exit the program.
    '''
    global hc_uuid
    global req_timeout
    global sleep_time
    env_vars = {
        "HC_UUID": hc_uuid,
        "REQUEST_TIMEOUT": req_timeout,
        "SLEEP_MINUTES": sleep_time
    }
    ok:bool = True
    for var_name, var_value in env_vars.items():
        if var_value is None:
            logging.error(f"{var_name} not found in environment variables.")
            ok = False
    if not ok:
        logging.error("Please set the required environment variables and try again.")
        exit(1)

def get_uptime() -> str:
    '''
    Get the system uptime in a human-readable format.
    Returns:
        str: Uptime formatted as "Xh Ymin Zs".
    '''
    try:
        # Read the uptime from /proc/uptime
        with open("/proc/uptime", "r", encoding="utf-8") as uptime_file:
            uptime_seconds = int(float(uptime_file.readline().split()[0]))
    except (OSError, ValueError, IndexError):
        logging.error("Unable to read system uptime.")
        return "0s"
    # Convert uptime from seconds to hours, minutes, and seconds
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    # Format the uptime string
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}min")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    # Join the parts into a single string
    return " ".join(parts)

def get_time() -> str:
    '''
    Get the current system time in a human-readable format.
    Returns:
        str: Current time formatted as "YYYY-MM-DD HH:MM:SS".
    '''
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def get_ping_number() -> int:
    '''
    Get the current ping number.
    Returns:
        int: The number of pings sent to Healthchecks.io.
    '''
    global ping_number
    # Use a lock to ensure thread-safe increment of the ping counter
    with ping_number_lock:
        current_ping:int = ping_number
        ping_number += 1
        return current_ping

def make_payload(status:str, info:dict= None) -> dict:
    '''
    Create a payload for the healthcheck request containing uptime and current time.
    Args:
        status (str): The status of the ping, can be "ping", "start", or "stop".
        info (dict, optional): Additional information to include in the payload. Defaults to None.
    Returns:
        dict: Payload with "uptime" and "timestamp" keys.
    '''
    payload = {
        "status": status,
        "ping_number": get_ping_number(),
        "timestamp": get_time(),
        "uptime": get_uptime()
    }
    if info:
        payload.update(info)
    return payload

def ping_healthcheck(mode:str="ping") -> bool:
    '''
    Send a ping to the Healthchecks.io endpoint with the specified mode.
    Args:
        mode (str): The mode of the ping, can be "ping", "start", or "stop".
    Returns:
        bool: True if the ping was successful (HTTP 200), False otherwise.
    '''
    global hc_uuid
    global req_timeout
    url:str = "https://hc-ping.com/%s" % (hc_uuid)
    if mode != "ping":
        url += "/%s" % mode
    try:
        response = requests.post(
            url,
            timeout=req_timeout,
            params=make_payload(status=mode)
            )
        return response.status_code == 200
    except requests.RequestException as e:
        logging.error("Ping failed: %s" % e)
        return False
    
def start_healthcheck() -> bool:
    '''
    Start the healthcheck by sending a "start" ping to Healthchecks.io.
    Returns:
        bool: True if the start ping was successful, False otherwise.'''
    return ping_healthcheck(mode="start")

def stop_healthcheck() -> bool:
    '''
    Stop the healthcheck by sending a "stop" ping to Healthchecks.io.
    Returns:
        bool: True if the stop ping was successful, False otherwise.
    '''
    return ping_healthcheck(mode="stop")

def ping_and_sleep() -> None:
    '''
    Send a ping to Healthchecks.io and then sleep for the configured amount of time.
    If the ping is successful, sleep for the full configured time. If the ping fails, sleep for half the configured time before trying again.
    '''
    if ping_healthcheck():
        logging.info("Ping successful. Sleeping for %d minutes." % sleep_time)
        time.sleep(sleep_time)
    else:
        logging.error("Ping failed. Sleeping for %d minutes." % (sleep_time/2))
        time.sleep(sleep_time/2)

def graceful_exit() -> bool:
    '''
    Perform a graceful shutdown by sending a "stop" ping to Healthchecks.io and logging the shutdown process.
    If the stop ping is successful, log a success message. If it fails, log an error message. Finally, exit the program.
    '''
    logging.info("Shutting down gracefully...")
    if stop_healthcheck():
        logging.info("Healthcheck stopped successfully.")
        return True
    else:
        logging.error("Failed to gracefully stop healthcheck.")
        return False

def _signal_handler(signum, frame):
    '''
    Handle termination signals (SIGTERM and SIGINT) to ensure a graceful shutdown of the healthcheck script.
    When a termination signal is received, this handler will log the signal, 
    attempt to perform a graceful exit by sending a "stop" ping to Healthchecks.io, 
    and then exit the program with an appropriate status code based on the success of the graceful exit.
    Args:
        signum: The signal number received.
        frame: The current stack frame (not used in this handler).
    '''
    logging.info("Received signal %s", signum)
    exit:bool = graceful_exit()
    exit(0 if exit else 1)

def main():
    set_logging()
    check_env_set()
    # Register signal handlers to ensure graceful shutdown on termination
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
    if not start_healthcheck():
        exit(1)
    while True:
        ping_healthcheck()

if __name__ == "__main__":
    main()
