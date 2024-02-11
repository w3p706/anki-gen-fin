import csv
from tortoise import run_async
from model import Lesson, LearningItem  # Adjust the import path as necessary
import db
import random
import logging
import argparse
import logger

logger = logging.getLogger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Imports learning items from a CSV file into the database.')
    parser.add_argument('input_file', help='CSV file with learning items to import into the database.')
    args = parser.parse_args()
    return args


def get_or_generate_id():
    # Generate a new id and save it
    new_id = random.randrange(1 << 30, 1 << 31)
    return new_id

async def import_csv_to_db(csv_file_path):
    logger.info(f'Import {csv_file_path}')    
    rows_imported = 0  # Initialize the counter

    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:

            if ("::" not in row['deck']):
                lesson_info = row['deck']
                lesson_name = row['deck']
            else:
                lesson_info = row['deck'].split('::')
                lesson_name = lesson_info[:1] if len(lesson_info) > 1 else None

            # Create or get Lesson
            lesson, created = await Lesson.get_or_create(
                folder=row['deck'],
                defaults={
                    'lesson_id': get_or_generate_id(),
                    'name': lesson_name, 
                    'order': 0
                }  # Adjust 'order' as needed
            )

            # Prepare LearningItem fields
            is_double_sided = True if row['sides'] == 'Double' else False

            logger.debug(f'Importing {row["Finnish"]} - {row["English"]} to lesson {lesson.lesson_id}')

            # Create LearningItem
            entry, changed = await LearningItem.update_or_create(
                lesson=lesson,
                native_text=row['Finnish'],
                defaults=  {
                    'translation':row['English'],
                    'is_default_double_sided': is_double_sided,
                }
            )

            if (changed):
                rows_imported += 1  # Increment the counter for each row imported

    logger.info(f'{rows_imported} rows imported or updated')  # Log the number of rows imported


async def run_import(input_file):
    await db.init()  # Make sure you have an async init function to set up Tortoise ORM
    await import_csv_to_db(input_file)


def main():
    args = parse_arguments()# Parse the command line arguments

    # Use the 'input_file' argument
    input_file_path = args.input_file
    logger.info(f"Processing file: {input_file_path}")

    run_async(run_import(input_file_path))
    

if __name__ == "__main__":
    main()


