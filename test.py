from uralicNLP import uralicApi
from uralicNLP import tokenizer
from uralicNLP.cg3 import Cg3
import csv
import json


cg = Cg3("fin")


language_dict = {
    'fin': 'Finnish'
}
analysis_label_dict = {
    # Example: '@X': 'Unknown analysis'
}
root_dict = {
    # Example: 'N': 'Noun', 'Prop': 'Proper noun', ...
}



def get_root_lexc(file_path):
    with open(file_path, 'r') as file:
        file_content = file.read()

    # Split the content into lines for easier processing
    lines = file_content.splitlines()
    extracted_data = []
    
    for line in lines:
        if line.startswith('+'):
            # Split line to get the first part until '!!' and the rest
            parts = line.split('`@CODE@`:', 1)
            if len(parts) == 2:
                first_col_value = parts[0].split('!!')[0][1:].strip()  # Extract the value until '!!', remove '+'
                # Extract the value after @CODE@: (trimming leading and trailing spaces)
                second_col_value = parts[1].strip()
                extracted_data.append((first_col_value, second_col_value))
    
    
    dictionary = {}
    for key, value in extracted_data:
        if key not in dictionary:
            dictionary[key] = value

    return dictionary



def read_analysis_labels(file_path):
    dictionary = {}
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            key = row[0]
            value = row[1]
            if key not in dictionary:
                dictionary[key] = value
    return dictionary


def process_morphology(arr, language, analysis_label, root):
    labels = []
    weight = 0
    analysis_label = ""
    language = ""
    for item in arr:
        if item.startswith('<W'):
            # Convert '<W:0.000000>' to a float value
            weight = float(item.strip('<W:').rstrip('>'))
        elif item.startswith('<'):
            # Lookup in the language dictionary
            key = item.strip('<>')  # Remove '<', '>'
            if key in language_dict:
                language = language_dict[key]
            else:
                language = key
                print(f"Warning: '{item}' not found in language dictionary.")
        elif item.startswith('@'):
            # Lookup in the analysis_label dictionary
            if item in analysis_label_dict:
                analysis_label = analysis_label_dict[item]
            else:
                analysis_label = item
                print(f"Warning: '{item}' not found in analysis_label dictionary.")
        else:
            # Lookup in the root dictionary
            if item in root:
                labels.append(root[item])
            else:
                print(f"Warning: '{item}' not found in root dictionary.")

    return weight, analysis_label, labels, language





def disambiguate_sentence(sentence):
    sentence_analysis = {
            "sentence": sentence,
            "words": {}
    }

    tokens = tokenizer.words(sentence)

    disambiguations = cg.disambiguate(tokens)
    for word, disambiguation in disambiguations:
        possible_words = disambiguation
        for possible_word in possible_words:

            if (possible_word.morphology[0] == 'Punct'):
                continue

            if word not in sentence_analysis["words"]:
                sentence_analysis["words"][word] = []

            weight, analysis_label, labels, language = process_morphology(possible_word.morphology, language_dict, analysis_label_dict, root_dict)

            word_analysis = {
                "lemma": possible_word.lemma,
                "morphology": possible_word.morphology,
                "weight": weight,
                "analysis_label": analysis_label,
                "labels": labels,
                "language": language
            }

            sentence_analysis["words"][word].append(word_analysis)

    return sentence_analysis

# https://kaikki.org/dictionary/Finnish/index.html

root_dict = get_root_lexc('root.lexc')
analysis_label_dict = read_analysis_labels('analysis_label.csv')

result = []
result.append(disambiguate_sentence("Viivillä heiluu hammas."))
result.append(disambiguate_sentence("Anteeksi, missä täällä on vessa?"))

# Specify the file path where you want to save the JSON output
file_path = 'sentence_analysis.json'

# Write the structure to a file in JSON format
with open(file_path, 'w') as json_file:
    json.dump(result, json_file, ensure_ascii=False, indent=4)

print(f"Structure saved as JSON to {file_path}")



# disambiguate_sentence("Nainen harjaa hampaitaan.")
# disambiguate_sentence("Käytkö sinä kaupassa, vai käynkö minä?")
# disambiguate_sentence("Minun täytyy vaihtaa rahaa ulkomaanmatkaa varten.")
# disambiguate_sentence("Viivillä on muumiyöpuku.")
# disambiguate_sentence("Siivooja petaa sängyn hotellihuoneessa.")
# disambiguate_sentence("Tämä ruoka on liian tulista minulle.")


# [('Kuusi', [<kuusi - Num, <fin>, Card, Sg, Nom, <W:0.000000>, @>N>, <kuusi - Num, <fin>, Sg, Nom, <W:0.000000>, @SUBJ>>, <kuusi - N, <fin>, Sg, Nom, <W:0.000000>, @>N>]),
#  ('kuusi', [<kuusi - Num, <fin>, Card, Sg, Nom, <W:0.000000>, @N<>, <kuusi - Num, <fin>, Sg, Nom, <W:0.000000>, @N<>, <kuusi - N, <fin>, Sg, Nom, <W:0.000000>, @SUBJ>>]),
#  ('kasvaa', [<kasvaa - V, <fin>, Act, Ind, Prs, Sg3, <W:0.000000>, @+FMAINV>]),
#  ('kuussa', [<kuu - N, <fin>, Sg, Ine, <W:0.000000>, @X>])]
      


####################
# kuusi ['Num', '<fin>', 'Card', 'Sg', 'Nom', '<W:0.000000>', '@>N']
# kuusi ['Num', '<fin>', 'Sg', 'Nom', '<W:0.000000>', '@SUBJ>']
# kuusi ['N', '<fin>', 'Sg', 'Nom', '<W:0.000000>', '@>N']


# kuusi ['Num', '<fin>', 'Card', 'Sg', 'Nom', '<W:0.000000>', '@N<']
# kuusi ['Num', '<fin>', 'Sg', 'Nom', '<W:0.000000>', '@N<']
# kuusi ['N', '<fin>', 'Sg', 'Nom', '<W:0.000000>', '@SUBJ>']


# kasvaa ['V', '<fin>', 'Act', 'Ind', 'Prs', 'Sg3', '<W:0.000000>', '@+FMAINV']
# kuu ['N', '<fin>', 'Sg', 'Ine', '<W:0.000000>', '@X']       
      

