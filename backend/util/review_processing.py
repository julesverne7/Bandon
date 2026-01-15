import pandas as pd
from openai import OpenAI
import json
import time
from datetime import datetime

# Initialize OpenAI client
client = OpenAI(api_key='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')  # Replace with your actual API key

# Define the categories
CATEGORIES = [
    'cleanliness',
    'crowding',
    'customer_service',
    'equipment_quality',
    'membership_billing',
    'price',
    'staff_attitude'
]

def analyze_review(review_text, place_name):
    """
    Send a review to ChatGPT and get structured categorized feedback
    """
    prompt = f"""Analyze this gym review and extract specific mentions for each category.
For each category, identify:
1. Specific fragments/quotes from the review that relate to that category
2. Sentiment (positive/negative/neutral)
3. Intensity (1-5, where 5 is very strong sentiment)

Categories to analyze:
- cleanliness
- crowding
- customer_service
- equipment_quality
- membership_billing
- price
- staff_attitude

Review: "{review_text}"

Return your analysis in this exact JSON format:
{{
  "cleanliness": {{"fragments": ["quote1", "quote2"], "sentiment": "negative", "intensity": 3}},
  "crowding": {{"fragments": [], "sentiment": "neutral", "intensity": 0}},
  ...
}}

If a category is not mentioned, use empty fragments array, "neutral" sentiment, and 0 intensity.
IMPORTANT: Return ONLY the JSON object, no additional text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-4o" for better quality
            messages=[
                {"role": "system", "content": "You are an expert at analyzing customer reviews and extracting structured feedback. Always return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )

        # Parse the JSON response
        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        print(f"Error analyzing review: {e}")
        return None

def process_reviews(input_file, output_file):
    """
    Process all reviews and save results to Excel
    """
    # Read the Excel file
    print(f"Reading {input_file}...")
    df = pd.read_excel(input_file)

    print(f"Found {len(df)} reviews to process")

    # Prepare columns for results
    result_columns = {}
    for category in CATEGORIES:
        result_columns[f'{category}_fragments'] = []
        result_columns[f'{category}_sentiment'] = []
        result_columns[f'{category}_intensity'] = []

    # Add a processing status column
    result_columns['processing_status'] = []

    # Process each review
    for idx, row in df.iterrows():
        print(f"\nProcessing review {idx + 1}/{len(df)} - {row['PLACE NAME']}")

        review_text = row['TEXT']
        place_name = row['PLACE NAME']

        # Analyze the review
        analysis = analyze_review(review_text, place_name)

        if analysis:
            # Extract data for each category
            for category in CATEGORIES:
                cat_data = analysis.get(category, {})
                fragments = cat_data.get('fragments', [])
                sentiment = cat_data.get('sentiment', 'neutral')
                intensity = cat_data.get('intensity', 0)

                # Join fragments with ' | ' separator
                result_columns[f'{category}_fragments'].append(' | '.join(fragments) if fragments else '')
                result_columns[f'{category}_sentiment'].append(sentiment)
                result_columns[f'{category}_intensity'].append(intensity)

            result_columns['processing_status'].append('success')
        else:
            # If analysis failed, fill with empty values
            for category in CATEGORIES:
                result_columns[f'{category}_fragments'].append('')
                result_columns[f'{category}_sentiment'].append('error')
                result_columns[f'{category}_intensity'].append(0)

            result_columns['processing_status'].append('failed')

        # Add a small delay to avoid rate limits
        time.sleep(0.5)

        # Save progress every 10 reviews
        if (idx + 1) % 10 == 0:
            print(f"Saving progress at review {idx + 1}...")
            temp_df = df.copy()
            for col_name, col_data in result_columns.items():
                temp_df[col_name] = col_data + [''] * (len(df) - len(col_data))
            temp_df.to_excel(f'{output_file}', index=False)

    # Add all result columns to the dataframe
    for col_name, col_data in result_columns.items():
        df[col_name] = col_data

    # Save final results
    print(f"\nSaving final results to {output_file}...")
    df.to_excel(output_file, index=False)
    print("Done!")

    return df


def print_summary_statistics(results_df):   
    """
    Print summary statistics of the processed reviews
    """
    # Print summary statistics
    print("\n=== SUMMARY STATISTICS ===")
    print(f"Total reviews processed: {len(results_df)}")
    print(f"Successful: {sum(results_df['processing_status'] == 'success')}")
    print(f"Failed: {sum(results_df['processing_status'] == 'failed')}")

    # Show sentiment breakdown by category
    print("\n=== SENTIMENT BREAKDOWN BY CATEGORY ===")
    for category in CATEGORIES:
        sentiment_col = f'{category}_sentiment'
        print(f"\n{category.upper()}:")
        print(results_df[sentiment_col].value_counts()) 


# Run this to call the processing function and print summary statistics
def start_processing(input_file, output_file):
    results_df = process_reviews(input_file, output_file)  
    # print_summary_statistics(results_df)
    return results_df


# Main execution
# if __name__ == "__main__":
#     input_file = "/content/sample_data/Bandon Locations_Full Data_1.xlsx"
#     output_file = f"Analyzed_Reviews_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

#     # Process the reviews
#     results_df = process_reviews(input_file, output_file) 
#     # Print summary statistics
#     print_summary_statistics(results_df)