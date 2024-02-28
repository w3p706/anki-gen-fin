from pydantic import BaseModel, ValidationError
from typing import *
import yaml

class SystemMessage(BaseModel):
    system: str

class AssistantMessage(BaseModel):
    assistant: str

class UserMessage(BaseModel):
    user: str

PromptMessage = Union[SystemMessage, AssistantMessage, UserMessage]


class LanguageToLearn(BaseModel):
    fullname: str
    shortname: str

class MachineTranslation(BaseModel):
    source_language: str
    source_language_fullname: str
    target_language: str
    target_language_fullname: str
    use_deepl: bool
    use_gpt: bool
    model: str
    prompt: List[PromptMessage]

class MainConfig(BaseModel):
    language_to_learn: LanguageToLearn
    machine_translation: MachineTranslation


def config(path: str) -> MainConfig:
    """
    Lädt die Konfigurationsdaten aus einer YAML-Datei.
    
    Args:
        dateipfad (str): Der Pfad zur YAML-Konfigurationsdatei.
    
    Returns:
        dict: Die geladenen Konfigurationsdaten.
    """
    with open(path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    try:
        config = MainConfig(**data)
    except ValidationError as e:
        print(e.json())
        raise
    return config