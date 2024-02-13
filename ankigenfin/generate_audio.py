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


logger = logging.getLogger(__name__)

# https://elevenlabs.io/
# see voices_eleven_labs.json or https://api.elevenlabs.io/v1/voices
# https://api.elevenlabs.io/v1/text-to-speech/XrExE9yKIg1WjnnlVkGX/stream?
# {"text":"Kissat ovat kaivanneet sinua.","model_id":"eleven_multilingual_v2"}

CHUNK_SIZE = 1024

voice_ids = [
        # ["z9fAnlkpzviPz146aGWa", "Glinda"], 
        ["piTKgcLEGmPE4e6mEKli", "Nicole"], 
        ["XrExE9yKIg1WjnnlVkGX", "Matilda"], 
        ["XB0fDUnXU5powFXDhCwa", "Charlotte"],
        ["AZnzlk1XvdvUeBnXmlld", "Domi"],
        ["EXAVITQu4vr4xnSDxMaL", "Sarah"],
        ["pFZP5JQG7iQjIQuC4Bku", "Lily"],
    ]


headers = {
  "Accept": "audio/mpeg",
  "Content-Type": "application/json",
  "xi-api-key": f"{os.environ.get("ELEVEN_LABS_API_KEY")}"
}

# response = requests.post(url, json=payload, headers=headers)

# if response.status_code != 200:
#     print(f"Error: {response.status_code}")
#     print(response.text)
#     exit()

# with open('media/output.mp3', 'wb') as f:
#     for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
#         if chunk:
#             f.write(chunk)


@retry(wait=wait_random_exponential(min=1, max=60), 
       stop=stop_after_attempt(20), 
       before_sleep=before_sleep_log(logger, logging.INFO), 
       retry_error_callback=lambda _: None)
async def get_audio(item, session, semaphore, progress_log):

    async with semaphore:

        voice_id = random.choice(voice_ids)

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id[0]}"

        async with session.post(url, headers=headers, json={
              "model_id": "eleven_multilingual_v2",
              "text": item.native_text,
              "voice_settings": {
                "use_speaker_boost": True,
                "style": 0,
                "stability": 0.5,
                "similarity_boost": 1.0,
              }
        }) as resp:

            if resp.status != 200:
                logger.error(f"Error: {resp.status}: {resp.reason} - {await resp.text()}")

            id = uuid.uuid4()
            subfolder = str(id)[0]

            # Create subfolder if it doesn't exist
            subfolder_path = os.path.join("media", subfolder)
            os.makedirs(subfolder_path, exist_ok=True)

            filename = os.path.join(subfolder_path, f"{id}.mp3")

            with open(filename, 'wb') as fd:
                async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                    if chunk:
                        fd.write(chunk)

            logger.info(f"Saved {filename} with text '{item.native_text}' and voice '{voice_id[1]}'")
            item.audio_file_name = filename
            await item.save()

            progress_log.increment()
            logger.info(progress_log)


async def generate_audio(deck, overwrite=False, all=False, max_parallel_calls = 2, timeout= 60):
    
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

    items = await LearningItem.filter(lesson=lesson).filter(audio_file_name=None)

    semaphore = asyncio.Semaphore(value=max_parallel_calls)
    progress_log = ProgressLog(len(items))

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(timeout)) as session:
        tasks = [get_audio(item, session, semaphore, progress_log) for item in items]
        await asyncio.gather(*tasks)

         