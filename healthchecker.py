#!/usr/bin/env python3

import logging
import time
import requests
import threading
import signal
import json

class HealthChecker:
    '''
    HealthChecker is a class that periodically sends pings to Healthchecks.io to indicate that the server is alive.
    '''
    def __init__(self, hc_uuid:str, req_timeout:float, sleep_time:int) -> None:
        '''
        Initialize the HealthChecker with the specified parameters.
        Args:
            hc_uuid (str): The UUID for Healthchecks.io.
            req_timeout (float): The HTTP request timeout in minutes.
            sleep_time (int): The time to sleep between pings in seconds.
        '''
        self.hc_uuid:str = hc_uuid
        ''' UUID for Healthchecks.io'''
        self.req_timeout:float = req_timeout
        ''' HTTP request timeout in seconds'''
        self.sleep_time:int = sleep_time
        ''' Time to sleep between pings in seconds'''
        self.ping_number:int = 0
        ''' Number of pings sent to Healthchecks.io from the start'''
        self.ping_number_lock:threading.Lock = threading.Lock()
        ''' Lock to ensure thread-safe increment of the ping counter'''
        self.health_time:time.struct_time = None
        ''' Time of first successful ping of the strike'''
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    @staticmethod
    def set_logging() -> None:
        '''
        Configure logging settings for the healthcheck script.
        '''
        logging.basicConfig(level=logging.INFO)

    def sec_to_human_readable(seconds:int) -> str:
        '''
        Convert a time duration from seconds to a human-readable format.
        Args:
            seconds (int): The time duration in seconds.
        Returns:
            str: Time duration formatted as "Ad Bh Cm Ds".
        '''
        years, remainder = divmod(seconds, 31536000)
        days, remainder = divmod(remainder, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = []
        if years:
            parts.append(f"{years}y")
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds or not parts:
            parts.append(f"{seconds}s")
        # Join the parts into a single string
        return " ".join(parts)

    @staticmethod
    def get_uptime() -> str:
        '''
        Get the system uptime in a human-readable format.
        Returns:
            str: Uptime formatted as "Ad Bh Cm Ds".
        '''
        try:
            # Read the uptime from /proc/uptime
            with open("/proc/uptime", "r", encoding="utf-8") as uptime_file:
                uptime_seconds = int(float(uptime_file.readline().split()[0]))
        except (OSError, ValueError, IndexError):
            logging.error("Unable to read system uptime.")
            return "0s"
        return HealthChecker.sec_to_human_readable(uptime_seconds)

    def get_time(self, sys_time:time.struct_time) -> str:
        '''
        Get the current system time in a human-readable format.
        Returns:
            str: Current time formatted as "YYYY-MM-DD HH:MM:SS".
        '''
        return time.strftime("%Y-%m-%d %H:%M:%S", sys_time)

    def get_ping_number(self) -> int:
        '''
        Get the current ping number.
        Returns:
            int: The number of pings sent to Healthchecks.io.
        '''
        # Use a lock to ensure thread-safe increment of the ping counter
        with self.ping_number_lock:
            current_ping:int = self.ping_number
            self.ping_number += 1
            return current_ping
        
    def get_health_time(self, sys_time:time.struct_time) -> str:
        '''
        Get the time of the first successful ping of the strike in a human-readable format.
        Returns:
            str: Time of the first successful ping formatted as "YYYY-MM-DD HH:MM:SS" or "0s" if no successful ping has been made.
        '''
        if self.health_time:
            time_diff_sec:int = int(time.mktime(sys_time) - time.mktime(self.health_time))
            return HealthChecker.sec_to_human_readable(time_diff_sec)
        else:
            return "0s"

    def make_payload(self, status:str) -> json:
        '''
        Create a payload for the healthcheck request containing uptime and current time.
        Args:
            status (str): The status of the ping, can be "ping", "start", or "stop".
        Returns:
            dict: Payload with "uptime" and "timestamp" keys.
        '''
        # Update the system time before creating the payload to ensure it reflects the current time
        current_time = time.localtime()
        payload:json = {
            "status": status,
            "ping_number": self.get_ping_number(),
            "timestamp": self.get_time(current_time),
            "uptime": HealthChecker.get_uptime(),
            "health_time": self.get_health_time(current_time)
        }
        return payload

    def ping_healthcheck(self, signal:str=None, mode:str="ping") -> bool:
        '''
        Send a ping to the Healthchecks.io endpoint with the specified mode.
        Args:
            signal (str, optional): The signal to send. Defaults to None.
            mode (str): The mode of the ping, can be "ping", "start", or "stop".
        Returns:
            bool: True if the ping was successful (HTTP 200), False otherwise.
        '''
        extra_info:dict = {}
        ''' Extra information to include in the log messages'''
        url:str = "https://hc-ping.com/%s" % (self.hc_uuid)
        ''' URL for the Healthchecks.io ping endpoint'''
        # If the mode is not "ping", append the mode to the URL
        if signal is not None:
            url += "/%s" % signal
        req:json = {"url": url, "timeout": self.req_timeout, "payload": self.make_payload(status=mode)}
        extra_info.update({"request": req})
        try:
            response:requests.Response = requests.post(
                url=req["url"],
                timeout=req["timeout"],
                json=req["payload"]
                )
            extra_info.update({"response": {"status_code": response.status_code, "text": response.text}})
            if response.status_code == 200:
                logging.info(f"Sending \'{mode}\' was successful: {response.text}", extra=extra_info)
                if self.health_time is None:
                    self.health_time = time.localtime()
                return True
            else:
                self.health_time = None
                logging.warning(
                    f"Sending \'{mode}\' failed with status code {response.status_code}: {response.text}",
                    extra=extra_info
                    )
                return False
        except requests.RequestException as e:
            self.health_time = None
            extra_info.update({"error": str(e)})
            logging.warning(f"Sending \'{mode}\' failed: {e}", extra=extra_info)
            return False
        
    def start_healthcheck(self) -> bool:
        '''
        Start the healthcheck by sending a "start" ping to Healthchecks.io.
        Returns:
            bool: True if the start ping was successful, False otherwise.'''
        return self.ping_healthcheck(signal="start", mode="start")

    def stop_healthcheck(self) -> bool:
        '''
        Stop the healthcheck by sending a "stop" ping to Healthchecks.io.
        Returns:
            bool: True if the stop ping was successful, False otherwise.
        '''
        return self.ping_healthcheck(signal="fail", mode="stop")

    def ping_and_sleep(self) -> None:
        '''
        Send a ping to Healthchecks.io and then sleep for the configured amount of time.
        If the ping is successful, sleep for the full configured time. If the ping fails, sleep for half the configured time before trying again.
        '''
        st:int = self.sleep_time
        ''' Time to sleep in seconds'''
        if self.ping_healthcheck():
            logging.info("Ping successful. Sleeping for %d minutes." % (st/60))
        else:
            st = self.sleep_time/2
            logging.warning("Ping failed. Sleeping for %d minutes." % (st/60))
        try:
            # Sleep for the configured amount of time, but allow interruption by signals
            time.sleep(st)
        except Exception as e:
            logging.error("Sleep interrupted: %s" % e)

    def graceful_exit(self) -> bool:
        '''
        Perform a graceful shutdown by sending a "stop" ping to Healthchecks.io and logging the shutdown process.
        
        Returns:
            bool: True if the healthcheck was stopped successfully, False otherwise.
        '''
        logging.info("Shutting down gracefully...")
        try:
            if self.stop_healthcheck():
                logging.info("Healthcheck stopped successfully.")
                exit(0)
            else:
                logging.error("Failed to gracefully stop healthcheck.")
                exit(1)
        except Exception as e:
            logging.error(f"Error during graceful shutdown: {e}")
            exit(1)

    def _signal_handler(self, signum, frame) -> None:
        '''
        Handle termination signals (SIGTERM and SIGINT) to ensure a graceful shutdown of the healthcheck script.
        When a termination signal is received, this handler will log the signal,
        attempt to perform a graceful exit by sending a "stop" ping to Healthchecks.io,
        and then exit the program with an appropriate status code based on the success of the graceful exit.
        Args:
            signum: The signal number received.
            frame: The current stack frame.
        '''
        logging.info("Received signal %s, frame: %s", signum, frame)
        self.graceful_exit()

    def run_pings(self) -> None:
        '''
        Run the healthcheck loop, which continuously sends pings to Healthchecks.io and sleeps for the configured amount of time.
        The loop will continue until a termination signal is received, at which point it will attempt to perform a graceful shutdown.
        '''
        HealthChecker.set_logging()
        # Start the healthcheck by sending a "start" ping
        if not self.start_healthcheck():
            logging.error("Start ping failed.")
            exit(1)
        # Enter the main loop to send pings and sleep
        while True:
            self.ping_and_sleep()
