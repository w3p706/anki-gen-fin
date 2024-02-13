"""
This file generates an HTML page based on the data from a JSON file.
The HTML page contains cards with word analysis results, including explanations and links.
The generated HTML page is saved to a file.
"""

import json
from .generate_html import generate_html


### ****OUTDATED*****
### neeeds to be updated for use with the database


# Pfad zur JSON-Datei
file_path = 'word_analysis_results.json'

# Datei einlesen
with open(file_path, 'r') as file:
    json_data = json.load(file)

# Erstellung des HTML-Dokuments mit der korrigierten Verarbeitung für 'erklärung'
html_content = """<html><head>    <style>
        
        .card {
            font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 20px;
            color: black;
            background-color: white;
            text-align: left;
            padding: 20px;
        }

        a {
            text-decoration: none;
            border-bottom: 3px solid #ff569d;
            color: #3c0e21;
            line-height: 1.5em;
        }


        details {
            margin-bottom: 40px;
            margin-left: 17px;
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

    </style></head><body>
    <div class="card">"""
for item in json_data:
    if ("error" in item):
        continue
    html_content += generate_html(item)
html_content += "</div></body></html>"

# Abspeichern des HTML-Inhalts in eine Datei
html_file_path = 'word_analysis_results.html'
with open(html_file_path, 'w') as file:
    file.write(html_content)



#http://en.m.wiktionary.org/wiki/{{text:sana}}#Finnish    

