import json
from tortoise import run_async
from model import Etymology  # Adjust the import path as necessary
import db
import logging
import logger


logger = logging.getLogger(__name__)

words = 0  # Initialize a counter to keep track of the number of words extracted
keys = {}

# Define a function to extract word and etymology_text from a file
async def extract_word_etymology(file_path):
    extracted_data = []
    global words

    with open(file_path, encoding="utf-8") as f:
        for line in f:
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
            
    
    return extracted_data  




async def run_import():
    await db.init()  # Make sure you have an async init function to set up Tortoise ORM

    # Path to the excerpt file
    file_path = 'base_data/kaikki.org-dictionary-Finnish.json'
    await extract_word_etymology(file_path)
    logger.info(f"Extracted {words} words")  






run_async(run_import())

