import pandas as pd


def vtt_to_csv(inputfile, outputfile, ankideck):
    # Read the VTT file
    with open(inputfile, 'r') as file:
        text_content = file.read()

    # Split the content into blocks based on the empty lines
    blocks = text_content.strip().split('\n\n')

    # Process each block to extract the relevant lines
    data = []
    for block in blocks[3:]:  # Skipping the first 3 lines of metadata
        lines = block.split('\n')
        # Append only the relevant lines (timestamp and text, ignoring translations)
        data.append([lines[0], lines[1], lines[2]])

    # Convert the list to a DataFrame
    df = pd.DataFrame(data, columns=['Timestamp', 'item', 'translation'])

    df['sides'] = 'Single'
    df['deck'] = ankideck

    # Drop the 'Timestamp' column
    df = df.drop('Timestamp', axis=1)

    # Save the DataFrame to a CSV file
    csv_file_path = outputfile
    df.to_csv(csv_file_path, index=False)

    return csv_file_path



