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
from .db import db_init, LearningItem, Lesson  # Adjust the import path as necessary
from .progress_log import ProgressLog
import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from .config import *
from string import Template


logger = logging.getLogger(__name__)



## This translates all words of a deck with the GPT
config : MachineTranslation = None


headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ.get("OPENAI_API_KEY")}"
}


@retry(wait=wait_random_exponential(min=1, max=60), 
       stop=stop_after_attempt(20), 
       before_sleep=before_sleep_log(logger, logging.INFO), 
       retry_error_callback=lambda _: None)
async def get_completion(item, context, session, semaphore, progress_log):

    # Umwandlung der Liste in einen JSON-String
    json_string = json.dumps(item, ensure_ascii=False)

    async with semaphore:

        daten = {
            'source_language_fullname': config.source_language_fullname,
            'target_language_fullname': config.target_language_fullname,
            'context': context,
            'json_string': json_string
        }

        messages = []
        for message in config.prompt:
            # @TODO: This could be done so that the prompt is rendered as template only once and not each time.
            if isinstance(message, SystemMessage):
                messages.append({'role':"system", 'content': Template(message.system).safe_substitute(daten)})
            elif isinstance(message, AssistantMessage):
                messages.append({'role':"assistant", 'content': Template(message.assistant).safe_substitute(daten)})
            elif isinstance(message, UserMessage):
                messages.append({'role':"user", 'content': Template(message.user).safe_substitute(daten)})


        async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json={
            "model": config.model,
            "messages": messages,
            "response_format" : {"type": "json_object"}
            
        }) as resp:

            if resp.status != 200:
                logger.error(f"Error: {resp.status}: {resp.text}")
                return 

            response_json = await resp.json()
            translated_item = json.loads(response_json["choices"][0]['message']["content"])

        
            # Versuche, das LearningItem mit der gegebenen ID zu finden
            learning_item = await LearningItem.get_or_none(learning_item_id=translated_item['key'])
            
            if learning_item:
                # Wenn ein LearningItem gefunden wurde, füge die Übersetzung hinzu
                learning_item.translation_machine = translated_item['text']  # Annahme: 'text' enthält die Übersetzung
                logger.info(f"Translated '{translated_item['key']}' to '{translated_item['text']}'")
                await learning_item.save()

            else:
                logger.warn(f"LearningItem mit der ID {translated_item['key']} wurde nicht gefunden.")

            progress_log.increment()
            logger.info(progress_log)


def chunk_list(lst, chunk_size):
    """Yield successive chunk_size chunks from lst."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


async def translate_gpt(mainConfig : MainConfig, deck, overwrite=False, all=False, max_parallel_calls=5, timeout=120):

    global config
    config = mainConfig.machine_translation
    
    await db_init() 

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

    items_list = [
        {"key": item.learning_item_id, "text": item.native_text}
        for item in items
    ]

    context = "\n".join([item["text"] for item in items_list[:100]])

    semaphore = asyncio.Semaphore(value=max_parallel_calls)
    progress_log = ProgressLog(len(items_list))

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(timeout)) as session:
        tasks = [get_completion(item, context, session, semaphore, progress_log) for item in items_list]
        await asyncio.gather(*tasks)







