import logging
import coloredlogs

coloredlogs.install()
# logging.basicConfig(format='%(asctime)s %(lineno)d %(levelname)s:%(message)s', level=logging.DEBUG)
logging.basicConfig(format='%(levelname)-8s %(asctime)s [%(filename)s:%(lineno)d] %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# logger = logging.getLogger(__name__)
# handler = logging.StreamHandler()
# handler.setFormatter(logging.Formatter('%(levelname)-8s %(asctime)s [%(filename)s:%(lineno)d] %(message)s'))
# # logger.setLevel(config['logger']['level'].upper())
# logger.addHandler(handler)