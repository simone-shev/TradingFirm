import csv
import os

# Get the CSV file name (assuming it's in the same folder as the script)
file_name = "Generated_Stock_Data.csv"  # Change this to your actual CSV file name

# Read the CSV file
rows = []
with open(file_name, mode='r', newline='', encoding='utf-8') as file:
    reader = csv.reader(file)
    header = next(reader)  # Read the header row
    for row in reader:
        # Process each row if needed (modify or keep as is)
        edit = [row[1], row[2], round(float(row[3]), 2), round(float(row[4]), 2), round(float(row[5]), 2), round(float(row[6]), 2)]

        rows.append(edit)

# Write back to the CSV file
with open("data/Generated_Market_Datav2.csv", mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(header)  # Write the header row
    for row in rows:
        writer.writerow(row)
