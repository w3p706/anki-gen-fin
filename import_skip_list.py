import csv
from tortoise import run_async
from db.model import SkipList  # Adjust the import path as necessary
import db.db
import random
import logging

logger = logging.getLogger(__name__)



async def import_skip_list(csv_file_path):
    logger.info(f'Import {csv_file_path}')    
    rows_imported = 0  # Initialize the counter

    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            await SkipList.update_or_create(word=row['Word'].lower())

            rows_imported += 1  # Increment the counter for each row imported

    logger.info(f'{rows_imported} rows imported')  # Log the number of rows imported


async def run_import():
    await db.init()  # Make sure you have an async init function to set up Tortoise ORM
    await import_skip_list('skip_list.csv')

run_async(run_import())