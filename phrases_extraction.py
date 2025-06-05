
import pandas as pd
import time
import os
import csv
import requests
from dotenv import load_dotenv

load_dotenv()

# API Setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

API_URL = 'http://new99acresposting:6009/api/analyze'

system_instructions = """
[You are a helpful assistant tasked with extracting concise, meaningful phrases from a homebuyer's review that express clear positive or negative sentiment about specific aspects of the property and its immediate surroundings.

 Identify and extract meaningful phrases that describe the characteristics, features, and conditions of the residential property and its immediate surroundings, and clearly indicate a positive or negative feeling about them. Prioritize extracting phrases that are directly stated in the review, avoiding inferences unless absolutely necessary to determine sentiment.

 Guidelines which must be followed while extracting the phrases :

 Focus on aspects like:

 - Physical attributes: construction quality (e.g., "poor wall finishing"), materials, structural elements.
 - Environmental factors: noise levels (e.g., "constant traffic noise"), air quality, natural light, ventilation (e.g., "stuffy rooms"), pest issues.
 - Layout and design: spaciousness (e.g., "cramped living area"), functionality, aesthetics.
 - Amenities (within the property): garden quality (e.g., "well-maintained garden"), gym equipment, pool cleanliness.
 - Connectivity and Accessibility: ease of access to the property, connectivity to public transport, walkability, nearby essential services (if described in terms of convenience or inconvenience related to the property itself).
 - Safety and Security: perceived safety of the area, security features of the property (e.g., "inadequate lighting at night", "broken gate").
 Exclude comments about: builder reputation, pricing, delays, sales/rental experience, construction progress, overall opinions without specific property details.

 Avoid very general terms ("good," "bad") unless they are directly linked to a specific property feature (e.g., "good quality tiles").

 Do not include personal names or addresses.
 include both  positive and negative sentiments.
 Do not include  short phrases which don’t have clear sentiments. For example, avoid phrases like "Good apartment" without specifics.
 Donot include the phrases which contains something  bad about builder , sales team,.
]
"""

def extract_phrases(review, sentiment):
    prompt = f"""
    Review: "{review}"
    Overall Sentiment: {sentiment}

    Extract specific phrases from this review that describe property features with clear sentiment.
    Format each phrase as: "phrase" (sentiment)
    """
    
    try:
        data = {
            "messages": [
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8,
            "keyType": "MINI"
        }
        
        response = requests.post(API_URL, json=data, headers={"Content-Type": "application/json"}, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        print(f"API Response: {response_data}")

        phrases = []
        
        if "result" in response_data:
            result_text = response_data['result']
            for line in result_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('"') and line.endswith('"'):
                    phrase = line[1:-1]
                    phrase_sentiment = "positive" if sentiment.lower() == "positive" else "negative"
                elif '(' in line and ')' in line:
                    parts = line.split('(')
                    phrase = parts[0].strip().strip('"')
                    phrase_sentiment = parts[1].split(')')[0].strip().lower()
                else:
                    phrase = line.strip('"')
                    phrase_sentiment = sentiment.lower()
                
                if phrase:
                    phrases.append({
                        'Phrase': phrase,
                        'Sentiment': phrase_sentiment
                    })
        
        return phrases

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return []
    except Exception as e:
        print(f"Phrase extraction error: {e}")
        return []

def process_phrases(classified_file, phrase_output):
    try:
        try:
            df = pd.read_csv(classified_file)
        except Exception as e:
            print(f"Error reading input file: {e}")
            return

        required_columns = ['xid', 'How Long do you stay here', 'Project name', 'Review', 'Sentiment']
        if not all(col in df.columns for col in required_columns):
            print(f"Input file missing required columns. Needs: {required_columns}")
            return

        os.makedirs(os.path.dirname(phrase_output) or '.', exist_ok=True)

        with open(phrase_output, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['xid', 'How Long do you stay here', 'Project name', 'Phrase', 'Sentiment']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for _, row in df.iterrows():
                review = str(row['Review']).strip()
                if not review:
                    continue
                    
                sentiment = str(row['Sentiment']).strip().lower()
                if sentiment not in ['positive', 'negative']:
                    continue

                phrases_data = extract_phrases(review, sentiment)
                print(f"Extracted {len(phrases_data)} phrases from review: {review[:50]}...")

                for phrase_info in phrases_data:
                    writer.writerow({
                        'xid': row['xid'],
                        'How Long do you stay here': row['How Long do you stay here'],
                        'Project name': row['Project name'],
                        'Phrase': phrase_info['Phrase'],
                        'Sentiment': phrase_info['Sentiment']
                    })
                csvfile.flush()

        print(f"Successfully saved phrases to {phrase_output}")

    except Exception as e:
        print(f"Error in process_phrases: {e}")

# Use relative paths in current working directory
cwd = os.getcwd()
classified_reviews_path = os.path.join(cwd, 'reviews.csv')
phrases_output_path = os.path.join(cwd, 'phrases.csv')

# Run the script
process_phrases(classified_reviews_path, phrases_output_path)
