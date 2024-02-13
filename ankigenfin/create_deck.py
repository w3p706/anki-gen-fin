from .generate_html import generate_html
import genanki
import os
import logging
import logger
from tortoise import run_async
from tortoise.functions import Count
from .db import db_init, LearningItem, Explanation, Lesson   # Adjust the import path as necessary
import uuid


logger = logging.getLogger(__name__)


my_model = genanki.Model(
  1865967360,
  'Card with Explanation & Media',
  fields=[
    {'name': 'Finnish'},
    {'name': 'English'},
    {'name': 'Explanation'},
    {'name': 'HasReverse'},
    {'name': 'Media'}
  ],
  templates=[
    {
      'name': 'Card Finnish => English',
      'qfmt': '<div class="front"><span>{{Finnish}}</span><span style="float: right;">{{Media}}</span></div>',
      'afmt': '{{FrontSide}}<div class="back">{{English}}</div>{{Explanation}}',
    },
    {
      'name': 'Card English => Finnish',
      'qfmt': '{{#HasReverse}}{{English}}{{/HasReverse}}',
      'afmt': '{{FrontSide}}<div class="back"><span>{{Finnish}}</span><span style="float: right;">{{Media}}</span></div>{{Explanation}}',
    }
  ],
    css="""
 
        .card {
            font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 20px;
            color: black;
            background-color: white;
            text-align: left;
            padding: 20px;
            max-width: 500px;
            margin: 0 auto;
        }

        a {
            text-decoration: none;
            border-bottom: 3px solid #ff569d;
            color: #3c0e21;
            line-height: 1.5em;
        }

        details {
            margin: 0 40px 10px 17px;
        }

        p {
            margin: 0 0 3px;
        }
        
        .back { 
            border-top: 1px solid rgb(187, 187, 187);
            padding: 20px 0; 
            margin: 20px 0;
        }

        .explanation {
            margin-bottom: 10px;
            font-family: ui-serif, "New York", serif;
            color: rgb(82, 82, 82);
            margin-left: 1em;
        }

        .explanation,
        .link {
            /* line-height: 1em; */
            color: rgb(82, 82, 82);
            margin: 0 0 10px;
        }

        .link {
            text-align: right;
        }

        .suffix-list {
            display: flex;
            flex-direction: column;
            width: 100%;
            margin: 20px 0;
            margin-left: 1em;
        }

        .row {
            display: flex;
            flex-direction: row;
            margin-bottom: 10px;
        }

        .suffix {
            flex: 0 0 15%;
        }

        .suffix-def {
            flex: 1;
        }

        .small {
            font-family: ui-serif, "New York", serif;
            color: rgb(82, 82, 82);
            font-size: 0.7em;
            line-height: 1em;
        }

        /* https://www.sitepoint.com/community/t/safari-details-summary-problem/396745/13 */
        .word-definition summary::-webkit-details-marker {
            display: none;
        }

        .word-definition summary {
            position: relative;
            font-size: 0.8em;
            list-style: none;
            cursor: pointer;
        }
        .word-definition .word > b {
            color: #861d48;
        }

        /* right arrow */
        .word-definition summary::before {
            content: "";
            position: absolute;
            left: -18px;
            top: 5px;
            width: 6px;
            height: 6px;
            border-top: 2px solid #ff569d;
            border-right: 2px solid #ff569d;
            transform: rotate(45deg);
        }

        .word-definition details[open] summary::before {
            transform: rotate(135deg);
        }

        .sample {
            margin-top: 20px;
        }

        .sample > div {
            margin: 10px 0 10px 40px;
        }

        .replay-button {
            border: initial;
        }

        .replay-button svg {
            width: 24px;
            height: 24px
        }

""",)


async def write_deck(learingitems, file_path):
    # one or multiple decks in a apkg file
    decks = []     
    media = []
    last_deck_name = ""   

    for item in learingitems:    

        audio_file_basename = None

        if (item.audio_file_name is not None):
            audio_file_basename = os.path.basename(item.audio_file_name)
            media.append(item.audio_file_name)

        explanations = await Explanation.filter(learning_item=item).order_by('index')
    
        html = ""
        for word in explanations:
            html += generate_html(word) or ""

        has_reverse = ""

        if item.is_default_double_sided:
            has_reverse = "1"

        if (item.anki_guid is None):
            item.anki_guid = genanki.guid_for(uuid.uuid4())
            await item.save()

        my_note = genanki.Note(
            model=my_model,
            fields=[item.native_text, item.translation, html, has_reverse, f"[sound:{audio_file_basename}]"],
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


async def create_deck(deck, out_file):
    logger.info(f"Processing Deck: {deck}")
    
    await db_init() 

    items = None
    lesson = None

    if (isinstance(deck, (int))):
        lesson = await Lesson.get_or_none(lesson_id=deck)

    if (lesson is None):
        lesson = await Lesson.get_or_none(folder=deck)
        
    if (lesson is None):
        logger.error(f'Deck "{deck}" not found')
        return

    items = await LearningItem.filter(lesson=lesson)

    await write_deck(items, out_file)

