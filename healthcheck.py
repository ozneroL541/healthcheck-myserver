#!/usr/bin/env python3

import logging
import os
import time
import requests
import threading
import signal

def load_dotenv_file(path: str = ".env") -> None:
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
        else:
            logging.info(f"{var_name} is set to {var_value}.")
    if not ok:
        logging.error("Please set the required environment variables and try again.")
        exit(1)
    else:
        logging.info("All required environment variables are set.")

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

def ping_healthcheck(signal:str= None, mode:str="ping") -> bool:
    '''
    Send a ping to the Healthchecks.io endpoint with the specified mode.
    Args:
        signal (str, optional): The signal to send. Defaults to None.
        mode (str): The mode of the ping, can be "ping", "start", or "stop".
    Returns:
        bool: True if the ping was successful (HTTP 200), False otherwise.
    '''
    global hc_uuid
    global req_timeout
    extra_info:dict = {}
    ''' Extra information to include in the log messages'''
    url:str = "https://hc-ping.com/%s" % (hc_uuid)
    ''' URL for the Healthchecks.io ping endpoint'''
    # If the mode is not "ping", append the mode to the URL
    if signal is not None:
        url += "/%s" % signal
    req = {"url": url, "timeout": req_timeout, "payload": make_payload(status=mode)}
    extra_info.update({"request": req})
    try:
        response = requests.post(
            url=req["url"],
            timeout=req["timeout"],
            json=req["payload"]
            )
        extra_info.update({"response": {"status_code": response.status_code, "text": response.text}})
        if response.status_code == 200:
            logging.info(f"Ping {mode} successful: {response.text}", extra=extra_info)
            return True
        else:
            logging.warning(
                f"Ping {mode} failed with status code {response.status_code}: {response.text}",
                extra=extra_info
                )
            return False
    except requests.RequestException as e:
        extra_info.update({"error": str(e)})
        logging.warning(f"Ping {mode} failed: {e}", extra=extra_info)
        return False
    
def start_healthcheck() -> bool:
    '''
    Start the healthcheck by sending a "start" ping to Healthchecks.io.
    Returns:
        bool: True if the start ping was successful, False otherwise.'''
    return ping_healthcheck(signal="start", mode="start")

def stop_healthcheck() -> bool:
    '''
    Stop the healthcheck by sending a "stop" ping to Healthchecks.io.
    Returns:
        bool: True if the stop ping was successful, False otherwise.
    '''
    return ping_healthcheck(signal="fail", mode="stop")

def ping_and_sleep() -> None:
    '''
    Send a ping to Healthchecks.io and then sleep for the configured amount of time.
    If the ping is successful, sleep for the full configured time. If the ping fails, sleep for half the configured time before trying again.
    '''
    global sleep_time
    st:int = sleep_time
    ''' Time to sleep in seconds'''
    if ping_healthcheck():
        logging.info("Ping successful. Sleeping for %d minutes." % (st/60))
    else:
        st = sleep_time/2
        logging.warning("Ping failed. Sleeping for %d minutes." % (st/60))
    try:
        # Sleep for the configured amount of time, but allow interruption by signals
        time.sleep(st)
    except Exception as e:
        logging.error("Sleep interrupted: %s" % e)

def graceful_exit() -> bool:
    '''
    Perform a graceful shutdown by sending a "stop" ping to Healthchecks.io and logging the shutdown process.
    If the stop ping is successful, log a success message. If it fails, log an error message. Finally, exit the program.
    '''
    logging.info("Shutting down gracefully...")
    try:
        if stop_healthcheck():
            logging.info("Healthcheck stopped successfully.")
            exit(0)
        else:
            logging.error("Failed to gracefully stop healthcheck.")
            exit(1)
    except Exception as e:
        logging.error(f"Error during graceful shutdown: {e}")
        exit(1)

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
    graceful_exit()

def main():
    set_logging()
    check_env_set()
    # Register signal handlers to ensure graceful shutdown on termination
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
    if not start_healthcheck():
        exit(1)
    while True:
        ping_and_sleep()

if __name__ == "__main__":
    main()
