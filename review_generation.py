
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
from collections import deque
from datetime import datetime

class Review(BaseModel):
    positive_review: str
    negative_review: str
    society_management: str
    green_area: str
    amenities: str
    connectivity: str
    construction: str
    overall: str
    duration_of_stay: str

class RateLimiter:
    def __init__(self, max_requests_per_minute=15, max_requests_per_day=1500):
        self.max_rpm = max_requests_per_minute
        self.max_daily = max_requests_per_day
        self.request_times = deque()
        self.daily_count = 0
        self.last_day_check = datetime.now().day

    def check_limit(self):
        now = datetime.now()
        if now.day != self.last_day_check:
            self.daily_count = 0
            self.last_day_check = now.day
        if self.daily_count >= self.max_daily:
            raise Exception("Daily request limit reached")
        while self.request_times and (now - self.request_times[0]).total_seconds() > 60:
            self.request_times.popleft()
        if len(self.request_times) >= self.max_rpm:
            time_to_wait = 60 - (now - self.request_times[0]).total_seconds()
            time.sleep(max(time_to_wait, 0))
            now = datetime.now()
        return True

    def record_request(self):
        now = datetime.now()
        self.request_times.append(now)
        self.daily_count += 1

class GeminiReviewGenerator:
    __model_name = 'gemini-2.0-flash'
    __prompt_file_path = 'gemini_ai_prompts.json'

    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("API key for Gemini is missing. Please set GEMINI_API_KEY in the .env file.")
        self.__client = genai.Client(api_key=api_key)
        self.rate_limiter = RateLimiter()
        # Changed to store chats by project_name AND set_number combination
        self.project_chats = {}  

    def __getPromptFromFile(self, type: str) -> str:
        with open(GeminiReviewGenerator.__prompt_file_path, 'r') as file:
            data = file.read()
        parsed_data = json.loads(data)
        return parsed_data.get(type)

    def _get_system_instruction_for_set(self, set_number):
        """
        Get the appropriate system instruction based on set number
        """
        # Define mapping of set numbers to system instruction keys
        instruction_mapping = {
            1: 'system_instruction_review_generator_resident',
            2: 'system_instruction_review_generator_family',
            3: 'system_instruction_review_generator_female',
            4: 'system_instruction_review_generator_old'
        }
        
        # Get the instruction key for the set number, default to resident if not found
        instruction_key = instruction_mapping.get(set_number, 'system_instruction_review_generator_resident')
        return self.__getPromptFromFile(instruction_key)

    def _initialize_chat_for_project_set(self, project_name, set_number):
        """
        Initialize a chat session for a specific project and set combination
        """
        # Get the appropriate system instruction for this set
        prompt = self._get_system_instruction_for_set(set_number)
        print(prompt)
        
        # Create unique key for project-set combination
        chat_key = f"{project_name}_set_{set_number}"
        
        chat = self.__client.chats.create(
            model=self.__model_name,
            config=types.GenerateContentConfig(
                temperature=0.8,
                top_p=0.7,
                system_instruction=[types.Part.from_text(text=prompt)],
                response_mime_type='application/json',
                response_schema=Review
            )
        )
        
        # Send initial context message
        chat.send_message(
            f"I will be generating a review for the project '{project_name}' (Set {set_number}). "
            f"Please generate a review that matches the persona defined in the system instruction."
        )
        
        self.project_chats[chat_key] = chat
        print(f"Initialized chat session for project: {project_name} - Set {set_number}")

    def generate_review(self, project_info_df, project_name, set_number):
        print(f"Generating review for project '{project_name}' - Set {set_number}...")
        print(project_info_df)
        
        if not self.rate_limiter.check_limit():
            time.sleep(10)
            return self.generate_review(project_info_df, project_name, set_number)
        
        self.rate_limiter.record_request()
        time.sleep(random.uniform(0.5, 1.5))

        # Create unique key for project-set combination
        chat_key = f"{project_name}_set_{set_number}"
        
        # Initialize chat if it doesn't exist for this project-set combination
        if chat_key not in self.project_chats:
            self._initialize_chat_for_project_set(project_name, set_number)

        chat = self.project_chats.get(chat_key)
        if not chat:
            return None

        message_content = f"""
        Generate a detailed review for project '{project_name}' based on the following data:
        {project_info_df.to_json(orient='records')}
        
        This is Set {set_number}. Please ensure the review reflects the perspective and style 
        appropriate for this set while maintaining uniqueness.
        """

        try:
            response = chat.send_message(message_content)
            review_json = response.text
        except Exception as e:
            print(f'Gemini AI Chat execution threw an exception: {e}')
            # Re-initialize chat on error
            self._initialize_chat_for_project_set(project_name, set_number)
            chat = self.project_chats.get(chat_key)
            response = chat.send_message(message_content) if chat else None
            print(response)
            review_json = response.text if response else None

        if not review_json:
            return None

        review_data = json.loads(review_json)

        # Handle missing overall rating
        if "overall" not in review_data:
            fields = ["society_management", "green_area", "amenities", "connectivity", "construction"]
            if all(review_data.get(field) in [None, "", "NA"] for field in fields):
                review_data["overall"] = "NA"
            else:
                valid_ratings = [review_data.get(f) for f in fields if isinstance(review_data.get(f), (int, float))]
                review_data["overall"] = round(sum(valid_ratings)/len(valid_ratings)) if valid_ratings else "NA"

        # Handle missing fields
        for field in ["society_management", "green_area", "amenities", "connectivity", "construction"]:
            if review_data.get(field) is None:
                review_data[field] = "NA"

        # Handle duration of stay
        if "duration_of_stay" not in review_data:
            review_data["duration_of_stay"] = project_info_df['duration_of_stay'].iloc[0] if 'duration_of_stay' in project_info_df.columns else "NA"

        return json.dumps(review_data)

    def get_chat_history(self, project_name, set_number):
        """
        Get chat history for a specific project and set combination
        """
        chat_key = f"{project_name}_set_{set_number}"
        chat = self.project_chats.get(chat_key)
        if not chat:
            return []
        return [
            {'role': msg.role, 'text': msg.parts[0].text if msg.parts else ""}
            for msg in chat.get_history()
        ]

def prepare_project_info_df(pname, set_phrases, duration, set_number):
    if not set_phrases or pd.isna(set_phrases) or set_phrases == "":
        return None
    phrases = [p.strip() for p in set_phrases.split('\n') if p.strip()]
    positive = [p.replace(" (positive)", "") for p in phrases if "(positive)" in p]
    negative = [p.replace(" (negative)", "") for p in phrases if "(negative)" in p]
    neutral = [p for p in phrases if "(positive)" not in p and "(negative)" not in p]
    return pd.DataFrame({
        'project_name': [pname],
        'positive_phrases': [positive],
        'negative_phrases': [negative],
        'neutral_phrases': [neutral],
        'duration_of_stay': [duration],
        'set_number': [set_number]  # Added set_number to the dataframe
    })

def main():
    df = pd.read_csv("output_sets.csv")
    set_columns = [col for col in df.columns if col.startswith("Set ")]
    output_file = "structured_reviews.csv"
    
    # Create output file if it doesn't exist
    if not os.path.exists(output_file):
        pd.DataFrame(columns=["xid", "Project name"] + [f"Review {i}" for i in range(1, len(set_columns)+1)]).to_csv(output_file, index=False)
    
    gen = GeminiReviewGenerator()

    for idx, (_, row) in enumerate(df.iterrows()):
        xid, pname = row["xid"], row["Project name"]
        print(f"\nProcessing project {idx+1}/{len(df)}: {pname} (ID: {xid})")
        pdata = {"xid": xid, "Project name": pname}

        # Process each set with different system instructions
        for s in range(1, len(set_columns)+1):
            scol, dcol = f"Set {s}", f"How Long do you stay here {s}"
            
            if scol not in row or pd.isna(row[scol]) or row[scol] == "":
                pdata[f"Review {s}"] = ""
                continue
            
            pdf = prepare_project_info_df(pname, row[scol], row.get(dcol, "NA"), s)
            if pdf is None:
                pdata[f"Review {s}"] = ""
                continue
                
            try:
                print(f"Generating review for {pname} - Set {s} (using system instruction for set {s})...")
                rjson = gen.generate_review(pdf, pname, s)
                pdata[f"Review {s}"] = rjson
                print(f"✓ Success: {pname} - Set {s}")
            except Exception as e:
                err_json = json.dumps({
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
                pdata[f"Review {s}"] = err_json
                print(f"Failed for {pname} (Set {s}): {str(e)[:100]}")

        # Save data for this project
        pd.DataFrame([pdata]).to_csv(output_file, mode='a', header=False, index=False)
        print(f"Saved data for {pname} to {output_file}")

    print(f"\nAll done! Generated reviews saved to {output_file}")
    print(f"Processed {len(df)} projects with different system instructions for each set")

if __name__ == "__main__":
    main()