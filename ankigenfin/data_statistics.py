from tortoise import Tortoise, run_async
from tortoise.functions import Count
from .db import db_init, Lesson, LearningItem, Analysis, Explanation  # Adjust the import according to your project structure
import json
import jsonschema
from jsonschema import validate
import copy
import logging
import logger
import string

logger = logging.getLogger(__name__)


schema_file_path = "ankigenfin/gpt-out.schema.json"


async def compute_statistics():
    await db_init()
    lessons = await Lesson.all().prefetch_related('learning_items')
    total_lessons = await Lesson.all().count()
    print(f"Number of Lessons: {total_lessons}")

    for lesson in lessons:
        learning_items_count = await lesson.learning_items.all().count()
        print(f"Lesson '{lesson.name}' has {learning_items_count} learning items.")

        total_token_count = 0
        analyzed_words_count = 0
        explained_words_count = 0
        for item in lesson.learning_items:
            # Remove punctuations from item.tokenized
            filtered_tokenized = [token for token in item.tokenized if token not in string.punctuation]
            total_token_count += len(filtered_tokenized)
            analyzed_count = await Analysis.filter(learning_item_id=item.learning_item_id).count()
            explained_count = await Explanation.filter(learning_item_id=item.learning_item_id).count()
            analyzed_words_count += analyzed_count
            explained_words_count += explained_count

        percent_analyzed = (analyzed_words_count / total_token_count * 100) if learning_items_count else 0
        percent_explained = (explained_words_count / total_token_count * 100) if learning_items_count else 0

        print(f"Lesson '{lesson.name}': {percent_analyzed:.2f}% of words analyzed, {percent_explained:.2f}% of words explained.")








