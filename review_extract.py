
# import pandas as pd
# import time
# import os
# import csv
# import google.generativeai as genai
# from dotenv import load_dotenv


# load_dotenv()

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_API_KEY:
#     raise ValueError("GEMINI_API_KEY not found in environment variables.")
# genai.configure(api_key=GEMINI_API_KEY)
# model = genai.GenerativeModel('gemini-2.0-flash')

# def extract_phrases(review, sentiment):
#     prompt = f"""
# You are a helpful assistant tasked with extracting concise, meaningful phrases from a homebuyer's review that express clear positive or negative sentiment about specific aspects of the property and its immediate surroundings.

# Identify and extract  phrases that describe the characteristics, features, and conditions of the residential property and its immediate surroundings and clearly indicate a positive or negative feeling about them. Prioritize extracting phrases that are directly stated in the review, avoiding inferences unless absolutely necessary to determine sentiment.

# Guidelines:

# Focus on aspects like:

# Physical attributes: construction quality (e.g., "poor wall finishing"), materials, structural elements.

# Environmental factors: noise levels (e.g., "constant traffic noise"), air quality, natural light, ventilation (e.g., "stuffy rooms"), pest issues.

# Layout and design: spaciousness (e.g., "cramped living area"), functionality, aesthetics.

# Amenities (within the property): garden quality (e.g., "well-maintained garden"), gym equipment, pool cleanliness.

# Connectivity and Accessibility: ease of access to the property, connectivity to public transport, walkability, nearby essential services (if described in terms of convenience or inconvenience related to the property itself).

# Safety and Security: perceived safety of the area, security features of the property (e.g., "inadequate lighting at night", "broken gate").

# Extract phrases as close to the original wording as possible.

# Exclude comments about: builder reputation, pricing, delays, sales/rental experience, construction progress, overall opinions without specific property details.

# Include only phrases that express an opinion or assessment, even if they contain factual elements (e.g., "leaky faucet").

# Avoid very general terms ("good," "bad") unless they are directly linked to a specific property feature (e.g., "good quality tiles").

# Capture both positive and negative sentiments.

# Do not include personal names or addresses.

# Do not extract short phrases which don’t have clear sentiments. For example, avoid phrases like "Good apartment" without specifics.

# When sentiment is implied by the context (e.g., listing something as an amenity), add a parenthetical note explaining the source of the sentiment.

# Example:

# Review: "The apartment has excellent natural light and a very functional kitchen layout. However, the balcony railing feels quite flimsy, and the neighborhood feels unsafe at night. It also has a pool."

# Extracted:

# Phrase: "Excellent natural light", Sentiment: positive

# Phrase: "Functional kitchen layout", Sentiment: positive

# Phrase: "Balcony railing feels quite flimsy", Sentiment: negative

# Phrase: "Neighborhood feels unsafe at night", Sentiment: negative

# Phrase: "Pool", Sentiment: positive (Implied by being listed as a feature of the apartment)

# Now extract from:

# Review: "{review}"

# Overall Sentiment: {sentiment}

# Return only a bullet-point list in this format:

# Phrase: "_", Sentiment: positive/negative (Explanation of sentiment, if implied)
# """
#     try:
#         response = model.generate_content(prompt)
#         time.sleep(8)
#         print(f"Raw API Response for review '{review}':\n{response.text}\n---") 
#         phrases = []
#         for line in response.text.strip().split('\n'):
#             line = line.strip('-•* ')
#             if "Phrase:" in line and "Sentiment:" in line:
#                 try:
#                     phrase_part = line.split("Phrase:")[1].split(",")[0].strip().strip('"')
#                     sentiment_part = line.split("Sentiment:")[1].strip().strip('"').lower()
#                     if phrase_part and sentiment_part in ['positive', 'negative']: 
#                         phrases.append({
#                             'Phrase': phrase_part.strip(), 
#                             'Sentiment': sentiment_part
#                         })
#                 except IndexError:
#                     print(f"Error parsing line: {line}")
#         return phrases
#     except Exception as e:
#         print(f"Phrase extraction error: {e}")
#         return []

# def process_phrases(classified_file, phrase_output):
#     df = pd.read_csv(classified_file)
#     fieldnames = ['xid', 'Project name', 'Phrase', 'Sentiment']

#     with open(phrase_output, 'w', newline='', encoding='utf-8') as csvfile:
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         writer.writeheader()

#         for _, row in df.iterrows():
#             review = str(row['Review'])
#             sentiment = row['Sentiment']
#             phrases_data = extract_phrases(review, sentiment)
#             print(f"Extracted phrases: {phrases_data} for review: {review}")

#             for phrase_info in phrases_data:
#                 writer.writerow({
#                     'xid': row['xid'],
#                     'Project name': row['Project name'],
#                     'Phrase': phrase_info['Phrase'],
#                     'Sentiment': phrase_info['Sentiment']
#                 })
#             csvfile.flush() 

#     print(f"Saved phrases to {phrase_output}")


# classified_reviews_path = r'C:\Users\jha.avinash\OneDrive - Info Edge (India) Ltd\Desktop\test_review\reviews.csv'
# phrases_output_path = r'C:\Users\jha.avinash\OneDrive - Info Edge (India) Ltd\Desktop\test_review\phrases.csv'
# process_phrases(classified_reviews_path, phrases_output_path)


















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

# URL and Model setup for your custom endpoint
API_URL = 'http://new99acresposting:6009/api/analyze'

# System instructions are provided separately for better structure
system_instructions = """
You are a helpful assistant tasked with extracting concise, meaningful phrases from a homebuyer's review that express clear positive or negative sentiment about specific aspects of the property and its immediate surroundings.

Identify and extract phrases that describe the characteristics, features, and conditions of the residential property and its immediate surroundings, and clearly indicate a positive or negative feeling about them. Prioritize extracting phrases that are directly stated in the review, avoiding inferences unless absolutely necessary to determine sentiment.

Guidelines:

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

Do not extract short phrases which don’t have clear sentiments. For example, avoid phrases like "Good apartment" without specifics.

When sentiment is implied by the context (e.g., listing something as an amenity), add a parenthetical note explaining the source of the sentiment.
"""

# Function to classify the sentiment and extract phrases using your API
def extract_phrases(review, sentiment):
    prompt = f"""
    Review: "{review}"
    Overall Sentiment: {sentiment}
    """
    
    try:
        # Send the request to the custom API
        data = {
            "messages": [
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,  # Lower temperature for deterministic output
            "keyType": "MINI"
        }
        
        response = requests.post(API_URL, json=data, headers={"Content-Type": "application/json"})
        
        if response.status_code != 200:
            print(f"Error: Received unexpected status code {response.status_code}")
            return []

        # Parse the response from the API
        response_data = response.json()
        print(f"API Response: {response_data}")

        phrases = []
        
        # Adjust the parsing logic to handle phrases more accurately
        # Split the response into individual phrase and sentiment pairs
        if "result" in response_data:
            result_text = response_data['result']
            # Split by new lines and clean up
            phrase_lines = result_text.split('\n')
            for line in phrase_lines:
                # Ensure the line contains a phrase and sentiment
                if '(' in line and ')' in line:
                    phrase = line.split('"')[1]  # Extract the phrase
                    sentiment = line.split('(')[1].split(')')[0].strip()  # Extract the sentiment
                    phrases.append({
                        'Phrase': phrase.strip(),
                        'Sentiment': sentiment.strip()
                    })
        return phrases

    except Exception as e:
        print(f"Phrase extraction error: {e}")
        return []


def process_phrases(classified_file, phrase_output):
    df = pd.read_csv(classified_file)
    fieldnames = ['xid', 'Project name', 'Phrase', 'Sentiment']

    # Open the output CSV file (it will be created automatically if it doesn't exist)
    with open(phrase_output, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for _, row in df.iterrows():
            review = str(row['Review'])
            sentiment = row['Sentiment']
            phrases_data = extract_phrases(review, sentiment)
            print(f"Extracted phrases: {phrases_data} for review: {review}")

            for phrase_info in phrases_data:
                writer.writerow({
                    'xid': row['xid'],
                    'Project name': row['Project name'],
                    'Phrase': phrase_info['Phrase'],
                    'Sentiment': phrase_info['Sentiment']
                })
            csvfile.flush() 

    print(f"Saved phrases to {phrase_output}")


# Input file (reviews.csv) and output file (phrases.csv)
classified_reviews_path = r'C:\Users\jha.avinash\OneDrive - Info Edge (India) Ltd\Desktop\test_review\reviews.csv'
phrases_output_path = r'C:\Users\jha.avinash\OneDrive - Info Edge (India) Ltd\Desktop\test_review\phrases.csv'
process_phrases(classified_reviews_path, phrases_output_path)
