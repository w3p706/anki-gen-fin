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

# https://elevenlabs.io/
# see voices_eleven_labs.json or https://api.elevenlabs.io/v1/voices
# https://api.elevenlabs.io/v1/text-to-speech/XrExE9yKIg1WjnnlVkGX/stream?
# {"text":"Kissat ovat kaivanneet sinua.","model_id":"eleven_multilingual_v2"}


CHUNK_SIZE = 1024


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
       stop=stop_after_attempt(Config.get().audio_generation.max_retries), 
       before_sleep=before_sleep_log(logger, logging.INFO), 
       retry_error_callback=lambda _: None)
async def get_audio(item, session, semaphore, progress_log):

    async with semaphore:

        voice = random.choice(Config.get().audio_generation.voices)

        text = item.native_text
        if len(text.split()) == 1:
            text = "sana on: " + text

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice.id}"

        async with session.post(url, headers=headers, json={
              "model_id": Config.get().audio_generation.model,
              "text": text,
              "voice_settings": {
                "use_speaker_boost": voice.use_speaker_boost,
                "style": voice.style,
                "stability": voice.stability,
                "similarity_boost": voice.similarity_boost,
              }
        }) as resp:

            if resp.status != 200:
                logger.error(f"Error: {resp.status}: {resp.reason} - {await resp.text()}")
                return

            id = uuid.uuid4()
            subfolder = str(id)[0]

            # Create subfolder if it doesn't exist
            subfolder_path = os.path.join(Config.get().audio_generation.output_folder, subfolder)
            os.makedirs(subfolder_path, exist_ok=True)

            filename = os.path.join(subfolder_path, f"{id}.mp3")


            with open(filename, 'wb') as fd:
                async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                    if chunk:
                        fd.write(chunk)

            # Check if file size is 0, if so delete it
            if os.path.getsize(filename) == 0:
                os.remove(filename)
                logger.info(f"Deleted {filename} because it was empty")
            else:
                logger.info(f"Saved {filename} with text '{item.native_text}' and voice '{voice.name}'")
                item.audio_file_name = f"{id}.mp3"
                await item.save()

            progress_log.increment()
            logger.info(progress_log)


async def generate_audio(lession_list):
    
    await db_init() 

    lessons = await Lesson.filter(folder__in=lession_list).all()
    if (not (lessons is None or len(lessons) == 0)):
        lession_list = [lesson.lesson_id for lesson in lessons]  

    logger.info(f"Generate audio for lessions {lession_list}")
    items = await LearningItem.filter(lesson_id__in=lession_list).filter(audio_file_name=None)
        
    if (len(items) == 0):
        logger.info(f'Lessions "{lession_list}" have no pending items')
        return

    semaphore = asyncio.Semaphore(value=Config.get().audio_generation.max_parallel_calls)
    progress_log = ProgressLog(len(items))

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(Config.get().audio_generation.timeout)) as session:
        tasks = [get_audio(item, session, semaphore, progress_log) for item in items]
        await asyncio.gather(*tasks)

         