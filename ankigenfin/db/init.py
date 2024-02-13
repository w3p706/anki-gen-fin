from tortoise import Tortoise, fields, models
from tortoise.contrib.pydantic import pydantic_model_creator

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
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
