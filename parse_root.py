import csv



def extract_and_parse_lines_fixed(content):
    # Split the content into lines for easier processing
    lines = content.splitlines()
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
    
    return extracted_data


# Re-read the file content to ensure we have the correct data to work with
with open('root.lexc', 'r') as file:
    file_content = file.read()


# Re-extract and parse the lines with the fixed approach
parsed_lines_fixed = extract_and_parse_lines_fixed(file_content)

print(parsed_lines_fixed[:10])  # Print the first 10 parsed lines

# Define the path for the CSV file where we'll save the results
csv_file_path = 'root.csv'

# Write the extracted data to a CSV file
with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    # Write a header row
    writer.writerow(['First Column', 'Second Column'])
    # Write the extracted data
    writer.writerows(parsed_lines_fixed)
