import os
import logging
import logger
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
from .db import db_init, LearningItem, SkipList, Analysis, Explanation, Lesson, Etymology  # Adjust the import path as necessary
from .progress_log import ProgressLog
import deepl

logger = logging.getLogger(__name__)

# https://github.com/DeepLcom/deepl-python

async def translate(deck, overwrite=False, all=False, max_parallel_calls=5, timeout=60):
    await db_init() 

    deepl_key = os.environ.get("DEEPL_API_KEY")
    deepl_url = os.environ.get("DEEPL_URL")
    translator = deepl.Translator(deepl_key, server_url=deepl_url).set_app_info("ankigenfin", "0.1")

    items = None
    lesson = None

    if (isinstance(deck, (int))):
        lesson = await Lesson.get_or_none(lesson_id=deck)

    if (lesson is None):
        lesson = await Lesson.get_or_none(folder=deck)
        
    if (lesson is None):
        logger.error(f'Deck "{deck}" not found')
        return

    items = await LearningItem.filter(lesson=lesson).filter(translation_machine=None)

    native_texts = [item.native_text for item in items]

    result = translator.translate_text(native_texts, source_lang="FI", target_lang="DE")

    logger.info(f"Translated '{len(result)}'/'{len(native_texts)}' items") 

    for i, translation in enumerate(result):
        items[i].translation_machine = translation.text        
        await items[i].save()

    semaphore = asyncio.Semaphore(value=max_parallel_calls)
    progress_log = ProgressLog(0)



