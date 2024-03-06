import aiohttp
import asyncio
import aiofiles
import csv
from tortoise import Tortoise, fields
from tortoise.models import Model
import json
import logging
import logger
import os
from .db import Etymology, SkipList, AnalysisLabel  # Adjust the import path as necessary

logger = logging.getLogger(__name__)

async def download_file(url, path):
    if os.path.exists(path):
        logger.info(f'File {path} already exists, skip downloading')
        return

    logger.info(f'Downloading {url} to {path}')

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            # Try to extract the total file size from response headers
            total_size = response.headers.get('content-length')
            if total_size is not None:
                total_size = int(total_size)
            else:
                logger.info("Couldn't determine the file size, progress will not be shown.")
                total_size = 0

            with open(f'{path}.tmp', 'wb') as f:
                downloaded = 0
                last_reported_progress = -10  # Initialize to a value less than 0

                while True:
                    chunk = await response.content.read(65536)  # You can adjust the chunk size if needed
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        # Check if progress has crossed the next 10% threshold
                        if progress >= last_reported_progress + 150:
                            logger.info(f'Download progress: {progress:.0f}%')
                            last_reported_progress = progress - (progress % 10)  # Update threshold

    # Rename the temporary file to the final file name
    os.rename(f'{path}.tmp', path)

    logger.info(f'Download {url} to {path} completed')


# Define a function to extract word and etymology_text from a file
async def extract_word_etymology(file_path):
    words = 0  # Initialize a counter to keep track of the number of words extracted
    keys = {}   
    extracted_data = []
    processed_lines = 0

    logger.info(f'Extracting word and etymology_text from {file_path}, and inserting into the database.')

    async with aiofiles.open(file_path, 'r') as f:
        async for line in f:
            data = json.loads(line)
            # Initialize dictionary to hold the extracted information
            word_info = {"word": data.get("word", None)}
            # Check if etymology_text is available, handle if it's not present
            etymology_text = data.get("etymology_text", None)
            word_info["etymology_text"] = etymology_text

            if (word_info["word"] is None or word_info["word"].strip() == "" or len(word_info["word"]) < 2):
                continue

            if etymology_text is  None or etymology_text.strip() == "":
                continue

            if (word_info["word"] in keys):
                continue    
            else:
                keys[word_info["word"]] = True

            try:
                entry = await Etymology.create(word=word_info["word"], description=word_info["etymology_text"])
                words += 1
            except Exception as e:
                logger.warn(f"Error while inserting '{word_info["word"]}': {e}")    

            processed_lines += 1
            if (processed_lines % 1000 == 0):
                logger.info(f'Processed {processed_lines} lines')
            



async def import_skiplist_from_csv(csv_file_path):
    logger.info(f'Import {csv_file_path}')    
    rows_imported = 0  # Initialize the counter

    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            await SkipList.update_or_create(word=row['Word'].lower())

            rows_imported += 1  # Increment the counter for each row imported

    logger.info(f'{rows_imported} rows imported')  # Log the number of rows imported




# https://github.com/giellalt/lang-fin/blob/main/test/data/korpustags.fin.txt
async def import_korpus_tags_fin(file_path):
    logger.info(f'Import {file_path}')
    rows_imported = 0  # Initialize the counter


 # Initialize containers for the two parts
    text_lines = []
    tsv_lines = []
    
    # Flag to determine which part of the file we're currently reading
    reading_tsv = False
    
    with open(file_path, newline='', encoding='utf-8-sig') as tsvfile:
        for line in tsvfile:
            # Check for the transition from text to TSV part
            if line.strip().startswith('%') or line.strip().startswith('#') or line.strip() == '':
                continue

            values = line.split('\t')

            if (len(values) < 2):
                continue
            
            entry, updated = await AnalysisLabel.get_or_create(label=values[0].strip(), defaults={'description': values[1].strip()})

            if updated:
                rows_imported += 1  # Increment the counter for each row imported

    logger.info(f'{rows_imported} rows imported or updated')  # Log the number of rows imported
    
    
# https://wiki.apertium.org/wiki/Syntactic_labels
async def import_analysis_labels(csv_file_path):
    logger.info(f'Import {csv_file_path}')    
    rows_imported = 0  # Initialize the counter

    with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            entry, updated = await AnalysisLabel.get_or_create(label=row['Tag'], defaults={'description' : row['Description']})

            if (updated):  
                rows_imported += 1  # Increment the counter for each row imported

    logger.info(f'{rows_imported} rows imported or updated')  # Log the number of rows imported

# https://github.com/giellalt/lang-fin/blob/main/src/fst/morphology/root.lexc
async def import_root_lexc(file_path):

    rows_imported = 0  # Initialize the counter

    with open(file_path, 'r') as file:
        file_content = file.read()

        # Split the content into lines for easier processing
        lines = file_content.splitlines()
        keys = {}
        
        for line in lines:
            if line.startswith('+'):
                # Split line to get the first part until '!!' and the rest
                parts = line.split('`@CODE@`:', 1)
                if len(parts) == 2:
                    first_col_value = parts[0].split('!!')[0][1:].strip()  # Extract the value until '!!', remove '+'
                    # Extract the value after @CODE@: (trimming leading and trailing spaces)
                    second_col_value = parts[1].strip()

                    # only import or update the first row.
                    if (first_col_value in keys):
                        continue
                    keys[first_col_value] = second_col_value 

                    etnry, updated = await AnalysisLabel.get_or_create(label=first_col_value, defaults={'description' : second_col_value})
                    if (updated):  
                        rows_imported += 1  # Increment the counter for each row imported

    logger.info(f'{rows_imported} rows imported or updated')  # Log the number of rows imported

async def import_extra():

    entry, updated = await AnalysisLabel.get_or_create(label='Cmpnd', defaults={'description' : 'Compound'})
    entry, updated = await AnalysisLabel.get_or_create(label='Pe4', defaults={'description' : 'Compound'})
    # etnry, updated = await AnalysisLabel.get_or_create(label='@HAB', defaults={'description' : 'Compound'}) # unknow synfunc
    # etnry, updated = await AnalysisLabel.get_or_create(label='@>P', defaults={'description' : 'Complement of postposition'})



async def generate_seed_db():

    if (os.path.exists('seed_temp.sqlite3')):
        logger.info('Removing old incomplete seed_temp.sqlite3')
        os.delete('seed_temp.sqlite3')

    TORTOISE_ORM = {
        "connections": {"default": "sqlite://seed_temp.sqlite3"},
        "apps": {
            "models": {
                "models": ["ankigenfin.db.model", "aerich.models"],
                "default_connection": "default",
            },
        },
    }

    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()

    dict_path = './ankigenfin/base_data/kaikki.org-dictionary-Finnish.jsonlines'
    skip_list = './ankigenfin/base_data/skip_list.csv'
    kopus_tags = './ankigenfin/base_data/korpustags.fin.txt'
    analysis_labels = './ankigenfin/base_data/analysis_label.csv'
    root_lexc = './ankigenfin/base_data/root.lexc'


    await download_file('https://kaikki.org/dictionary/Finnish/kaikki.org-dictionary-Finnish.json', dict_path)
    await extract_word_etymology(dict_path)

    # Import the skip list
    await import_skiplist_from_csv(skip_list)

    # Import the analysis labels
    await import_korpus_tags_fin(kopus_tags)
    await import_analysis_labels(analysis_labels)
    await import_root_lexc(root_lexc)
    await import_extra()

    # Close Tortoise connections
    await Tortoise.close_connections()


    if (os.path.exists('seed.sqlite3')):
        logger.info('Removing old seed.sqlite3')
        os.delete('seed.sqlite3')

    os.rename('seed_temp.sqlite3', 'seed.sqlite3')

    logger.info('Seed database generation completed successfully.')