import os
import logging
import logger
import json
import jsonschema
from jsonschema import validate
from jsonschema.exceptions import ValidationError
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
from .config import *
from string import Template


logger = logging.getLogger(__name__)


headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ.get("OPENAI_API_KEY")}"
}


def load_json_schema():
    """
    Load the JSON Schema from a file.
    """
    with open(Config.get().explain.gpt_options.schema_file_path, 'r') as file:
        schema = json.load(file)
    return schema

# Inpired by https://towardsdatascience.com/the-proper-way-to-make-calls-to-chatgpt-api-52e635bea8ff
@retry(wait=wait_random_exponential(min=1, max=60), 
    stop=stop_after_attempt(Config.get().explain.gpt_options.max_retries), 
    before_sleep=before_sleep_log(logger, logging.INFO), 
    retry_error_callback=lambda _: None)
async def get_completion(word_data_with_context, session, semaphore, schema):

    word_data_with_context_str = str(word_data_with_context)
    async with semaphore:

        gpt_options = Config.get().explain.gpt_options

        template_data = {
            'target_language_fullname': Config.get().target_language.fullname,
            'translated_language_fullname': Config.get().translated_language.fullname,
            'word_data_with_context_str': word_data_with_context_str,
        }

        messages = []
        for message in gpt_options.prompt:
            # @TODO: This could be done so that the prompt is rendered as template only once and not each time.
            if isinstance(message, SystemMessage):
                messages.append({'role':"system", 'content': Template(message.system).safe_substitute(template_data)})
            elif isinstance(message, AssistantMessage):
                messages.append({'role':"assistant", 'content': Template(message.assistant).safe_substitute(template_data)})
            elif isinstance(message, UserMessage):
                messages.append({'role':"user", 'content': Template(message.user).safe_substitute(template_data)})



        async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json={
            "model": gpt_options.model,
            "messages": messages,
            "response_format" : {"type": "json_object"}      
        }) as resp:

            if resp.status != 200:
                logger.error(f"Error: {resp.status}: {resp.text}")
                return 

            response_json = await resp.json()
            json_fragment_of_intrest = json.loads(response_json["choices"][0]['message']["content"])

            # we need to validate the response to detect brainwaves or fantasy of the AI
            validate(instance=json_fragment_of_intrest, schema=schema)

            return json_fragment_of_intrest


async def process_row(learning_item, session, semaphore, progress_log, schema):

    analysis = Analysis.filter(learning_item=learning_item)    

    distinct_indexes = await analysis.distinct().values_list("index", flat=True)

    for index in distinct_indexes:

        if (await Explanation.filter(learning_item=learning_item, index=index).exists()):
            continue
        
        analysis_by_index = await analysis.filter(index=index)
        word = analysis_by_index[0].word

        skiplist = await SkipList.get_or_none(word=word.lower())
        if (skiplist is not None):
            logger.info(f'Skipping \'{word}\' for \'{learning_item.native_text}\' ({learning_item.learning_item_id}) because it\'s on the skip list.')
            continue

        word_data_with_context = {
            "sentence": learning_item.native_text,
            "word": word,
            "etymology": "",
            "disambiguations": []
        }

        lemma = ""

        for word_analysis in analysis_by_index:

            if (lemma == ""):
                lemma = word_analysis.lemma

            word_data_with_context["disambiguations"].append({
                "lemma": word_analysis.lemma,
                #"weight": word_analysis.analysis_detail["weight"],
                "analysis_label": word_analysis.analysis_detail["analysis_label"],
                "labels": word_analysis.analysis_detail["labels"],
                "language": word_analysis.analysis_detail["language"]
            })


        entry = await Etymology.get_or_none(word=lemma)
        if (entry is not None):
            # only add if it not contains 'proto-finnic' these are not helpful
            if entry.description.lower().find('proto-finnic') == -1:
                word_data_with_context["etymology"] = entry.description
                
        

        logger.info(f'Explaining {word}')
        logger.debug(word_data_with_context)
        progress_log.total += 1
        explanation = await get_completion(word_data_with_context, session, semaphore, schema)

        explained = Explanation(
            word=word.lower(), 
            lemma=explanation["lemma"],
            explanation_detail=explanation, 
            learning_item=learning_item, 
            index=index)    
        
        await explained.save()

        progress_log.increment()
        logger.info(progress_log)



async def explain(deck, overwrite=False, all=False):
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

    items = await LearningItem.filter(lesson=lesson).annotate(
        explanation_count=Count('explanation')
    ).filter(explanation_count=0)

    schema = load_json_schema()

    semaphore = asyncio.Semaphore(value=Config.get().explain.gpt_options.max_parallel_calls)
    progress_log = ProgressLog(0)

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(Config.get().explain.gpt_options.timeout)) as session:
        tasks = [process_row(item, session, semaphore, progress_log, schema) for item in items]
        await asyncio.gather(*tasks)



