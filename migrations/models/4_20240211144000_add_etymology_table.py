from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "etymology" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "word" VARCHAR(255) NOT NULL UNIQUE,
    "description" TEXT NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "etymology";"""
