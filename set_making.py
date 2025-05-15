import csv
import random
from collections import defaultdict

input_file = 'phrases.csv'
output_file = 'output_sets.csv'

data = defaultdict(lambda: {'positives': [], 'negatives': []})


with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = (row['xid'], row['Project name'])
        phrase = row['Phrase']
        sentiment = row['Sentiment'].lower()

        if 'positive' in sentiment:
            data[key]['positives'].append(phrase)
        elif 'negative' in sentiment:
            data[key]['negatives'].append(phrase)

output_rows = []

for (xid, project_name), sentiments in data.items():
    positives = sentiments['positives']
    negatives = sentiments['negatives']
    used_pos = set()
    used_neg = set()
    sets = []

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

        combined = [f"{p} (positive)" for p in pos_sample] + [f"{n} (negative)" for n in neg_sample]
        sets.append('; '.join(combined))

    row = [xid, project_name] + sets
    output_rows.append(row)

# Determine the max number of sets to build header
max_sets = max((len(row) - 2 for row in output_rows), default=0)
headers = ['xid', 'Project name'] + [f'Set {i+1}' for i in range(max_sets)]

# Write to CSV
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    for row in output_rows:
        row += [''] * (max_sets - len(row) + 2)
        writer.writerow(row)

print(f"✅ Output saved to {output_file}")
