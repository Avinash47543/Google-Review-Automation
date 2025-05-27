
import sys
from pydantic import BaseModel
from dotenv import load_dotenv
from google.generativeai import types
import google.generativeai as genai
import os, random
import json
import time
import pandas as pd
from google import genai
from google.genai import types

class Review(BaseModel):
    positive_review: str
    negative_review: str
    society_management:str
    green_area:str
    amenities:str
    connectivity:str
    construction:str
    overall: str
    duration_of_stay: str

class GeminiReviewGenerator:
    __model_name = 'gemini-2.0-flash'
    __prompt_file_path = 'gemini_ai_prompts.json'

    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("API key for Gemini is missing. Please set GEMINI_API_KEY in the .env file.")
        self.__client = genai.Client(api_key=api_key)

    def __getPromptFromFile(self, type: str) -> str:
        with open(GeminiReviewGenerator.__prompt_file_path, 'r') as file:
            data = file.read()
        parsed_data = json.loads(data)
        prompt = parsed_data.get(type)
        return prompt

    def generate_review(self, project_info_df, project_name, set_number):
        try:
            time.sleep(random.uniform(0.5, 1.5))
            prompt = self.__getPromptFromFile('system_instruction_review_generator')
            print(f"Sending payload to Gemini for {project_name} (Set {set_number}):")

            generation_config = types.GenerateContentConfig(
                temperature=1.2,
                top_p=0.85,
                system_instruction=[
                    types.Part.from_text(text=prompt),
                ],
                response_mime_type='application/json',
                response_schema=Review
            )

            contents = [types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=project_info_df.to_json(orient='records')),
                ],
            )]

            try:
                model_reply = self.__client.models.generate_content(
                    model=self.__model_name,
                    contents=contents,
                    config=generation_config
                )
            except Exception as e:
                print(f'Gemini AI execution threw an exception: {e}')
                return None

            review_json = model_reply.text
            print(f"Generated review JSON: {review_json}")
            review_data = json.loads(review_json)

            if "overall" not in review_data:
                fields = ["society_management", "green_area", "amenities", "connectivity", "construction"]
                if all(review_data.get(field) in [None, "", "NA"] for field in fields):
                    review_data["overall"] = "NA"
                else:
                    rating_values = [review_data.get(field) for field in fields]
                    valid_ratings = [r for r in rating_values if isinstance(r, (int, float))]
                    review_data["overall"] = round(sum(valid_ratings) / len(valid_ratings)) if valid_ratings else "NA"

            for field in ["society_management", "green_area", "amenities", "connectivity", "construction"]:
                if review_data.get(field) is None:
                    review_data[field] = "NA"

            if "duration_of_stay" not in review_data:
                review_data["duration_of_stay"] = project_info_df['duration_of_stay'].iloc[0] if 'duration_of_stay' in project_info_df.columns else "NA"

            return json.dumps(review_data)

        except Exception as e:
            if "429" in str(e) and "quota" in str(e).lower():
                print(f"Rate limit hit. Retrying... ({str(e)[:100]})")
                time.sleep(10)
                return self.generate_review(project_info_df, project_name, set_number)
            else:
                return json.dumps({
                    "positive_review": f"Error: {str(e)[:100]}",
                    "negative_review": "",
                    "society_management": "NA",
                    "green_area": "NA",
                    "amenities": "NA",
                    "connectivity": "NA",
                    "construction": "NA",
                    "overall": "NA",
                    "duration_of_stay": "NA"
                })

def prepare_project_info_df(pname, set_phrases, duration, set_number):
    if not set_phrases or pd.isna(set_phrases) or set_phrases == "":
        return None

    phrases = set_phrases.split('\n') if isinstance(set_phrases, str) else []
    phrases = [p.strip() for p in phrases if p.strip()]

    positive_phrases = [p.replace(" (positive)", "") for p in phrases if "(positive)" in p]
    negative_phrases = [p.replace(" (negative)", "") for p in phrases if "(negative)" in p]
    neutral_phrases = [p for p in phrases if "(positive)" not in p and "(negative)" not in p]

    data = {
        'project_name': [pname],
        'positive_phrases': [positive_phrases],
        'negative_phrases': [negative_phrases],
        'neutral_phrases':  [neutral_phrases],
        'duration_of_stay': [duration]
    }

    return pd.DataFrame(data)

def main():
    try:
        df = pd.read_csv("output_sets.csv")
        print(f"Loaded {len(df)} projects from output_sets.csv")
    except FileNotFoundError:
        raise FileNotFoundError("The file 'output_sets.csv' was not found. Please check the file path.")

    set_columns = [col for col in df.columns if col.startswith("Set ")]
    max_sets = len(set_columns)
    print(f"Found {max_sets} set columns: {set_columns}")

    final_reviews = []
    review_generator = GeminiReviewGenerator()

    for idx, (_, row) in enumerate(df.iterrows()):
        xid = row["xid"]
        pname = row["Project name"]
        print(f"\nProcessing project {idx+1}/{len(df)}: {pname} (ID: {xid})")

        project_reviews = []

        for set_num in range(1, max_sets + 1):
            set_col = f"Set {set_num}"
            duration_col = f"How Long do you stay here {set_num}"

            if set_col not in df.columns:
                project_reviews.append("")
                continue

            set_phrases = row.get(set_col, "")
            duration = row.get(duration_col, "NA")

            if pd.isna(set_phrases) or set_phrases == "":
                project_reviews.append("")
                continue

            project_info_df = prepare_project_info_df(pname, set_phrases, duration, set_num)
            if project_info_df is None or project_info_df.empty:
                project_reviews.append("")
                continue

            try:
                print(f"Generating review for {pname} - Set {set_num}...")
                review_json = review_generator.generate_review(project_info_df, pname, set_num)
                project_reviews.append(review_json)
                print(f"✓ Success: {pname} - Set {set_num}")
            except Exception as e:
                error_json = json.dumps({
                    "positive_review": f"Failed: {str(e)[:100]}",
                    "negative_review": "",
                    "society_management": "NA",
                    "green_area": "NA",
                    "amenities": "NA",
                    "connectivity": "NA",
                    "construction": "NA",
                    "overall": "NA",
                    "duration_of_stay": "NA"
                })
                project_reviews.append(error_json)
                print(f"Failed for {pname} (Set {set_num}): {str(e)[:100]}")

        project_data = {
            "xid": xid,
            "Project name": pname
        }

        for i, review in enumerate(project_reviews[:], 1):
            project_data[f"Review {i}"] = review

        final_reviews.append(project_data)

    output_df = pd.DataFrame(final_reviews)
    output_df.to_csv("gemini_structured_reviews.csv", index=False)
    print(f"\nAll done! Generated reviews saved to gemini_structured_reviews.csv")
    print(f"Processed {len(final_reviews)} projects")

if __name__ == "__main__":
    main()
