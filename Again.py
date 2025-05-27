
import os
import csv
import time
import random
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.0-flash")

def enhance_negative_content(original_negative, max_retries=5):
    prompt = f"""
    Improve and enhance the following negative housing society review content while maintaining the same meaning and key points. Make it more natural, detailed, and engaging:

    Original Negative Points:
    {original_negative}

    Instructions:
    1. Keep the same core feedback but make it sound more natural, use conversational English, which can be understood by a general audience.
    2. Maintain the original negative sentiment 
    3. Start directly with the main issue or complaint. DO NOT use filler phrases like "Unfortunately", "Honestly", "To be honest", "Overall", "I have to say", "Let me be frank", etc.
    4. Begin immediately with the specific problem, concern, or criticism
    5. Return ONLY the enhanced negative content (no section headers needed)
    6. Should be 2-3 sentences that sound like genuine resident feedback
    7. Do not add any extra content or points which are not there in the original review
    8. Make the feedback sound direct and straightforward without softening introductions
    9. Ensure no contradictory statements within the review

    Examples of GOOD negative review starts:
    - "The maintenance response time is extremely slow..."
    - "Parking spaces are insufficient for residents..."
    - "The gym equipment is poorly maintained..."
    - "Noise levels from construction are unbearable..."
    
    Examples of BAD negative review starts to AVOID:
    - "Unfortunately, the maintenance response time..."
    - "Honestly, I think the parking spaces..."
    - "To be frank, the gym equipment..."
    - "Overall, the noise levels..."
    """
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            time.sleep(5)  # Wait 5 seconds after successful call
            return response.text.strip()
        except ResourceExhausted as e:
            wait = (2 ** attempt) + random.uniform(0, 1)
            print(f"Rate limit hit. Waiting {wait:.1f} seconds before retrying... (Attempt {attempt+1}/{max_retries})")
            time.sleep(wait)
        except Exception as e:
            print(f"Error enhancing content: {e}")
            break
    return None

def main():
    input_csv = "processed_reviews.csv"
    output_csv = "enhanced_reviews.csv"

    with open(input_csv, encoding="utf-8") as f_in, open(output_csv, "w", encoding="utf-8", newline="") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for idx, row in enumerate(reader, 1):
            original_positive = row.get("positive", "").strip()
            original_negative = row.get("negative", "").strip()
            
            print(f"Processing review {idx}...")
            
            # Keep positive content as-is
            enhanced_positive = original_positive
            
            # Only enhance negative content if it exists
            if original_negative:
                print(f"Enhancing negative content for review {idx}...")
                enhanced_negative_content = enhance_negative_content(original_negative)
                
                if enhanced_negative_content:
                    enhanced_negative = enhanced_negative_content
                    print(f"Review {idx} negative content enhanced.")
                else:
                    enhanced_negative = original_negative
                    print(f"Review {idx} negative enhancement failed, kept original.")
            else:
                enhanced_negative = original_negative
                print(f"Review {idx} has no negative content to enhance.")
            
           
            row["positive"] = enhanced_positive
            row["negative"] = enhanced_negative
            writer.writerow(row)
            print(f"Review {idx} written to output.\n")

if __name__ == "__main__":
    main()