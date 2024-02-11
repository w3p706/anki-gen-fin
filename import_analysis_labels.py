import csv
from tortoise import run_async
from model import AnalysisLabel  # Adjust the import path as necessary
import db
import random
import logging
import logger

logger = logging.getLogger(__name__)



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



async def run_import():
    await db.init()  # Make sure you have an async init function to set up Tortoise ORM
    await import_korpus_tags_fin('./base_data/korpustags.fin.txt')
    await import_analysis_labels('./base_data/analysis_label.csv')
    await import_root_lexc('./base_data/root.lexc')
    await import_extra()


run_async(run_import())