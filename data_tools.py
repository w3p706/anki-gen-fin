import ankigenfin
from tortoise import run_async
import logging
import logger

logger = logging.getLogger(__name__)

# run_async(ankigenfin.check_and_migrate_explanations())
run_async(ankigenfin.compute_statistics())