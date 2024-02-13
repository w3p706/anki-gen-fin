import csv
from tortoise import run_async
from .db import db_init, Lesson, LearningItem  # Adjust the import path as necessary
import random
import logging
import logger

logger = logging.getLogger(__name__)

def get_or_generate_id():
    # Generate a new anki id and save it
    new_id = random.randrange(1 << 30, 1 << 31)
    return new_id

async def import_csv_to_db(csv_file_path):
    logger.info(f'Import {csv_file_path}')    

    lessons = []
    rows_imported = {}
    total_rows = 0

    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        # check for the correct columns
        required_columns = ['deck', 'Finnish', 'English', 'sides']
        if not all(column in reader.fieldnames for column in required_columns):            
            raise ValueError("Missing required columns in the CSV file.")

        for row in reader:

            if ("::" not in row['deck']):
                lesson_name = row['deck']
            else:
                lesson_info = row['deck'].split('::')
                lesson_name = lesson_info[-1] if len(lesson_info) > 1 else None

            # Create or get Lesson
            lesson, created = await Lesson.get_or_create(
                folder=row['deck'],
                defaults={
                    'lesson_id': get_or_generate_id(),
                    'name': lesson_name, 
                    'order': 0
                }  
            )

            if (not lesson.folder in rows_imported):
                rows_imported[lesson.folder] = 0
                lessons.append(lesson)

            is_double_sided = True if row['sides'] == 'Double' else False

            logger.debug(f'Importing {row["Finnish"]} - {row["English"]} to lesson {lesson.lesson_id}')

            # Create LearningItem in db
            entry, changed = await LearningItem.update_or_create(
                lesson=lesson,
                native_text=row['Finnish'],
                defaults=  {
                    'translation':row['English'],
                    'is_default_double_sided': is_double_sided,
                }
            )

            total_rows += 1
            if (changed):
                rows_imported[lesson.folder] += 1  

    return lessons, rows_imported, total_rows


async def import_learning_items(input_file):
    """
    imports a file to the database, and returns the imported lessons
    """
    logger.info(f"Processing file: {input_file}")
    await db_init()  
    lessons, rows_imported, total_rows = await import_csv_to_db(input_file)

    logger.info(f'A total {total_rows} in file.')

    for key, value in rows_imported.items():
        logger.info(f'Lesson {key}: {value} rows imported or updated')

    return lessons, rows_imported, total_rows




