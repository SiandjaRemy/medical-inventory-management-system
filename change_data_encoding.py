import json

def convert_utf16_to_utf8(input_filename, output_filename):
    try:
        with open(input_filename, 'r', encoding='utf-16') as f: # Open in UTF-16 mode
            data = json.load(f) # Load the JSON data

        with open(output_filename, 'w', encoding='utf-8') as f: # Write in UTF-8 mode
            json.dump(data, f, indent=4, ensure_ascii=False) # ensure_ascii=False is crucial

        print(f"Successfully converted '{input_filename}' to '{output_filename}'")

    except FileNotFoundError:
        print(f"Error: File '{input_filename}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in '{input_filename}'.")
    except Exception as e:
        print(f"An error occurred: {e}")



# Example usage:
convert_utf16_to_utf8("db.json", "db_utf8.json")

# Then, run loaddata on the new file:
# python manage.py loaddata data_utf8.json
