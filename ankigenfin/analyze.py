﻿from uralicNLP import uralicApi
from uralicNLP import tokenizer
from uralicNLP.cg3 import Cg3
from tortoise import run_async
from tortoise.functions import Count
from tortoise.expressions import Q
import csv
import logging
from .db import db_init, Lesson, LearningItem, Analysis, AnalysisLabel 
import logger
from .config import *

logger = logging.getLogger(__name__)

cg = None

async def process_morphology(arr):
    labels = []
    weight = 0
    analysis_label = ""
    language = ""
    for item in arr:
        if item.startswith('<W'):
            # Convert '<W:0.000000>' to a float value
            weight = float(item.strip('<W:').rstrip('>'))
        elif item.startswith('<'):
            # Lookup in the language dictionary
            key = item.strip('<>')  # Remove '<', '>'
            if key in Config.get().analyze:
                language = Config.get().analyze[key]
            else:
                language = key
                logger.warn(f"Warning: '{item}' not found in language dictionary.")
        elif item.startswith('@'):
            label = await AnalysisLabel.filter(label__iexact=item).first()
            if label:
                analysis_label = label.description
            else:
                logger.warn(f"Warning: analytics label not found: '{item}'")
        else:
            label = await AnalysisLabel.filter(label__iexact=item).first()
            if label:
                labels.append(label.description)
            else:
                logger.warn(f"Warning: analytics label not found: '{item}'")


    return weight, analysis_label, labels, language


async def disambiguate_sentence(leaning_item):

    tokens = tokenizer.words(leaning_item.native_text)
    leaning_item.tokenized = tokens
    await leaning_item.save()

    disambiguations = cg.disambiguate(tokens)
    for word, disambiguation in disambiguations:

        for possible_word in disambiguation:
            if (possible_word.morphology[0] == 'Punct'):
                continue

            weight, analysis_label, labels, language = await process_morphology(possible_word.morphology)

            word_analysis = {
                "lemma": possible_word.lemma,
                "morphology": possible_word.morphology,
                "weight": weight,
                "analysis_label": analysis_label,
                "labels": labels,
                "language": language
            }

            analysis = '+'.join([item for item in word_analysis['morphology'] if not item.startswith('<')])


            try:
                token_index = tokens.index(word)
            except ValueError:                
                logger.warn(f"Exess word from disambiguation. Word: {word}, Tokens: {tokens}, Native Text: {leaning_item.native_text}, Disambiguation: {disambiguations}")
                continue  

            await Analysis.create(
                    index=token_index,
                    word=word, 
                    lemma=possible_word.lemma, 
                    analysis = possible_word.lemma + '+' + analysis,
                    analysis_detail=word_analysis,
                    learning_item_id = leaning_item.learning_item_id
                )


async def analyze(lession_list):
    global cg
    cg = Cg3(Config.get().target_language.cg_language_name)
    
    await db_init() 

    lessons = await Lesson.filter(folder__in=lession_list).all()
    if (not (lessons is None or len(lessons) == 0)):
        lession_list = [lesson.lesson_id for lesson in lessons]   
    
    logger.info(f"Analyze words for lessions {lession_list}")
    items = await LearningItem.filter(lesson_id__in=lession_list).annotate(
        analysis_count=Count('analysis')
    ).filter(analysis_count=0)

    if (len(items) == 0):
        logger.info(f'Lessions "{lession_list}" have no pending items')
        return

    analysis_count = 0
    for item in items:
        await disambiguate_sentence(item)

        analysis_count += 1
        logger.info(f'Analysis for {analysis_count}/{len(items)} saved to database')

    # Log the analysis count
    logger.info(f'Total number of analyses performed: {analysis_count}')

