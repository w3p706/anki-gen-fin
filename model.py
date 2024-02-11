from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator

# https://tortoise.github.io/

class Lesson(models.Model):
    lesson_id = fields.IntField(pk=True)  # Primary Key
    name = fields.CharField(max_length=255)
    folder = fields.CharField(max_length=255)
    order = fields.IntField()

    # Relationship with LearningItem
    learning_items = fields.ReverseRelation["LearningItem"]

class LearningItem(models.Model):
    learning_item_id = fields.IntField(pk=True)  # Primary Key
    native_text = fields.TextField()
    translation = fields.TextField()
    is_default_double_sided = fields.BooleanField()
    tokenized = fields.JSONField(null=True)
    lesson = fields.ForeignKeyField('models.Lesson', related_name='learning_items')
    audio_file_name = fields.TextField(null=True)

    # Relationship with Analysis
    analysis = fields.ReverseRelation["Analysis"]
    explanation = fields.ReverseRelation["Explanation"]


class Analysis(models.Model):
    analysis_id = fields.IntField(pk=True)  # Primary Key
    index = fields.IntField() # Index of the word in the sentence
    word = fields.CharField(max_length=255)
    lemma = fields.CharField(max_length=255)
    analysis = fields.CharField(max_length=255, null=True)
    analysis_detail = fields.JSONField(null=True)  

    learning_item: fields.ForeignKeyRelation[LearningItem] = fields.ForeignKeyField(
        "models.LearningItem", related_name="analysis"
    )
    
class Explanation(models.Model):
    analysis_id = fields.IntField(pk=True)  # Primary Key
    index = fields.IntField() # Index of the word in the sentence
    word = fields.CharField(max_length=255)
    lemma = fields.CharField(max_length=255)
    explanation_detail = fields.JSONField(null=True)

    learning_item: fields.ForeignKeyRelation[LearningItem] = fields.ForeignKeyField(
        "models.LearningItem", related_name="explanation"
    )

class SkipList(models.Model):
    word = fields.CharField(max_length=255)


class AnalysisLabel(models.Model):
    label = fields.CharField(max_length=255, unique=True)
    description = fields.CharField(max_length=255)

class Etymology(models.Model):
    word = fields.CharField(max_length=255, unique=True)
    description = fields.TextField()


# Pydantic models for data validation and serialization (optional but useful)
Lesson_Pydantic = pydantic_model_creator(Lesson, name="Lesson")
LearningItem_Pydantic = pydantic_model_creator(LearningItem, name="LearningItem")
Analysis_Pydantic = pydantic_model_creator(Analysis, name="Analysis")
SkipList_Pydantic = pydantic_model_creator(SkipList, name="SkipList")


