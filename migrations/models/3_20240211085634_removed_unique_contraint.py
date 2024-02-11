from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "analysislabel_tmp" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "label" VARCHAR(255) NOT NULL UNIQUE,
    "description" VARCHAR(255)
);

INSERT INTO analysislabel_tmp SELECT * FROM analysislabel;

DROP TABLE analysislabel;

ALTER TABLE `analysislabel_tmp` RENAME TO `analysislabel`;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "analysislabel" ADD UNIQUE INDEX "uid_analysislab_descrip_1d568b" ("description");"""
