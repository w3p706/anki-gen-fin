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
from model import LearningItem, SkipList, Analysis, Explanation  # Adjust the import path as necessary
import db
from progress_log import ProgressLog




logger = logging.getLogger(__name__)

instructions = """Der Finnish Language Expert analysiert finnische Wörter auf Deutsch und liefert das Ergebnis in einem spezifischen JSON-Format zurück. Als Input erhält er ein Wort, mögliche Begriffsklärungen mit Fallanalyse und ein Satz als Kontext. Für jedes analysierte Wort gibt er eine strukturierte JSON-Antwort zurück, die folgendes enthält:
- 'word' (das gegebene Wort), 
- 'lemma' (die Grundform des Wortes), 
- 'suffixes' (eine Liste mit Tupeln aus der im Wort verwendeten Endungen sowie deren Fälle und Bedeutung), 
- 'meaning' (die Bedeutung des Wortes auf Deutsch) 
- 'explanation' (Erkläre kurz und knapp aus welchen Teilen das Wortes besteht, und erläutere die einzenen Bestandteile. Wenn es im Nominativ ist musst du das nicht erklären. Sonst erläutere wieso in diesem Satz dieser Fall benötigt wird. Liefere hier auch spezielle Hinweise zur Verwendung dieses Wortes wenn es welche gibt. ) 
- 'sample' (Beispielsatz mit dem analysierten Wort in Finnish und Deutsch. Nicht der im Kontext übermittelte Satz.)

Dieses Format sorgt für eine klare und systematische Darstellung der linguistischen Analyse. Der Expert bleibt sachlich und direkt, mit einem neutralen Ton.

Beispiel:

{
  "word": "elokuvassaan",
  "lemma": "elokuva",
  "suffixes": [
    {"-ssa": "inessiv; innerhalb von, in etwas drin"},
    {"-an": "3. Person Singular possessivsuffix; sein/ihr"}
  ],
  "meaning": "in seinem/ihrem Film",
  "explanation": "Das finnische Wort 'elokuva' bedeutet 'Film' oder 'Kino' auf Deutsch. Es setzt sich aus zwei Teilen zusammen: „elo“ und „kuva“.\n'Elo': Dieser Teil des Wortes stammt von „elämä“, was „Leben“ bedeutet. Es bezieht sich auf etwas Lebendiges oder Dynamisches.\n'Kuva': Dieser Teil bedeutet 'Bild' oder 'Abbildung'.", 
  "sample": {
    "finnisch": "Ohjaaja esitteli uusia teemoja elokuvassaan.",
    "deutsch": "Der Regisseur stellte neue Themen in seinem Film vor."
  }
}"""


headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ.get("OPENAI_API_KEY")}"
}

    


def get_query(learning_item):
    return f'{learning_item.native_text} {learning_item.translation}'




@retry(wait=wait_random_exponential(min=1, max=60), 
       stop=stop_after_attempt(20), 
       before_sleep=before_sleep_log(logger, logging.INFO), 
       retry_error_callback=lambda _: None)
async def get_completion(word_data_with_context, session, semaphore, progress_log):

    word_data_with_context_str = str(word_data_with_context)
    async with semaphore:

        async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json={
            "model": "gpt-4-turbo-preview",
            "messages": [
              {
                "role": "system",
                "content": instructions,
              },
              {
                "role": "user",
                "content": word_data_with_context_str,
              }
            ],
            "response_format" : {"type": "json_object"}
        }) as resp:

            response_json = await resp.json()

            return response_json["choices"][0]['message']["content"]


async def process_row(learning_item, session, semaphore, progress_log):

    order = 0

    analysis = Analysis.filter(learning_item=learning_item)    

    distinct_indexes = await analysis.distinct().values_list("index", flat=True)

    for index in distinct_indexes:

        if (await Explanation.filter(learning_item=learning_item, index=index).exists()):
            continue
        
        analysis_by_index = await analysis.filter(index=index)
        word = analysis_by_index[0].word

        if (await SkipList.filter(word=word).exists()):
            continue

        word_data_with_context = {
            "sentence": learning_item.native_text,
            "word": word,
            "disambiguations": []
        }

        for word_analysis in analysis_by_index:

            word_data_with_context["disambiguations"].append({
                "lemma": word_analysis.lemma,
                #"weight": word_analysis.analysis_detail["weight"],
                "analysis_label": word_analysis.analysis_detail["analysis_label"],
                "labels": word_analysis.analysis_detail["labels"],
                "language": word_analysis.analysis_detail["language"]
            })


        logger.info(f'Explaining {word}')
        progress_log.total += 1
        explanation = await get_completion(word_data_with_context, session, semaphore, progress_log)

        json_explanation = json.loads(explanation)

        explained = Explanation(
            word=word.lower(), 
            lemma=json_explanation["lemma"],
            explanation_detail=explanation, 
            learning_item=learning_item, 
            index=index)    
        
        await explained.save()

        progress_log.increment()
        logger.info(progress_log)



async def run_explain(max_parallel_calls, timeout):
    
    await db.init() 

    items_without_explanation = await LearningItem.annotate(
        explanation_count=Count('explanation')
    ).filter(explanation_count=0).limit(5)

    semaphore = asyncio.Semaphore(value=max_parallel_calls)
    progress_log = ProgressLog(0)

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(timeout)) as session:
        tasks = [process_row(item, session, semaphore, progress_log) for item in items_without_explanation]
        await asyncio.gather(*tasks)


run_async(run_explain(5, 60))