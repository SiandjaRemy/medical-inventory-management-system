import chardet

with open("db.json", "rb") as f: # Open in binary mode
    result = chardet.detect(f.read())

print(f"Detected encoding: {result['encoding']}")
