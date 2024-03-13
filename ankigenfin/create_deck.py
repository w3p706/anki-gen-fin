import genanki
import os
import logging
import logger
from tortoise import run_async
from tortoise.functions import Count
from .db import db_init, LearningItem, Explanation, Lesson   # Adjust the import path as necessary
import uuid
from jinja2 import Environment, FileSystemLoader
from .config import *


logger = logging.getLogger(__name__)

async def get_model():

    css_path = Config.get().anki_card.css_path
    with open(css_path, 'r') as file:
        css = file.read()

    fields = []
    for field in Config.get().anki_card.fields:
        fields.append({'name': field})

    templates = []
    for t in Config.get().anki_card.templates:
        templates.append({
            'name': t.name,
            'qfmt': t.qfmt,
            'afmt': t.afmt,
        })

    my_model = genanki.Model(
        Config.get().anki_card.id,
        Config.get().anki_card.name,
        fields=fields,
        templates=templates,
        css=css,)
    
    return my_model

    


async def write_deck(learingitems, file_path):
    # one or multiple decks in a apkg file
    decks = []     
    media = []
    last_deck_name = ""   

    my_model = await get_model()

    template_path = Config.get().anki_card.explanation_template

    template_dir = os.path.dirname(template_path)
    template_file = os.path.basename(template_path)
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_file)

    for item in learingitems:    

        subfolder = str(item.audio_file_name)[0]
        subfolder_path = os.path.join(Config.get().audio_generation.output_folder, subfolder)
        filename = os.path.join(subfolder_path, item.audio_file_name)
        media.append(filename)

        explanations = await Explanation.filter(learning_item=item).order_by('index')

        # '{
        #     "word": "Koiramme",
        #     "lemma": "koira",
        #     "suffixes": [
        #         {
        #             "-mme": "1. Person Plural possessivsuffix; unser"
        #         }
        #     ],
        #     "meaning": "unser Hund",
        #     "explanation": "Das finnische Wort \'Koiramme\' besteht aus der Grundform \'koira\', was \'Hund\' bedeutet, und dem Suffix \'-mme\', welches einen Besitz in der ersten Person Plural (unser) anzeigt. Es wird in einer neutralen, allt\\u00e4glichen Situation verwendet, um auf ein Haustier zu verweisen, das den Sprechern gemeinsam geh\\u00f6rt.",
        #     "sample": {
        #         "target-language": "Koiramme leikkii puistossa.",
        #         "translation": "Unser Hund spielt im Park."
        #     }
        # }'

        html = ""
        for word in explanations:
            explanation_html = template.render(item=word.explanation_detail)
            html += explanation_html or ""

        has_reverse = ""

        if item.is_default_double_sided:
            has_reverse = "1"

        if (item.anki_guid is None):
            item.anki_guid = genanki.guid_for(uuid.uuid4())
            await item.save()

        translation = item.translation
        if (item.translation_machine is not None):
            translation += f" / {item.translation_machine}"

        my_note = genanki.Note(
            model=my_model,
            fields=[item.native_text, f"{translation}" , html, has_reverse, f"[sound:{item.audio_file_name}]"],
            guid=item.anki_guid)
        
        lesson = await Lesson.get(lesson_id=item.lesson_id)
        if (last_deck_name != lesson.folder):
            my_deck = genanki.Deck(lesson.lesson_id, lesson.folder)
            logger.info(f'Deck Name: {lesson.folder}')
            last_deck_name = lesson.folder
            decks.append(my_deck) 
                            
        my_deck.add_note(my_note)


    package = genanki.Package(decks)
    package.media_files = media
    package.write_to_file(file_path)

    logger.info(f'File written: {file_path}')


async def create_deck(lession_list, out_file=None):
    
    await db_init() 

    lessons = await Lesson.filter(folder__in=lession_list).all()
    if (not (lessons is None or len(lessons) == 0)):
        lession_list = [lesson.lesson_id for lesson in lessons]  

    logger.info(f"Creating deck for lessions {lession_list}")
    items = await LearningItem.filter(lesson_id__in=lession_list).order_by('lesson_id', 'learning_item_id')
        
    if (len(items) == 0):
        logger.error(f'Lessions "{lession_list}" have no items')
        return

    await write_deck(items, out_file)

