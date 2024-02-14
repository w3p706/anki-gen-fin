from typing import Union, List, Dict
import urllib.parse
import json


def process_endungen(data):
    """
    Verarbeitet die 'endungen' Daten, um sicherzustellen, dass sie korrekt in einen String umgewandelt werden können.

    :param endungen: Die 'endungen' Daten, die verarbeitet werden sollen.
    :return: Ein String, der die verarbeiteten 'endungen' darstellt.
    """
    if not data:
        return ""
    
    html = ""
    
    # Wenn die 'endungen' eine Liste von Dictionaries sind, werden ihre Werte extrahiert und verbunden
    for entry in data:
        for suffix, definition in entry.items():
            html += f"""<div class="row">
                        <div class="suffix">{suffix}</div>
                        <div class="suffix-def">{definition}</div>
                    </div>"""
        
    return html

def create_html_wiktionary_links(item):
    """
    Erstellt links zu Wiktionary für das Wort und das Basiswort
    """
    html = ""
    if (item.lemma):
        html += f"<a href='http://en.m.wiktionary.org/wiki/{urllib.parse.quote_plus(item.lemma)}#Finnish'>{item.lemma}</a>"
    
    return html



def generate_html(item):
    """
    Erstellt einen HTML-String für ein Wort und seine Eigenschaften.

    :param item: object like this:
         { 
            "word":"maissa",
            "lemma":"maa",
            "suffixes":[{"-issa":"inessiv, Plural; in etwas drin, bezogen auf einen Ort oder Zeit"}],
            "meaning":"ungef\u00e4hr um, in der N\u00e4he von",
            "explanation":"Das Wort 'maissa' in dem Satz 'P\u00e4\u00e4sen t\u00f6ist\u00e4 viiden maissa.' wird als adverbiale Endung verwendet, die eine ungef\u00e4hre Zeitangabe im Finnischen ausdr\u00fcckt. Es leitet sich von dem Wort 'maa' ab, was 'Land' bedeutet, aber in diesem Kontext wird es benutzt, um eine N\u00e4he oder einen ungef\u00e4hren Zeitpunkt anzugeben.",
            "sample":{
                "finnisch":"Olemme perill\u00e4 kuuden maissa.",
                "deutsch":"Wir sind ungef\u00e4hr um sechs Uhr am Ziel."
            }
        }
        
    :return: Ein HTML-String für das Wort und seine Eigenschaften.
    """

    if item is None: 
        return None

    grundform = ""

    if item.word != item.lemma:
        grundform = item.lemma


    sample_target_language = item.explanation_detail['sample'].get('target-language', None)
    sample_translation = item.explanation_detail['sample'].get('translation', None)

    html = f"""<div class="word-definition">
            <details>
                <summary>
                    <div class="summary-content">
                        <div class="word"><b>{item.explanation_detail.get('word', '---')}</b> {grundform}</div>
                        <div class="translation">{item.explanation_detail.get('meaning', '---')}</div>
                    </div>
                </summary>
                <div class="link small">
                    {create_html_wiktionary_links(item)}
                </div>
                <div class="suffix-list small">
                    {process_endungen(item.explanation_detail.get('suffixes', []))}                    
                </div>
                <div class="explanation small">
                    {create_html_details_element(item.explanation_detail.get('explanation', '---'))}
                </div>
                <div class="sample small">
                    <b>Beispiel:</b>
                    <div>{sample_target_language}</div>
                    <div>{sample_translation}</div>
                </div>
            </details>
        </div>"""


    return html





def create_html_details_element(content: Union[str, List[Dict[str, str]]]) -> str:
    """
    Erstellt ein HTML `<details>` Element für den gegebenen Inhalt.

    :param content: Inhalt des `<details>` Elements, kann ein String oder eine Liste von Dictionaries sein.
    :return: String des HTML `<details>` Elements.
    """

    details_html = ""

    # Behandlung verschiedener Inhaltsarten
    if isinstance(content, str):
        details_html += f"<p>{content}</p>"
    elif isinstance(content, list) and content and isinstance(content[0], dict):
        for item in content:
            for key, value in item.items():
                details_html += f"<p><strong>{key}:</strong> {value}</p>"
    else:
        details_html += "<p>Keine detaillierte Erklärung verfügbar.</p>"
    
    return details_html
