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
import json

logger = logging.getLogger(__name__)



# Funktion zum Importieren der Daten aus einer JSON-Datei
async def import_data_from_json():
    with open('/workspaces/anki-gen-fin/test-translated.json', 'r') as file:
        data = json.load(file)
    
    for item in data:
        # Versuche, das LearningItem mit der gegebenen ID zu finden
        learning_item = await LearningItem.get_or_none(learning_item_id=item['key'])
        
        if learning_item:
            # Wenn ein LearningItem gefunden wurde, füge die Übersetzung hinzu
            learning_item.translation_machine = item['text']  # Annahme: 'text' enthält die Übersetzung
            await learning_item.save()
        else:
            print(f"LearningItem mit der ID {item['key']} wurde nicht gefunden.")



async def translate(deck, overwrite=False, all=False, max_parallel_calls=5, timeout=60):
    await db_init() 
    await import_data_from_json()





