from tortoise import Tortoise, run_async
from .db import db_init, Explanation  # Adjust the import according to your project structure
import json
import jsonschema
from jsonschema import validate
import copy
import logging
import logger

logger = logging.getLogger(__name__)


schema_file_path = "ankigenfin/gpt-out.schema.json"

def load_json_schema():
    """
    Load the JSON Schema from a file.
    """
    with open(schema_file_path, 'r') as file:
        schema = json.load(file)
    return schema

# Function to validate a single explanation detail
async def adjust_explanation_detail(explanation, schema):
    if (explanation.explanation_detail is None):
        logger.warning(f"Explanation detail is None. Deleting record: {explanation.analysis_id}")
        await explanation.delete() 
        return False

    try:
        validate(instance=explanation.explanation_detail, schema=schema)
        return True
    except jsonschema.exceptions.ValidationError as e:
        # Attempt to correct the data
        correction = False
        corrected_detail = copy.deepcopy(explanation.explanation_detail)  # Make a copy to avoid modifying the original
        if 'sample' in corrected_detail and 'finnisch' in corrected_detail['sample']:
            corrected_detail['sample']['target-language'] = corrected_detail['sample'].pop('finnisch')
            correction = True
        if 'sample' in corrected_detail and 'finnish' in corrected_detail['sample']:
            corrected_detail['sample']['target-language'] = corrected_detail['sample'].pop('finnish')
            correction = True
        if 'sample' in corrected_detail and 'deutsch' in corrected_detail['sample']:
            corrected_detail['sample']['translation'] = corrected_detail['sample'].pop('deutsch')
            correction = True
        
        if (correction):
            explanation.explanation_detail = corrected_detail
            await explanation.save() 
            return False
        
        if (not correction):
            logger.warning(f"Non recoverable error: {e.message}, {explanation.id}: Data removed.")
            await explanation.delete() 

        return False


# Main function to loop through explanations and validate them
async def check_and_migrate_explanations():
    await db_init()
    schema = load_json_schema()
    explanations = await Explanation.all()
    for explanation in explanations:
        await adjust_explanation_detail(explanation, schema)


