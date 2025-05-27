
import pandas as pd
import time
import os
import requests
import openai
from dotenv import load_dotenv
import chardet
from typing import Dict, List, Optional
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sentiment_analysis.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

openai.api_key = "dummy"  # Required by SDK, ignored by custom endpoint
MODEL_ID = "gpt-4.0-mini"

SYSTEM_INSTRUCTION = """
You are an expert residential real estate analyst with extensive experience evaluating homebuyer feedback.

Classification guidelines:
1. POSITIVE: Reviews that genuinely describe positive experiences or aspects of the property itself (quality construction, good amenities, comfortable living experience, sound insulation, locations, USP, etc.)

2. NEGATIVE: Reviews that genuinely describe negative experiences or issues with the property itself (poor construction quality, design flaws, inadequate facilities, maintenance problems, etc.)

3. IGNORE if the review:
   - Uses excessive sarcasm or irony that contradicts its stated sentiment
   - Contains overly promotional language that seems artificially enthusiastic
   - Contains excessive negativity about the builder's behavior, sales tactics, or delivery timelines
   - Lacks clear sentiment about the property's actual qualities
   - Is too brief or vague to determine genuine sentiment about the property

Analyze the actual content. Focus exclusively on property quality assessment.

Return only one word as your classification: 'positive', 'negative', or 'ignore'.
"""

def detect_file_encoding(file_path: str) -> str:
    try:
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read())
        return result['encoding'] or 'utf-8'
    except Exception as e:
        logging.error(f"Error detecting file encoding: {e}")
        return 'utf-8'

def classify_sentiment(review: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            messages = [
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": f'Review: "{review}"'}
            ]
            
            data = {
                "messages": messages,
                "temperature": 0.8,
                "keyType": "MINI"
            }

            response = requests.post(
                'http://new99acresposting:6009/api/analyze',
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code != 200:
                logging.warning(f"Attempt {attempt + 1}: Received status code {response.status_code}")
                time.sleep(2 ** attempt)
                continue
            
            response_data = response.json()
            sentiment = response_data.get("result", "").strip().lower()
            valid_sentiments = {'positive', 'negative', 'ignore'}

            if sentiment not in valid_sentiments:
                logging.warning(f"Invalid response: {sentiment}. Treating as 'ignore'.")
                sentiment = 'ignore'

            logging.info(f"Classified sentiment: {sentiment} for review: {review[:50]}...")
            return sentiment

        except requests.exceptions.RequestException as e:
            logging.warning(f"Attempt {attempt + 1}: API request failed - {str(e)}")
            time.sleep(2 ** attempt)
        except Exception as e:
            logging.error(f"Unexpected error during classification: {e}")
            break

    return 'ignore'

def ensure_directory_exists(file_path: str) -> None:
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def process_sentiments(input_file: str, output_file: str, ignore_file: str) -> None:
    try:
        encoding = detect_file_encoding(input_file)
        logging.info(f"Detected encoding: {encoding} for file: {input_file}")

        try:
            df = pd.read_csv(input_file, encoding=encoding)
        except UnicodeDecodeError:
            for fallback_encoding in ['windows-1252', 'iso-8859-1', 'latin1']:
                try:
                    df = pd.read_csv(input_file, encoding=fallback_encoding)
                    logging.info(f"Successfully read with {fallback_encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Failed to read file with any supported encoding")

        # Clean column names
        df.columns = [col.strip() for col in df.columns]

        if 'Review' not in df.columns:
            raise ValueError("Input CSV must contain a 'Review' column")

        output_data = []
        ignore_data = []
        total_reviews = len(df)
        
        logging.info(f"Starting processing of {total_reviews} reviews...")

        for index, row in df.iterrows():
            review = str(row['Review']).strip()
            if not review:
                continue

            duration = row.get('How Long do you stay here', 'N/A')
            logging.info(f"Processing review {index + 1}/{total_reviews} | Stay Duration: {duration}")

            sentiment = classify_sentiment(review)
            row_data = row.to_dict()

            if sentiment in ['positive', 'negative']:
                row_data['Sentiment'] = sentiment
                output_data.append(row_data)
            else:
                row_data['Ignore_Reason'] = "Ignored due to unclear sentiment or irrelevant content."
                ignore_data.append(row_data)

            if (index + 1) % 10 == 0:
                logging.info(f"Processed {index + 1}/{total_reviews} reviews")

        ensure_directory_exists(output_file)
        ensure_directory_exists(ignore_file)

        if output_data:
            result_df = pd.DataFrame(output_data)
            result_df.to_csv(output_file, index=False, encoding='utf-8')
            logging.info(f"Saved {len(result_df)} classified reviews to {output_file}")

        if ignore_data:
            ignore_df = pd.DataFrame(ignore_data)
            ignore_df.to_csv(ignore_file, index=False, encoding='utf-8')
            logging.info(f"Saved {len(ignore_df)} ignored reviews to {ignore_file}")

    except Exception as e:
        logging.error(f"Fatal error in process_sentiments: {e}", exc_info=True)
        raise

def main():
    try:
        os.chdir(r'C:\Users\jha.avinash\OneDrive - Info Edge (India) Ltd\Desktop\test_review')

        input_path = 'input.csv'
        output_path = 'reviews.csv'
        ignore_path = 'ignore.csv'

        logging.info("Starting sentiment analysis pipeline...")
        start_time = time.time()
        
        process_sentiments(input_path, output_path, ignore_path)
        
        elapsed_time = time.time() - start_time
        logging.info(f"Analysis complete! Total processing time: {elapsed_time:.2f} seconds")

    except Exception as e:
        logging.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
