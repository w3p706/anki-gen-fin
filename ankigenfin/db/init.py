from tortoise import Tortoise, fields, models
from tortoise.contrib.pydantic import pydantic_model_creator
import os
import logging
import logger
import shutil



logger = logging.getLogger(__name__)

# Your models definitions here

TORTOISE_ORM = {
    "connections": {"default": "sqlite://media/db.sqlite3"},
    "apps": {
        "models": {
            "models": ["ankigenfin.db.model", "aerich.models"],
            "default_connection": "default",
        },
    },
}

async def db_init():

    if (not os.path.exists('media/db.sqlite3')):
        logger.info('no database found, copy seed database from seed.sqlite3')
        shutil.copy('seed.sqlite3', 'media/db.sqlite3')

    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
