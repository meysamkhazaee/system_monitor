import logging
import colorlog

# Create a logger object
logger = logging.getLogger(__name__)

# Define a log format for colorlog
log_format = (
    '%(log_color)s%(levelname)-8s%(reset)s %(asctime)s [%(filename)s:%(lineno)d] %(message)s'
)

# Create a colorlog formatter using the log format
formatter = colorlog.ColoredFormatter(
    log_format,
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'bold_red',
    }
)

# Create a stream handler
handler = logging.StreamHandler()

# Set the formatter for the handler
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

# Set the logging level (default to DEBUG, but can be changed)
logger.setLevel(logging.DEBUG)