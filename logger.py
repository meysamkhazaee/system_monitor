import logging
import os
import datetime
from termcolor import colored

class logger:
    def __init__(self, client_id="async_client", log_level=logging.INFO):
        """
        Initializes a logger instance.

        Args:
            log_file_path (str): The path to the log file.
            log_level (int, optional): The logging level (default: logging.INFO).
            format_string (str, optional): The format string for log messages (default: "%(asctime)s %(levelname)s %(message)s").
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S")

        # Get the absolute path of the current script (logger.py)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = f"logs/{client_id}"

        log_file_path = os.path.join(script_dir, log_dir)
        if not os.path.exists(log_file_path):
            os.makedirs(log_file_path)

        log_file_name = os.path.join(log_file_path, f"log_{date_str}_{time_str}.log")

        # File handler for saving logs to a file
        file_handler = logging.FileHandler(log_file_name, "w")
        file_handler.setLevel(log_level)

        # Create a formatter with the specified format string for file logs
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # Stream handler for color output to console (CMD)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)

        # Add the handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Log the client id on startup
        self.logger.critical(f"client id: {client_id}\n")

    def _colorize(self, level, message):
        """
        Colorizes log message based on log level.
        """
        if level == logging.DEBUG:
            return colored(message, 'blue')
        elif level == logging.INFO:
            return colored(message, 'green')
        elif level == logging.WARNING:
            return colored(message, 'yellow')
        elif level == logging.ERROR:
            return colored(message, 'red')
        elif level == logging.CRITICAL:
            return colored(message, 'magenta')
        return message

    def _log(self, level, message):
        """
        Custom log function to add color and write the log.
        """
        colored_message = self._colorize(level, message)
        if level == logging.DEBUG:
            self.logger.debug(colored_message)
        elif level == logging.INFO:
            self.logger.info(colored_message)
        elif level == logging.WARNING:
            self.logger.warning(colored_message)
        elif level == logging.ERROR:
            self.logger.error(colored_message)
        elif level == logging.CRITICAL:
            self.logger.critical(colored_message)

    def debug(self, message):
        """Logs a debug message."""
        self._log(logging.DEBUG, message)

    def info(self, message):
        """Logs an info message."""
        self._log(logging.INFO, message)

    def warning(self, message):
        """Logs a warning message."""
        self._log(logging.WARNING, message)

    def error(self, message):
        """Logs an error message."""
        self._log(logging.ERROR, message)

    def critical(self, message):
        """Logs a critical message."""
        self._log(logging.CRITICAL, message)
