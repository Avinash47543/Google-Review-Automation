
import csv
import random
import re
from collections import defaultdict

input_file = 'phrases.csv'
output_file = 'output_sets.csv'


def extract_years(text):
    match = re.search(r'(\d+)', text)
    return int(match.group(1)) if match else 0

# Data structure: {(xid, project): {positives, negatives, durations}}
data = defaultdict(lambda: {'positives': [], 'negatives': [], 'durations': {}})

# Read and group input
with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = (row['xid'], row['Project name'])
        phrase = row['Phrase']
        sentiment = row['Sentiment'].lower()
        duration = extract_years(row['How Long do you stay here'])

        if 'positive' in sentiment:
            data[key]['positives'].append(phrase)
        elif 'negative' in sentiment:
            data[key]['negatives'].append(phrase)

        data[key]['durations'][phrase] = duration

# Build output rows
output_rows = []
max_sets = 0

for (xid, project_name), sentiments in data.items():
    positives = sentiments['positives']
    negatives = sentiments['negatives']
    durations = sentiments['durations']
    used_pos = set()
    used_neg = set()
    sets = []
    avg_durations = []

    while True:
        available_pos = [p for p in positives if p not in used_pos]
        available_neg = [n for n in negatives if n not in used_neg]

        if not available_pos and not available_neg:
            break

        pos_sample_count = min(10, len(available_pos))
        neg_sample_count = min(10, len(available_neg))

        if pos_sample_count == 0 and neg_sample_count == 0:
            break

        pos_sample = random.sample(available_pos, pos_sample_count)
        neg_sample = random.sample(available_neg, neg_sample_count)

        used_pos.update(pos_sample)
        used_neg.update(neg_sample)

        phrases = pos_sample + neg_sample
        combined = [f"{p} (positive)" for p in pos_sample] + [f"{n} (negative)" for n in neg_sample]
        sets.append('; '.join(combined))

        durations_list = [durations[p] for p in phrases if p in durations]
        avg_duration = sum(durations_list) / len(durations_list) if durations_list else 0
        avg_durations.append(f"{avg_duration:.1f} Years")

    max_sets = max(max_sets, len(sets))
    row = [xid, project_name]
    for s, d in zip(sets, avg_durations):
        row.append(s)
        row.append(d)
    output_rows.append(row)

# Prepare headers dynamically
headers = ['xid', 'Project name']
for i in range(1, max_sets + 1):
    headers.append(f'Set {i}')
    headers.append(f'How Long do you stay here {i}')

# Write to output file
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    for row in output_rows:
        row += [''] * (len(headers) - len(row))  # pad missing columns
        writer.writerow(row)

print(f"Output saved to {output_file}")
