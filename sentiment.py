

# import pandas as pd
# import time
# import os
# import google.generativeai as genai
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # Configure Gemini
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_API_KEY:
#     raise ValueError("GEMINI_API_KEY not found in environment variables.")
# genai.configure(api_key=GEMINI_API_KEY)
# model = genai.GenerativeModel('gemini-2.0-flash')

# def classify_sentiment(review):
#     prompt = f"""
# You are a home buyer evaluating residential projects.

# Instructions:
# - You are given a review. Determine if it's genuinely positive or negative.
# - If it’s sarcastic or overly promotional (like fake 5-star reviews), ignore it.
# - Also ignore reviews focusing too negatively on builder behavior, sales, or delivery timelines.
# - Do not classify reviews that lack sentiment.

# Review: "{review}"

# Return only one word: 'positive', 'negative', or 'ignore'.
# """
#     try:
#         response = model.generate_content(prompt)
#         time.sleep(5)
#         sentiment = response.text.strip().lower()
#         print(f"Classified sentiment: {sentiment} for review: {review}")
#         return sentiment if sentiment in ['positive', 'negative'] else None
#     except Exception as e:
#         print(f"Error classifying sentiment: {e}")
#         return None

# def process_sentiments(input_file, output_file):
#     df = pd.read_csv(input_file)
#     output_data = []

#     for _, row in df.iterrows():
#         review = str(row['Review']).strip()
#         if not review:
#             continue

#         sentiment = classify_sentiment(review)
#         if sentiment:
#             row_data = row.to_dict()
#             row_data['Sentiment'] = sentiment
#             output_data.append(row_data)

#     result_df = pd.DataFrame(output_data)

    
#     os.makedirs(os.path.dirname(output_file), exist_ok=True)
#     result_df.to_csv(output_file, index=False)
#     print(f"Saved classified reviews to {output_file}")


# os.chdir(r'C:\Users\jha.avinash\OneDrive - Info Edge (India) Ltd\Desktop\test_review')


# input_path = 'input.csv'
# output_path = 'reviews.csv'

# process_sentiments(input_path, output_path)






























import pandas as pd
import time
import os
import requests
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI with your custom endpoint
openai.api_key = "dummy"  # Required by SDK, but ignored by your endpoint

# Model ID for your local deployment
MODEL_ID = "gpt-4.0-mini"

# System instructions
SYSTEM_INSTRUCTION = """
You are an expert residential real estate analyst with extensive experience evaluating homebuyer feedback.

Classification guidelines:
1. POSITIVE: Reviews that genuinely describe positive experiences or aspects of the property itself (quality construction, good amenities, comfortable living experience, sound insulation,locations, USP , etc.)

2. NEGATIVE: Reviews that genuinely describe negative experiences or issues with the property itself (poor construction quality, design flaws, inadequate facilities, maintenance problems, etc.)

3. IGNORE if the review:
   - Uses excessive sarcasm or irony that contradicts its stated sentiment
   - Contains overly promotional language that seems artificially enthusiastic
   - contains excessive negativity about the builder's behavior, sales tactics, or delivery timelines
   - Lacks clear sentiment about the property's actual qualities
   - Is too brief or vague to determine genuine sentiment about the property

Analyze the actual content . Focus exclusively on property quality assessment.

Return only one word as your classification: 'positive', 'negative', or 'ignore'.
"""

def classify_sentiment(review):
    try:
        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": f'Review: "{review}"'}
        ]
        
        data = {
            "messages": messages,
            "temperature": 0.1,  # Lower temperature for deterministic output
            "keyType": "MINI"
        }

        # Send request to your custom endpoint
        response = requests.post(
            'http://new99acresposting:6009/api/analyze',
            json=data,
            headers={"Content-Type": "application/json"}
        )

        # Ensure a successful response
        if response.status_code != 200:
            print(f"Error: Received unexpected status code {response.status_code}")
            return 'ignore'
        
        response_data = response.json()

        # Log the full response for debugging
        print(f"API Response: {response_data}")

        # Check if the response contains the correct 'result' field
        sentiment = response_data.get("result", "").strip().lower()
        
        if sentiment not in ['positive', 'negative', 'ignore']:
            print(f"Invalid response: {sentiment}. Treating as 'ignore'.")
            sentiment = 'ignore'

        print(f"Classified sentiment: {sentiment} for review: {review[:50]}...")
        return sentiment

    except Exception as e:
        print(f"Error classifying sentiment: {e}")
        return 'ignore'

def process_sentiments(input_file, output_file, ignore_file):
    df = pd.read_csv(input_file)
    output_data = []
    ignore_data = []

    for index, row in df.iterrows():
        review = str(row['Review']).strip()
        if not review:
            continue

        print(f"Processing review {index + 1}/{len(df)}...")
        sentiment = classify_sentiment(review)
        row_data = row.to_dict()

        if sentiment in ['positive', 'negative']:
            row_data['Sentiment'] = sentiment
            output_data.append(row_data)
        else:
            row_data['Ignore_Reason'] = "Ignored due to unclear sentiment or irrelevant content."
            ignore_data.append(row_data)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    result_df = pd.DataFrame(output_data)
    result_df.to_csv(output_file, index=False)
    print(f"Saved {len(result_df)} classified reviews to {output_file}")

    if ignore_data:
        ignore_df = pd.DataFrame(ignore_data)
        ignore_df.to_csv(ignore_file, index=False)
        print(f"Saved {len(ignore_df)} ignored reviews with reasons to {ignore_file}")

# Set working directory
os.chdir(r'C:\Users\jha.avinash\OneDrive - Info Edge (India) Ltd\Desktop\test_review')

# File paths
input_path = 'input.csv'
output_path = 'reviews.csv'
ignore_path = 'ignore.csv'

print("Starting sentiment analysis...")
process_sentiments(input_path, output_path, ignore_path)
print("Analysis complete! Check the output folder for results.")
