from uralicNLP import uralicApi
from uralicNLP import tokenizer
from uralicNLP.cg3 import Cg3
from tortoise import run_async
from tortoise.functions import Count
import csv
import logging
from model import LearningItem, Analysis  # Adjust the import path as necessary
import db
import logger


logger = logging.getLogger(__name__)


cg = Cg3("fin")


language_dict = {
    'fin': 'Finnish'
}
analysis_label_dict = {
    # Example: '@X': 'Unknown analysis'
}
root_dict = {
    # Example: 'N': 'Noun', 'Prop': 'Proper noun', ...
}



def get_root_lexc(file_path):
    with open(file_path, 'r') as file:
        file_content = file.read()

    # Split the content into lines for easier processing
    lines = file_content.splitlines()
    extracted_data = []
    
    for line in lines:
        if line.startswith('+'):
            # Split line to get the first part until '!!' and the rest
            parts = line.split('`@CODE@`:', 1)
            if len(parts) == 2:
                first_col_value = parts[0].split('!!')[0][1:].strip()  # Extract the value until '!!', remove '+'
                # Extract the value after @CODE@: (trimming leading and trailing spaces)
                second_col_value = parts[1].strip()
                extracted_data.append((first_col_value, second_col_value))
    
    
    dictionary = {}
    for key, value in extracted_data:
        if key not in dictionary:
            dictionary[key] = value

    return dictionary



def read_analysis_labels(file_path):
    dictionary = {}
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            key = row[0]
            value = row[1]
            if key not in dictionary:
                dictionary[key] = value
    return dictionary


def process_morphology(arr, language, analysis_label, root):
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
            if key in language_dict:
                language = language_dict[key]
            else:
                language = key
                print(f"Warning: '{item}' not found in language dictionary.")
        elif item.startswith('@'):
            # Lookup in the analysis_label dictionary
            if item in analysis_label_dict:
                analysis_label = analysis_label_dict[item]
            else:
                analysis_label = item
                print(f"Warning: '{item}' not found in analysis_label dictionary.")
        else:
            # Lookup in the root dictionary
            if item in root:
                labels.append(root[item])
            else:
                print(f"Warning: '{item}' not found in root dictionary.")

    return weight, analysis_label, labels, language





async def disambiguate_sentence(leaning_item):

    tokens = tokenizer.words(leaning_item.native_text)
    leaning_item.tokenized = tokens
    leaning_item.save()

    disambiguations = cg.disambiguate(tokens)
    for word, disambiguation in disambiguations:

        for possible_word in disambiguation:
            if (possible_word.morphology[0] == 'Punct'):
                continue

            weight, analysis_label, labels, language = process_morphology(possible_word.morphology, language_dict, analysis_label_dict, root_dict)

            word_analysis = {
                "lemma": possible_word.lemma,
                "morphology": possible_word.morphology,
                "weight": weight,
                "analysis_label": analysis_label,
                "labels": labels,
                "language": language
            }

            analysis = '+'.join([item for item in word_analysis['morphology'] if not item.startswith('<')])

            await Analysis.create(
                    index=tokens.index(word),
                    word=word, 
                    lemma=possible_word.lemma, 
                    analysis = possible_word.lemma + '+' + analysis,
                    analysis_detail=word_analysis,
                    learning_item_id = leaning_item.learning_item_id
                )




# https://kaikki.org/dictionary/Finnish/index.html
# Glinda, Nicole, Charlotte, mathilda

root_dict = get_root_lexc('root.lexc')
analysis_label_dict = read_analysis_labels('analysis_label.csv')

async def run_disambiguation():
    analysis_count = 0
    await db.init() 

    items_without_analysis = await LearningItem.annotate(
        analysis_count=Count('analysis')
    ).filter(analysis_count=0)

    for item in items_without_analysis:
        await disambiguate_sentence(item)

        analysis_count += 1
        logger.info(f'Analysis for {analysis_count}/{len(items_without_analysis)} saved to database')

    # Log the analysis count
    logger.info(f'Total number of analyses performed: {analysis_count}')


run_async(run_disambiguation())