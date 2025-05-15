
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
import random
import json
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests
from pydantic import BaseModel

class review(BaseModel):
    review:str
    sentiment:str

    client =genai.GenerativeModel("gemini-2.0-flash")
    response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="",
    config={
        "response_mime_type": "application/json",
        "response_schema": list[review],
    },
)
# Use the response as a JSON string.
    print(response.text)

# Use instantiated objects.
    my_recipes: list[reviews] = response.parsed




load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("API key for Gemini is missing. Please set GEMINI_API_KEY in the .env file.")


genai.configure(api_key=api_key)


gemini_model = genai.GenerativeModel("gemini-2.0-flash")


@retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=4, max=30),  
    retry=retry_if_exception_type((requests.exceptions.HTTPError, Exception)), 
    reraise=True
)
def call_gemini_with_retry(prompt):
    """Call Gemini API with retry logic for rate limits"""
    try:
        
        time.sleep(random.uniform(1, 2))
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        
        if "429" in str(e) and "quota" in str(e).lower():
            print(f"Rate limit hit. Waiting before retry... ({str(e)[:100]}...)")
            
            time.sleep(random.uniform(20, 30))
            raise e  
        else:
            return f"Error generating review: {str(e)}"

def generate_review_prompt(pname, set_phrases, set_number, previous_reviews=None):
    """
    Generates a personalized review prompt for the Gemini model.
    
    Args:
        pname: Project name
        set_phrases: Phrases from the current set
        set_number: The set number being processed
        previous_reviews: List of reviews already generated for this project
    """
    if not set_phrases or pd.isna(set_phrases) or set_phrases == "":
        return None
    
    
    phrases = set_phrases.split('\n') if isinstance(set_phrases, str) else []
    phrases = [p.strip() for p in phrases if p.strip()]
    
    
    positive_phrases = [p.replace(" (positive)", "") for p in phrases if "(positive)" in p]
    negative_phrases = [p.replace(" (negative)", "") for p in phrases if "(negative)" in p]
    
    
    neutral_phrases = [p for p in phrases if "(positive)" not in p and "(negative)" not in p]
    
    
    context = ""
    if previous_reviews and len(previous_reviews) > 0:
        context = "Previous reviews for this project mentioned: " + "; ".join(previous_reviews)
        context += ". Your review should be consistent with these points but provide a fresh perspective."
    
    prompt = f"""

    You are the resident of "{pname}" society . Your task is to generate the review based on Set {set_number} feedback.
    
    Write 2 paragraphs from a resident's perspective about their experience living in this society. 
    
    Include these points from Set {set_number}:
    {', '.join(phrases) if phrases else 'No specific points mentioned.'}
    
    {'Positive aspects to emphasize: ' + ', '.join(positive_phrases) if positive_phrases else ''}
    {'Points of concern: ' + ', '.join(negative_phrases) if negative_phrases else ''}
    {'Other aspects to mention: ' + ', '.join(neutral_phrases) if neutral_phrases else ''}
    
    {context}
    
    Important guidelines:
    1. Sound like a real resident - conversational, not promotional
    2. Be specific and personal in your observations, Don't use superatives or exaggerate
    3. Keep the review balanced and authentic
    4. Divide the reviews into two classes - Positives and Negatives
    5. Use simple language and avoid jargon.
    Length: 200-300 characters maximum for each review.
    6.Its okay to make grammatical mistakes in the review.
    7. Separate the reviews into two classes - Positives and Negatives
    
    Use these given example reviews as reference . Use them to understand the tone and style of the review:
    Positive:
    It's great that they offer amenities such as a gym, badminton court, and swimming pool, and when they are in use, they appear to be well maintained. I appreciate the overall environment and the fact that it feels like a good place to live. The layout of the 2 and 3 BHK flats is also something that people find appealing
    The infrastructure and landscaping create a beautiful atmosphere. The clubhouse, swimming pool, and fitness center cater to my needs. I appreciate the friendly community and proactive management, making it a safe place for families.I truly enjoy living in Jaipurias Sunrise Greens Premium.\
    Jubilee Hillview is a luxurious residential paradise with its breathtaking views and modern amenities. its just so beautiful. The club house for socializing it privides various activities for the members it's a perfect haven. The sports ground is a bonus for fitness enthusiasts. Good safety and security gives residence a peace of mind. The social maintenance is also very vibrant. A truly desirable place to live
    I enjoy the vibrant community and the good food options nearby. The ample parking space is also a significant plus for me. Society is located in an excellent locality, Koparkhairne sector 15, with main roads facing near Gulab Sons Dairy, IDBI bank, HDFC Bank, and the local market
    The location is fantastic, with easy access to schools, hospitals, and shopping areas. The community is well-maintained, and the staff is friendly and helpful. I love the spacious apartments and the beautiful landscaping. The amenities like the gym and swimming pool are a great bonus. Overall, it's a wonderful place to live.


    Negative:
    Accessing cars or even locating a nearby bus stop requires quite a walk, making it seem almost essential to have your own vehicle. Additionally, it's somewhat troubling to learn that the clubhouse and swimming pool have been closed for an extended period, along with the problem of recycled water in the toilets creating an unpleasant odor.
    I am disappointed with the ongoing issues like seepage and electricity problems. Despite the high maintenance charges, the management often falls short. While the location is great, I feel more effort is needed to resolve these concerns and enhance our living experience.
    Ongoing Construction near by soicety disrupts the peaceful environment at times. Additionally, improved safety measures around the community would enhance residents' peace of mind
    Despite it's stunning views, the amenities were poorly maintained. The clubhouse was often closed and the sports ground was neglected. Safety and security measures often lack, and social events were nonexistend. the luxurious feel was missing 
    The ageing condition of the building and the occasional rude behaviour from the security staff have taken away from what could have been a much better living experience. These issues make day-to-day life here less comfortable and negatively impact my overall living experience.
    Honestly, the experience was mostly positive. However, did encounter some security personnel who came across as arrogant, and overall, the staff and security weren't always good, which was a bit disappointing
    Not overly impressed. It's good, but it doesn't quite live up to the "heaven" description. It's a bit of an overstatement in my opinion.




Give Ratings according to reviews generated. The ratings Should match with the reviews generated.
   
Society Management Rating: Assign a rating (out of 5) for society management. 
Green Area Rating: Assign a rating (out of 5) for the green areas and parks. 
Amenities Rating: Assign a rating (out of 5) for the society's amenities. 
Connectivity Rating: Assign a rating (out of 5) for society connectivity and commute. 
Construction Rating: Assign a rating (out of 5) for society construction quality.
Use whole numbers for all ratings (1-5). 
If a specific rating cannot be determined from the reviews, use "5"

    """
    return prompt

def load_checkpoint():
    """Load progress from checkpoint file if it exists"""
    checkpoint_file = "review_generation_checkpoint.json"
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
                print(f"Loaded checkpoint: {len(checkpoint['completed_projects'])} projects already processed")
                return checkpoint
        except Exception as e:
            print(f"Error loading checkpoint: {e}")
    
    
    return {
        "completed_projects": {},
        "call_count": 0,
        "last_updated": datetime.now().isoformat()
    }

def save_checkpoint(checkpoint, final_reviews):
    """Save current progress to checkpoint file"""
    checkpoint_file = "review_generation_checkpoint.json"
    checkpoint["last_updated"] = datetime.now().isoformat()
    
    
    temp_output = "gemini_reviews_in_progress.csv"
    pd.DataFrame(final_reviews).to_csv(temp_output, index=False)
    
    try:
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f)
        print(f"✓ Checkpoint saved: {len(checkpoint['completed_projects'])} projects")
    except Exception as e:
        print(f"Error saving checkpoint: {e}")

def main():
    # API limits
    DAILY_LIMIT = 1500
    MINUTE_LIMIT = 12  
    
    try:
        
        df = pd.read_csv("output_sets.csv")
    except FileNotFoundError:
        raise FileNotFoundError("The file 'output_sets.csv' was not found. Please check the file path.")
    
   
    set_columns = [col for col in df.columns if col.startswith("Set ")]
    max_sets = len(set_columns)
    
    print(f"Found {max_sets} set columns: {set_columns}")
    
    
    checkpoint = load_checkpoint()
    call_count = checkpoint.get("call_count", 0)
    completed_projects = checkpoint.get("completed_projects", {})
    
    # Initialize a list to store the final reviews
    final_reviews = []
    
    # Load any previously saved reviews if they exist
    temp_output = "gemini_reviews_in_progress.csv"
    if os.path.exists(temp_output):
        try:
            previous_df = pd.read_csv(temp_output)
            final_reviews = previous_df.to_dict('records')
            print(f"Loaded {len(final_reviews)} previously generated reviews")
        except Exception as e:
            print(f"Could not load previous reviews: {e}")
    
    print("\nStarting review generation with rate limit handling...")
    print(f"API Limits - Daily: {DAILY_LIMIT}, Per Minute: {MINUTE_LIMIT}")
    
    # Process each row (project) in the dataframe
    for idx, (_, row) in enumerate(df.iterrows()):
        xid = str(row["xid"])  # Convert to string for consistent dict keys
        pname = row["Project name"]
        
        # Skip projects that are already complete
        if xid in completed_projects:
            print(f"Skipping already completed project: {pname} (ID: {xid})")
            
            # Make sure it's in our final_reviews list
            if not any(r["xid"] == xid for r in final_reviews):
                final_reviews.append({
                    "xid": xid,
                    "Project name": pname,
                    "Review 1": completed_projects[xid].get("Review 1", ""),
                    "Review 2": completed_projects[xid].get("Review 2", ""),
                    "Review 3": completed_projects[xid].get("Review 3", ""),
                    "Review 4": completed_projects[xid].get("Review 4", "")
                })
            continue
        
        print(f"\nProcessing project {idx+1}/{len(df)}: {pname} (ID: {xid})")
        
        # Check if we should continue based on remaining calls
        if call_count >= DAILY_LIMIT - 10:  # Leave buffer of 10 calls
            print(f"⚠️ Approaching daily limit ({call_count}/{DAILY_LIMIT}). Saving progress and exiting.")
            break
        
        project_reviews = []
        
        # Process each set for this project
        for set_num in range(1, 5):  # Assuming up to 4 sets
            set_col = f"Set {set_num}"
            
            # Skip if this set column doesn't exist
            if set_col not in df.columns:
                project_reviews.append("")
                continue
            
            # Get phrases for this set
            set_phrases = row.get(set_col, "")
            
            # Skip empty sets
            if pd.isna(set_phrases) or set_phrases == "":
                project_reviews.append("")
                continue
            
            # Generate the review prompt, passing previous reviews for context
            prompt = generate_review_prompt(
                pname, 
                set_phrases, 
                set_num, 
                [r for r in project_reviews if r and not r.startswith("Failed") and not r.startswith("Error")]
            )
            
            if not prompt:
                project_reviews.append("")
                continue
                
            # Update call count
            call_count += 1
            
            # Check for minute rate limit (15 per minute)
            if call_count % MINUTE_LIMIT == 0:
                print(f"Reached {MINUTE_LIMIT} calls, pausing for 65 seconds to respect per-minute rate limit...")
                time.sleep(65)  # Wait a bit more than a minute to be safe
            
            # Generate the review using Gemini with retry logic
            try:
                print(f"Generating review for {pname} - Set {set_num}...")
                review_text = call_gemini_with_retry(prompt)
                project_reviews.append(review_text)
                print(f"✓ Successfully generated review for {pname} - Set {set_num}")
                
                # Update checkpoint after each successful review
                checkpoint["call_count"] = call_count
                
                # Add delay between project sets to avoid hitting rate limits
                time.sleep(3)  # 3 second pause between set generations
            except Exception as e:
                error_msg = f"Failed after retries for {pname} (Set {set_num}): {str(e)[:100]}..."
                project_reviews.append(error_msg)
                print(error_msg)
                
                
                print("Cooling down for 25 seconds before continuing...")
                time.sleep(25)
        
        
        while len(project_reviews) < 4:
            project_reviews.append("")
        
        
        project_data = {
            "xid": xid,
            "Project name": pname,
            "Review 1": project_reviews[0],
            "Review 2": project_reviews[1],
            "Review 3": project_reviews[2],
            "Review 4": project_reviews[3]
        }
        
        final_reviews.append(project_data)
        
        
        completed_projects[xid] = {
            "Review 1": project_reviews[0],
            "Review 2": project_reviews[1],
            "Review 3": project_reviews[2],
            "Review 4": project_reviews[3]
        }
        
        
        if (idx + 1) % 3 == 0:
            checkpoint["completed_projects"] = completed_projects
            checkpoint["call_count"] = call_count
            save_checkpoint(checkpoint, final_reviews)
    
    
    output_file = "gemini_multiple_reviews.csv"
    pd.DataFrame(final_reviews).to_csv(output_file, index=False)
    
    print(f"\n Gemini reviews saved to {output_file}")
    print(f"Generated a total of {call_count} reviews")
    print(f"Completed {len(completed_projects)} out of {len(df)} projects")
    
    
    with open("review_generation_status.txt", "w") as f:
        f.write(f"Generated on: {datetime.now()}\n")
        f.write(f"Completed: {len(completed_projects)} out of {len(df)} projects\n")
        f.write(f"API calls made: {call_count}\n")
        f.write(f"Projects remaining: {len(df) - len(completed_projects)}\n")
        
        if len(completed_projects) < len(df):
            f.write("\nTo continue generation, run the script again.\n")
            f.write("It will automatically skip already processed projects.\n")
        
    print("Status file created: review_generation_status.txt")
    
    
    checkpoint["completed_projects"] = completed_projects
    checkpoint["call_count"] = call_count
    save_checkpoint(checkpoint, final_reviews)

if __name__ == "__main__":
    main()




















































































