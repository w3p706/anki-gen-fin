import asyncio
from typing import Type
from tortoise import Tortoise, connections, fields, run_async
from tortoise.transactions import in_transaction
from ankigenfin.db.model import Lesson, LearningItem, Analysis, Explanation

# This script copies data between 2 databases.

async def copy_lesson(lesson_id):
    config = {
        "connections": {"destination": "sqlite://media/db.hef.sqlite3", "source": "sqlite://media/db.sqlite3"},
        "apps": {
            "models": {
                "models": ["ankigenfin.db.model", "aerich.models"],
                "default_connection": "destination",
            }
        },
        "use_tz": False,
        "timezone": "UTC",
    }

    # Initialize source DB
    await Tortoise.init(config=config)

    con_source = connections.get("source")
    # con_destination = connections.get("destination")

    
    # Fetch the lesson and related data from source DB
    lesson = await Lesson.get(lesson_id=lesson_id,using_db=con_source).prefetch_related(
        'learning_items__analysis',
        'learning_items__explanation'
    )
        

    async with in_transaction(connection_name="destination") as connection:
        # Create or update the lesson in the destination DB
        dest_lesson = await Lesson.get_or_create(
            lesson_id=lesson.lesson_id,
            name=lesson.name, 
            folder=lesson.folder, 
            order=lesson.order,
            using_db=connection
        )
        
        # Handle related LearningItems, Analysis, and Explanations
        for item in lesson.learning_items:
            dest_item = await LearningItem.create(
                native_text=item.native_text, 
                translation=item.translation,
                translation_machine=item.translation_machine, 
                is_default_double_sided=item.is_default_double_sided,
                tokenized=item.tokenized,
                audio_file_name=item.audio_file_name,
                anki_guid=item.anki_guid,                    
                lesson=dest_lesson[0],
                using_db=connection
            )
                       
            # Assuming analysis and explanation are related by learning_item_id
            for analysis in item.analysis:
                await Analysis.create(
                    index=analysis.index,
                    word=analysis.word,
                    lemma=analysis.lemma,
                    analysis=analysis.analysis,
                    analysis_detail=analysis.analysis_detail,
                    learning_item=dest_item,
                    using_db=connection
                )
            
            for explanation in item.explanation:
                await Explanation.create(
                    index=explanation.index,
                    word=explanation.word,
                    lemma=explanation.lemma,
                    explanation_detail=explanation.explanation_detail,                 
                    learning_item=dest_item,
                    using_db=connection
                )
    
    # Deinitialize destination DB
    await Tortoise.close_connections()

if __name__ == '__main__':
    # run_async(copy_lesson(1188264215))
    run_async(copy_lesson(1206945825))
    run_async(copy_lesson(1265557338))
    run_async(copy_lesson(1285808371))
    run_async(copy_lesson(1318186282))
    run_async(copy_lesson(1387326933))
    run_async(copy_lesson(1462574892))
    run_async(copy_lesson(1472781837))
    run_async(copy_lesson(1536860836))
    run_async(copy_lesson(1539538902))
    run_async(copy_lesson(1695866679))
    run_async(copy_lesson(1854559305))
    run_async(copy_lesson(1880727203))
    run_async(copy_lesson(1894817635))
    run_async(copy_lesson(1934797809))