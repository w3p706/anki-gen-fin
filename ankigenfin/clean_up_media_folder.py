import requests
import os
import logging
import logger
import json
import asyncio
import aiohttp
from tenacity import (
    retry,
    before_sleep_log,
    stop_after_attempt,
    wait_random_exponential,
)
from tortoise import run_async
from tortoise.functions import Count
from .db import db_init, LearningItem, Lesson  # Adjust the import path as necessary
from .progress_log import ProgressLog
import random    
import uuid
from .config import *

logger = logging.getLogger(__name__)


async def clean_up_media_folder():
    await db_init() 

    items = await LearningItem.all()

    for item in items:
        if (item.audio_file_name is None or item.audio_file_name == ""):
            continue

        if ('media/' in item.audio_file_name):
            item.audio_file_name = os.path.basename(item.audio_file_name)
            await item.save()


        subfolder = str(item.audio_file_name)[0]
        subfolder_path = os.path.join(Config.get().audio_generation.output_folder, subfolder)

        filename = os.path.join(subfolder_path, item.audio_file_name)

        if not os.path.exists(filename):
            item.audio_file_name = None
            await item.save()
            logger.warning(f"Audio file '{filename}' for item {item.learning_item_id} does not exist; Audio set to None.")
        elif os.path.getsize(filename) == 0:
            item.audio_file_name = None
            await item.save()
            os.remove(filename)
            logger.warning(f"Audio file '{filename}' for item {item.learning_item_id} is empty; Audio set to None. File removed")
            



         