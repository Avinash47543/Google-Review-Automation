
# import csv
# import random
# import re
# from collections import defaultdict

# input_file = 'phrases.csv'
# output_file = 'output_sets.csv'

# def extract_years(text):
#     match = re.search(r'(\d+)', text)
#     return int(match.group(1)) if match else 0

# def distribute_phrases_equally(positives, negatives, durations, num_sets=5):
#     """
#     Distribute positive and negative phrases equally across 5 sets
#     """
#     # Shuffle the phrases to ensure random distribution
#     random.shuffle(positives)
#     random.shuffle(negatives)
    
#     # Calculate how many phrases per set
#     pos_per_set = len(positives) // num_sets
#     neg_per_set = len(negatives) // num_sets
    
#     # Calculate remainders (extra phrases)
#     pos_remainder = len(positives) % num_sets
#     neg_remainder = len(negatives) % num_sets
    
#     sets = []
#     pos_index = 0
#     neg_index = 0
    
#     for set_num in range(num_sets):
#         # Calculate phrases for this set
#         pos_count = pos_per_set + (1 if set_num < pos_remainder else 0)
#         neg_count = neg_per_set + (1 if set_num < neg_remainder else 0)
        
#         # Get phrases for this set
#         set_positives = positives[pos_index:pos_index + pos_count]
#         set_negatives = negatives[neg_index:neg_index + neg_count]
        
#         # Update indices
#         pos_index += pos_count
#         neg_index += neg_count
        
#         # Skip empty sets
#         if not set_positives and not set_negatives:
#             continue
        
#         # Create formatted phrases
#         formatted_phrases = []
#         formatted_phrases.extend([f"{p} (positive)" for p in set_positives])
#         formatted_phrases.extend([f"{n} (negative)" for n in set_negatives])
        
#         # Calculate average duration
#         all_phrases = set_positives + set_negatives
#         durations_list = [durations.get(p, 0) for p in all_phrases]
#         avg_duration = sum(durations_list) / len(durations_list) if durations_list else 0
        
#         sets.append({
#             'phrases': '; '.join(formatted_phrases),
#             'duration': f"{avg_duration:.1f} Years",
#             'pos_count': len(set_positives),
#             'neg_count': len(set_negatives)
#         })
    
#     return sets

# # Data structure: {(xid, project): {positives, negatives, durations}}
# data = defaultdict(lambda: {'positives': [], 'negatives': [], 'durations': {}})

# # Read and group input
# with open(input_file, 'r', encoding='utf-8') as f:
#     reader = csv.DictReader(f)
#     for row in reader:
#         key = (row['xid'], row['Project name'])
#         phrase = row['Phrase']
#         sentiment = row['Sentiment'].lower()
#         duration = extract_years(row['How Long do you stay here'])

#         if 'positive' in sentiment:
#             data[key]['positives'].append(phrase)
#         elif 'negative' in sentiment:
#             data[key]['negatives'].append(phrase)

#         data[key]['durations'][phrase] = duration

# # Build output rows
# output_rows = []

# for (xid, project_name), sentiments in data.items():
#     positives = sentiments['positives']
#     negatives = sentiments['negatives']
#     durations = sentiments['durations']
    
#     total_phrases = len(positives) + len(negatives)
    
#     print(f"\n{xid} - {project_name}:")
#     print(f"  Total positives: {len(positives)}")
#     print(f"  Total negatives: {len(negatives)}")
#     print(f"  Total phrases: {total_phrases}")
    
#     # Create sets based on total phrase count
#     if total_phrases < 40:
#         print(f"  Creating 1 set (less than 40 phrases)")
#         # Create one set with all phrases
#         formatted_phrases = []
#         formatted_phrases.extend([f"{p} (positive)" for p in positives])
#         formatted_phrases.extend([f"{n} (negative)" for n in negatives])
        
#         # Calculate average duration
#         all_phrases = positives + negatives
#         durations_list = [durations.get(p, 0) for p in all_phrases]
#         avg_duration = sum(durations_list) / len(durations_list) if durations_list else 0
        
#         sets = [{
#             'phrases': '; '.join(formatted_phrases),
#             'duration': f"{avg_duration:.1f} Years",
#             'pos_count': len(positives),
#             'neg_count': len(negatives)
#         }]
        
#         print(f"    Set 1: {len(positives)} positives, {len(negatives)} negatives")
#     else:
#         print(f"  Distributing across 5 sets...")
#         # Create 5 sets with equal distribution
#         sets = distribute_phrases_equally(positives, negatives, durations, 5)
    
#     # Print distribution info
#     for i, set_data in enumerate(sets, 1):
#         print(f"    Set {i}: {set_data['pos_count']} positives, {set_data['neg_count']} negatives")
    
#     # Build row for this xid/project
#     row = [xid, project_name]
#     for set_data in sets:
#         row.append(set_data['phrases'])
#         row.append(set_data['duration'])
    
#     output_rows.append(row)

# # Prepare headers for exactly 5 sets
# headers = ['xid', 'Project name']
# for i in range(1, 6):
#     headers.append(f'Set {i}')
#     headers.append(f'How Long do you stay here {i}')

# # Write to output file
# with open(output_file, 'w', newline='', encoding='utf-8') as f:
#     writer = csv.writer(f)
#     writer.writerow(headers)
#     for row in output_rows:
#         row += [''] * (len(headers) - len(row))  # pad missing columns
#         writer.writerow(row)

# print(f"\nOutput saved to {output_file}")




























































































import csv
import random
import re
from collections import defaultdict

input_file = 'phrases.csv'
output_file = 'output_sets.csv'

def extract_years(text):
    match = re.search(r'(\d+)', text)
    return int(match.group(1)) if match else 0

def distribute_phrases_equally(positives, negatives, durations, num_sets=4):
    """
    Distribute positive and negative phrases equally across 4 sets
    """
    random.shuffle(positives)
    random.shuffle(negatives)
    
    pos_per_set = len(positives) // num_sets
    neg_per_set = len(negatives) // num_sets
    
    pos_remainder = len(positives) % num_sets
    neg_remainder = len(negatives) % num_sets
    
    sets = []
    pos_index = 0
    neg_index = 0
    
    for set_num in range(num_sets):
        pos_count = pos_per_set + (1 if set_num < pos_remainder else 0)
        neg_count = neg_per_set + (1 if set_num < neg_remainder else 0)
        
        set_positives = positives[pos_index:pos_index + pos_count]
        set_negatives = negatives[neg_index:neg_index + neg_count]
        
        pos_index += pos_count
        neg_index += neg_count
        
        if not set_positives and not set_negatives:
            continue
        
        formatted_phrases = []
        formatted_phrases.extend([f"{p} (positive)" for p in set_positives])
        formatted_phrases.extend([f"{n} (negative)" for n in set_negatives])
        
        all_phrases = set_positives + set_negatives
        durations_list = [durations.get(p, 0) for p in all_phrases]
        avg_duration = sum(durations_list) / len(durations_list) if durations_list else 0
        
        sets.append({
            'phrases': '; '.join(formatted_phrases),
            'duration': f"{avg_duration:.1f} Years",
            'pos_count': len(set_positives),
            'neg_count': len(set_negatives)
        })
    
    return sets

data = defaultdict(lambda: {'positives': [], 'negatives': [], 'durations': {}})

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

output_rows = []

for (xid, project_name), sentiments in data.items():
    positives = sentiments['positives']
    negatives = sentiments['negatives']
    durations = sentiments['durations']
    
    total_phrases = len(positives) + len(negatives)
    
    print(f"\n{xid} - {project_name}:")
    print(f"  Total positives: {len(positives)}")
    print(f"  Total negatives: {len(negatives)}")
    print(f"  Total phrases: {total_phrases}")
    
    if total_phrases < 40:
        print(f"  Creating 1 set (less than 40 phrases)")
        formatted_phrases = []
        formatted_phrases.extend([f"{p} (positive)" for p in positives])
        formatted_phrases.extend([f"{n} (negative)" for n in negatives])
        
        all_phrases = positives + negatives
        durations_list = [durations.get(p, 0) for p in all_phrases]
        avg_duration = sum(durations_list) / len(durations_list) if durations_list else 0
        
        sets = [{
            'phrases': '; '.join(formatted_phrases),
            'duration': f"{avg_duration:.1f} Years",
            'pos_count': len(positives),
            'neg_count': len(negatives)
        }]
        
        print(f"    Set 1: {len(positives)} positives, {len(negatives)} negatives")
    else:
        print(f"  Distributing across 4 sets...")
        sets = distribute_phrases_equally(positives, negatives, durations, 4)
    
    for i, set_data in enumerate(sets, 1):
        print(f"    Set {i}: {set_data['pos_count']} positives, {set_data['neg_count']} negatives")
    
    row = [xid, project_name]
    for set_data in sets:
        row.append(set_data['phrases'])
        row.append(set_data['duration'])
    
    output_rows.append(row)

# Prepare headers for exactly 4 sets
headers = ['xid', 'Project name']
for i in range(1, 5):
    headers.append(f'Set {i}')
    headers.append(f'How Long do you stay here {i}')

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    for row in output_rows:
        row += [''] * (len(headers) - len(row))  # pad missing columns
        writer.writerow(row)

print(f"\nOutput saved to {output_file}")
