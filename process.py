import json
import csv
import explain
import logging
import logger

logger = logging.getLogger(__name__)

# Create an empty dictionary to store the skip list
skip_list = {}

# Open the CSV file
with open('skip_list.csv', 'r') as file:
    # Create a CSV reader object
    reader = csv.reader(file)

    # Skip the header row
    next(reader)

    # Iterate over each row in the CSV file
    for row in reader:
        # Extract the word and its skip value from the row
        word = row[0]
        skip_value = int(row[1])

        # Add the word and skip value to the skip list dictionary
        skip_list[word.lower()] = skip_value


## Todo: If Explanation => Skip sentence. Explanation Complete?
## create additional Skiplist with morphology voi+N+Sg+Par, count from database



# Open the JSON file
with open('sentence_analysis.json', 'r') as file:
    # Load the JSON data
    data = json.load(file)

    # Filter the data by "folder": "101::LB-S1-L11"
    filtered_data = [item for item in data if item.get("folder") == "101::LB-S1-L11"]
    iteration_count = 0

    # Loop for every word
    for item in filtered_data:
        logger.info(f'Analizing {item.get("sentence")}')
        words = item.get("words")

        if iteration_count >= 3:
            break  # Exit the loop

        iteration_count += 1

        # Loop for every word
        for word, word_analysis in words.items():
            
            # Skip the word if it is in the skip list
            if word.lower() in skip_list:
                continue

            word_data_with_context = {
                "sentence": item.get("sentence"),
                "words": {
                    word: []
                }
            }

            # Loop for every word in word_analysis
            for analysis in word_analysis:
                # Get the word's lemma, weight, analysis_label, labels, and language
                lemma = analysis.get("lemma")
                weight = analysis.get("weight")
                analysis_label = analysis.get("analysis_label")
                labels = analysis.get("labels")
                language = analysis.get("language")

                # Create a new word entry in the new structure
                word_data_with_context["words"][word].append({
                    "lemma": lemma,
                    "weight": weight,
                    "analysis_label": analysis_label,
                    "labels": labels,
                    "language": language
                })

            logger.info(f'Analizing {word}')
            explanation = explain.gpt_explain(word, word_data_with_context)

            if not explanation:
                continue

            if "explanation" not in item:
                item["explanation"] = []

            item["explanation"].append(explanation)



# Save the updated JSON data
with open('sentence_analysis_updated.json', 'w') as file:
    json.dump(data, file)



            

            