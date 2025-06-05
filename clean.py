
import pandas as pd
import json

df = pd.read_csv('structured_reviews.csv')

new_rows = []

for _, row in df.iterrows():
    xid = row['xid']
    project_name = row['Project name']
    
    
    for col in df.columns:
        if 'Review' in col and pd.notna(row[col]):
            try:
                # Parse JSON string from the review column
                review_data = json.loads(row[col])
                
                positive = review_data.get('positive_review', 'N.A.')
                negative = review_data.get('negative_review', 'N.A.')
                duration = review_data.get('duration_of_stay', 'N.A.')
                
                society_management = review_data.get('society_management', 'N.A.')
                green_area = review_data.get('green_area', 'N.A.')
                amenities = review_data.get('amenities', 'N.A.')
                connectivity = review_data.get('connectivity', 'N.A.')
                construction = review_data.get('construction', 'N.A.')
                overall = review_data.get('overall', 'N.A.')
                
                new_rows.append({
                    'xid': xid,
                    'project_name': project_name,
                    'duration_of_stay': duration,
                    'positive': positive,
                    'negative': negative,
                    'society_management': society_management,
                    'green_area': green_area,
                    'amenities': amenities,
                    'connectivity': connectivity,
                    'construction': construction,
                    'overall_rating': overall
                })
            except (json.JSONDecodeError, AttributeError) as e:
                print(f"Skipping invalid JSON in {col} for xid {xid}: {e}")
                continue

new_df = pd.DataFrame(new_rows)
new_df.to_csv('processed_reviews.csv', index=False)

print(f"Processed {len(new_rows)} reviews from {len(df)} projects.")
print("New CSV created as 'processed_reviews.csv'")
