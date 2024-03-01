from pydantic import BaseModel, ValidationError, FilePath, fields
from typing import *
import yaml
import os
import logging
import logger

logger = logging.getLogger(__name__)

class SystemMessage(BaseModel):
    system: str

class AssistantMessage(BaseModel):
    assistant: str

class UserMessage(BaseModel):
    user: str

PromptMessage = Union[SystemMessage, AssistantMessage, UserMessage]

class GptOptions(BaseModel):
    model: str
    prompt: List[PromptMessage]
    max_retries: int
    max_parallel_calls: int
    timeout: int
    schema_file_path: Optional[FilePath] = None

class Language(BaseModel):
    fullname: str
    shortname: str
    cg_language_name: Optional[str] = ""

class MachineTranslation(BaseModel):
    use_deepl: bool
    use_gpt: bool
    gpt_options: GptOptions

class Voice(BaseModel):
    name: str
    id: str
    use_speaker_boost: bool
    style: int
    stability: float
    similarity_boost: float

class AudioGeneration(BaseModel):
    model: str
    max_parallel_calls: int
    max_retries: int
    timeout: int
    output_folder: str
    voices: List[Voice]    

class Explain(BaseModel):
    gpt_options: GptOptions

class Template(BaseModel):
    name: str
    qfmt: str
    afmt: str

class AnkiCard(BaseModel):
    id: int
    name: str
    fields: List[str]
    templates: List[Template]
    css_path: FilePath  
    explanation_template: FilePath  


class Config(BaseModel):
    target_language: Language
    translated_language: Language
    machine_translation: MachineTranslation
    audio_generation: AudioGeneration
    analyze: Dict[str, str]
    explain: Explain
    anki_card: AnkiCard


    # Class variable to hold the config instance
    _config_data: Optional['Config'] = None

    @classmethod
    def load_from_yaml(cls, file_path: str = None):
        if file_path is None:
            file_path = os.environ.get("CONFIG")
            if file_path is None:
                raise ValueError("No file path provided and 'CONFIG' environment variable is not set.")
        
        logger.info(f"Loading config from {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            try:
                cls._config_data = cls(**data)
            except ValidationError as e:
                logger.error(f"Error loading config: {e}")
                exit(1)
            
            logger.info(f"Config loaded.")
        


    @classmethod
    def get(cls) -> 'Config':
        if cls._config_data is None or isinstance(cls._config_data, fields.ModelPrivateAttr):
            cls.load_from_yaml()
        return cls._config_data        

