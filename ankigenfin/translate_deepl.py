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


async def translate_deepl(lession_list, max_parallel_calls=5, timeout=60):
    
    await db_init() 

    lessons = await Lesson.filter(folder__in=lession_list).all()
    if (not (lessons is None or len(lessons) == 0)):
        lession_list = [lesson.lesson_id for lesson in lessons]  

    logger.info(f"Creating Deepl translations for lessions {lession_list}")

    deepl_key = os.environ.get("DEEPL_API_KEY")
    deepl_url = os.environ.get("DEEPL_URL")
    translator = deepl.Translator(deepl_key, server_url=deepl_url).set_app_info("ankigenfin", "0.1")

    items = await LearningItem.filter(lesson_id__in=lession_list).filter(translation_machine=None)

    if (len(items) == 0):
        logger.info(f'Lessions "{lession_list}" have no pending items')
        return
    
    native_texts = [item.native_text for item in items]

    result = translator.translate_text(native_texts, source_lang="FI", target_lang="DE")

    logger.info(f"Translated '{len(result)}'/'{len(native_texts)}' items") 

    for i, translation in enumerate(result):
        items[i].translation_machine = translation.text        
        await items[i].save()

    semaphore = asyncio.Semaphore(value=max_parallel_calls)
    progress_log = ProgressLog(0)



