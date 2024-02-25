import logging
import sys

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s')

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(formatter)

# file_handler = logging.FileHandler('media/logs/process.log')
# file_handler.setLevel(logging.DEBUG)
# file_handler.setFormatter(formatter)

# logger.addHandler(file_handler)
logger.addHandler(stdout_handler)
