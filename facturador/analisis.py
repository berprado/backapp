# Let's begin by loading and analyzing the content of each file.
import os

# Define the directory where the files are stored
directory = "/mnt/data/"

# List of files to analyze
files = [
    "config.py", "ui.py", "zeeper.py", "main.py", "invoice_xml_generator.py",
    "verificanit.py", "models.py", "cufd.py", "database.py",
    "export.py", "data_access.py", "generate_cuf.py", "business_logic.py"
]

# Dictionary to store the content of each file
file_contents = {}

# Load and read the contents of each file
for file in files:
    with open(os.path.join(directory, file), 'r') as f:
        file_contents[file] = f.read()

file_contents.keys()  # Just return the keys to confirm the loading was successful.
