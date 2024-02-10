from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "lesson" (
    "lesson_id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "folder" VARCHAR(255) NOT NULL,
    "order" INT NOT NULL
);
CREATE TABLE IF NOT EXISTS "learningitem" (
    "learning_item_id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "native_text" TEXT NOT NULL,
    "translation" TEXT NOT NULL,
    "is_default_double_sided" INT NOT NULL,
    "tokenized" JSON,
    "lesson_id" INT NOT NULL REFERENCES "lesson" ("lesson_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "analysis" (
    "analysis_id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "index" INT NOT NULL,
    "word" VARCHAR(255) NOT NULL,
    "lemma" VARCHAR(255) NOT NULL,
    "analysis" VARCHAR(255),
    "analysis_detail" JSON,
    "learning_item_id" INT NOT NULL REFERENCES "learningitem" ("learning_item_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "explanation" (
    "analysis_id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "index" INT NOT NULL,
    "word" VARCHAR(255) NOT NULL,
    "lemma" VARCHAR(255) NOT NULL,
    "explanation_detail" JSON,
    "learning_item_id" INT NOT NULL REFERENCES "learningitem" ("learning_item_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "skiplist" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "word" VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
