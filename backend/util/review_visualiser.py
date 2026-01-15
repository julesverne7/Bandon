# pip install matplotlib seaborn numpy 
import os
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend for non-GUI rendering 
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
from backend.settings import MEDIA_ROOT
from .review_processing import CATEGORIES  
import plotly.express as px   

# Set style for better-looking plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_analyzed_data(file_path):
    """Load the analyzed Excel file"""
    df = pd.read_excel(file_path)
    return df

def calculate_negative_percentage(df):
    """
    Calculate percentage of negative mentions by location and category
    """
    locations = df['PLACE ADDRESS'].unique()

    # Create a matrix for the heatmap
    heatmap_data = []
    location_names = []

    for location in locations:
        location_df = df[df['PLACE ADDRESS'] == location]
        row_data = []

        # Extract city name from address for cleaner labels
        city = location.split(',')[1].strip() if ',' in location else location[:30]
        location_names.append(city)

        for category in CATEGORIES:
            sentiment_col = f'{category}_sentiment'

            # Count mentions of this category
            total_mentions = (location_df[sentiment_col] != 'neutral').sum()
            negative_mentions = (location_df[sentiment_col] == 'negative').sum()

            # Calculate percentage (avoid division by zero)
            if total_mentions > 0:
                negative_pct = (negative_mentions / total_mentions) * 100
            else:
                negative_pct = 0

            row_data.append(negative_pct)

        heatmap_data.append(row_data)

    return np.array(heatmap_data), location_names

def calculate_mention_frequency(df):
    """
    Calculate how often each category is mentioned (regardless of sentiment)
    """
    locations = df['PLACE ADDRESS'].unique()

    frequency_data = []
    location_names = []

    for location in locations:
        location_df = df[df['PLACE ADDRESS'] == location]
        row_data = []

        city = location.split(',')[1].strip() if ',' in location else location[:30]
        location_names.append(city)

        total_reviews = len(location_df)

        for category in CATEGORIES:
            sentiment_col = f'{category}_sentiment'

            # Count non-neutral mentions
            mentions = (location_df[sentiment_col] != 'neutral').sum()
            mention_pct = (mentions / total_reviews) * 100

            row_data.append(mention_pct)

        frequency_data.append(row_data)

    return np.array(frequency_data), location_names

def calculate_weighted_score(df):
    """
    Calculate weighted negative score (percentage * intensity)
    """
    locations = df['PLACE ADDRESS'].unique()

    weighted_data = []
    location_names = []

    for location in locations:
        location_df = df[df['PLACE ADDRESS'] == location]
        row_data = []

        city = location.split(',')[1].strip() if ',' in location else location[:30]
        location_names.append(city)

        for category in CATEGORIES:
            sentiment_col = f'{category}_sentiment'
            intensity_col = f'{category}_intensity'

            # Get negative reviews with their intensities
            negative_mask = location_df[sentiment_col] == 'negative'
            negative_intensities = location_df[negative_mask][intensity_col]

            # Calculate weighted score
            if len(negative_intensities) > 0:
                avg_intensity = negative_intensities.mean()
                negative_count = len(negative_intensities)
                total_reviews = len(location_df)

                # Weighted score: (% negative) * (avg intensity)
                weighted_score = (negative_count / total_reviews * 100) * (avg_intensity / 5)
            else:
                weighted_score = 0

            row_data.append(weighted_score)

        weighted_data.append(row_data)

    return np.array(weighted_data), location_names 

def create_category_breakdown(df, category, output_file):
    """
    Create a detailed interactive breakdown for a specific category across locations using Plotly.
    """
     
    locations = df['PLACE ADDRESS'].unique()
    location_data = []

    for location in locations: 
        location_df = df[df['PLACE ADDRESS'] == location]
         
        city = location.split(',')[1].strip() if ',' in location else location[:30]

        sentiment_col = f'{category}_sentiment'
         
        if sentiment_col not in df.columns:
            continue

        positive = (location_df[sentiment_col] == 'positive').sum()
        negative = (location_df[sentiment_col] == 'negative').sum()
        neutral = (location_df[sentiment_col] == 'neutral').sum()

        location_data.append({
            'Location': city,
            'Positive': positive,
            'Negative': negative,
            'Neutral': neutral,  
            'Total': positive + negative + neutral
        })

    breakdown_df = pd.DataFrame(location_data)
     
    if breakdown_df.empty:
        print(f"No data for category: {category}")
        return breakdown_df
 
    breakdown_df = breakdown_df.sort_values('Negative', ascending=False)

    
    plot_df = breakdown_df.melt(
        id_vars=['Location', 'Total'],  
        value_vars=['Negative', 'Positive'],  
        var_name='Sentiment', 
        value_name='Count'     
    )
 
    fig = px.bar(plot_df, 
                 x='Location', 
                 y='Count', 
                 color='Sentiment', 
                 barmode='group',  
                  
                 color_discrete_map={
                     'Negative': '#e74c3c',  
                     'Positive': '#2ecc71'   
                 },
                  
                 hover_data={'Total': True, 'Location': False},
                 
                 title=f'{category.replace("_", " ").title()} - Sentiment by Location',
                 text_auto=True 
                )
 
    fig.update_layout(
        xaxis_title='Location',
        yaxis_title='Number of Mentions',
        legend_title='Sentiment',
        bargap=0.15, 
        bargroupgap=0.1,  
        height=600,
         
        xaxis={'categoryorder': 'array', 'categoryarray': breakdown_df['Location']}
    )
     
    fig.update_xaxes(tickangle=-45)
 
    if output_file.endswith('.png'):
        output_file = output_file.replace('.png', '.html')
    
    fig.write_html(output_file)
    print(f"Saved: {output_file}")
     

    return breakdown_df, fig.to_dict()  # Save JSON version too 


def create_priority_matrix(df, output_filename):
    """
    Create an interactive priority matrix using Plotly: Frequency vs Negative Sentiment.
    High frequency + high negative = high priority to fix.
    Output is an HTML file.
    """
     
    category_stats = []

    for category in CATEGORIES:
        sentiment_col = f'{category}_sentiment'
 
        if sentiment_col not in df.columns:
            print(f"Warning: Column {sentiment_col} not found in DataFrame. Skipping.")
            continue

        total_reviews = len(df) 
        total_mentions = (df[sentiment_col] != 'neutral').sum()
        negative_mentions = (df[sentiment_col] == 'negative').sum()

        frequency_pct = (total_mentions / total_reviews) * 100

        if total_mentions > 0:
            negative_pct = (negative_mentions / total_mentions) * 100
        else:
            negative_pct = 0

        category_stats.append({
            'Category': category.replace('_', ' ').title(),
            'Frequency': frequency_pct,  
            'Negative_Pct': negative_pct,  
            'Total_Mentions': total_mentions, 
            'Negative_Count': negative_mentions  
        })

    stats_df = pd.DataFrame(category_stats)
     
    if stats_df.empty:
        print("No data available to create priority matrix.")
        return stats_df
 
    median_freq = stats_df['Frequency'].median()
    median_neg = stats_df['Negative_Pct'].median()
 
    fig = px.scatter(stats_df,
                     x='Frequency',
                     y='Negative_Pct',
                     size='Negative_Count',  
                     color='Negative_Pct',   
                     text='Category',        
                     
                      
                     color_continuous_scale='RdYlGn_r', 
                     
                      
                     hover_data={
                         'Frequency': ':.1f%',
                         'Negative_Pct': ':.1f%',
                         'Negative_Count': True,
                         'Total_Mentions': True,
                         'Category': False  
                     },
                      
                     labels={
                         'Frequency': 'Frequency of Mentions (%)',
                         'Negative_Pct': '% Negative When Mentioned',
                         'Negative_Count': 'Negative Mentions Count',
                         'Total_Mentions': 'Total Mentions Count'
                     },
                     title='Priority Matrix: Issue Frequency vs Negative Sentiment<br><sup>(Bubble size reflects number of negative mentions)</sup>'
                    )
 
    fig.add_vline(x=median_freq, line_width=2, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_hline(y=median_neg, line_width=2, line_dash="dash", line_color="gray", opacity=0.5)
 
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.98, y=0.98,
        text="HIGH PRIORITY<br>(Fix These First)",
        showarrow=False,
        font=dict(size=12, color="darkred", family="Arial Black"),
        bgcolor="rgba(255, 200, 200, 0.6)", # Hafif kırmızımsı şeffaf arka plan
        bordercolor="darkred",
        borderwidth=2,
        align="center"
    )
 
    fig.update_traces(
        textposition='top center',  
        marker=dict(line=dict(width=1, color='DarkSlateGrey'))  
    )

    fig.update_layout(
        height=800,  
        width=1200,  
        title_x=0.5,  
        title_font_size=20,
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='Lightgrey'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='Lightgrey'),
        coloraxis_colorbar=dict(title="% Negative")  
    )
 
    if not output_filename.endswith('.html'):
        output_html = output_filename.rsplit('.', 1)[0] + '.html'
    else:
        output_html = output_filename

    fig.write_html(output_html)
    print(f"Saved interactive priority matrix to: {output_html}") 

    return stats_df, fig.to_dict()  # Save JSON version too

def generate_insights_report(df, output_file):
    """
    Generate a text report with key insights
    """
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("BANDON FITNESS - REVIEW ANALYSIS INSIGHTS REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        # Overall statistics
        f.write("OVERALL STATISTICS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total Reviews Analyzed: {len(df)}\n")
        f.write(f"Number of Locations: {df['PLACE ADDRESS'].nunique()}\n")
        f.write(f"Average Rating: {df['SCORE'].mean():.2f}/5\n\n")

        # Top issues across all locations
        f.write("TOP ISSUES ACROSS ALL LOCATIONS\n")
        f.write("-" * 80 + "\n")

        issue_counts = []
        for category in CATEGORIES:
            sentiment_col = f'{category}_sentiment'
            negative_count = (df[sentiment_col] == 'negative').sum()
            issue_counts.append((category.replace('_', ' ').title(), negative_count))

        issue_counts.sort(key=lambda x: x[1], reverse=True)

        for i, (issue, count) in enumerate(issue_counts, 1):
            f.write(f"{i}. {issue}: {count} negative mentions\n")

        f.write("\n")

        # Worst performing locations
        f.write("LOCATIONS NEEDING MOST ATTENTION\n")
        f.write("-" * 80 + "\n")

        location_scores = []
        for location in df['PLACE ADDRESS'].unique():
            location_df = df[df['PLACE ADDRESS'] == location]
            city = location.split(',')[1].strip() if ',' in location else location[:30]

            total_negative = 0
            for category in CATEGORIES:
                sentiment_col = f'{category}_sentiment'
                total_negative += (location_df[sentiment_col] == 'negative').sum()

            avg_rating = location_df['SCORE'].mean()
            location_scores.append((city, total_negative, avg_rating, len(location_df)))

        location_scores.sort(key=lambda x: x[1], reverse=True)

        for i, (city, neg_count, avg_rating, review_count) in enumerate(location_scores, 1):
            f.write(f"{i}. {city}\n")
            f.write(f"   - Negative mentions: {neg_count}\n")
            f.write(f"   - Average rating: {avg_rating:.2f}/5\n")
            f.write(f"   - Total reviews: {review_count}\n\n")

        # Category-specific insights
        f.write("CATEGORY-SPECIFIC INSIGHTS\n")
        f.write("-" * 80 + "\n")

        for category in CATEGORIES:
            sentiment_col = f'{category}_sentiment'
            fragments_col = f'{category}_fragments'

            negative_df = df[df[sentiment_col] == 'negative']

            if len(negative_df) > 0:
                f.write(f"\n{category.replace('_', ' ').upper()}\n")
                f.write(f"Negative mentions: {len(negative_df)}\n")

                # Get most common fragments (simple frequency)
                all_fragments = []
                for fragments in negative_df[fragments_col]:
                    if pd.notna(fragments) and fragments != '':
                        all_fragments.extend([f.strip() for f in str(fragments).split('|')])

                if all_fragments:
                    f.write(f"Sample negative comments:\n")
                    for fragment in all_fragments[:3]:
                        f.write(f"  - {fragment}\n")

        f.write("\n" + "=" * 80 + "\n")
    
    content = ""
    with open(output_file, 'r') as f:
        content = f.read() 

    print(f"Saved: {output_file}")
    return content

def create_interactive_heatmap(data, location_names, title, filename):
    """
    Create and save an interactive heatmap visualization as HTML
    """ 
    formatted_categories = [cat.replace('_', ' ').title() for cat in CATEGORIES]
 
    fig = px.imshow(data,
                    labels=dict(x="Category", y="Location", color="Score"),
                    x=formatted_categories,
                    y=location_names,
                    text_auto='.1f',  
                    color_continuous_scale='RdYlGn_r',  
                    title=title,
                    aspect="auto")

     
    fig.update_layout(
        title_font_size=20,
        title_x=0.5,  
        width=1200,
        height=800
    )
     
    fig.update_xaxes(tickangle=45)
    fig.write_html(filename)
    print(f"Saved HTML: {filename}")
    return fig.to_dict()   


def main(analyzed_file: pd.DataFrame, id: int):
    """
    Main function to generate all visualizations
    """
    print("Loading analyzed data...")
    df = load_analyzed_data(analyzed_file)
    DATA_ROOT = os.path.join(MEDIA_ROOT, 'visualizations') 

    print("\n1. Creating main heatmap (% Negative by Location)...")
    negative_data, location_names = calculate_negative_percentage(df)
    heatmap_negative_on_location_json = create_interactive_heatmap(negative_data, location_names,
                  'Bandon Fitness - % Negative Sentiment by Location & Category',
                  os.path.join(DATA_ROOT, f'heatmap_negative_pct_{id}.html'))

    print("\n2. Creating mention frequency heatmap...")
    frequency_data, location_names = calculate_mention_frequency(df)
    heatmap_mention_frequency_json = create_interactive_heatmap(frequency_data, location_names,
                  'Bandon Fitness - % Reviews Mentioning Each Category',
                  os.path.join(DATA_ROOT,f'heatmap_mention_frequency_{id}.html'))

    print("\n3. Creating weighted severity heatmap...")
    weighted_data, location_names = calculate_weighted_score(df)
    heatmap_weighted_score_json = create_interactive_heatmap(weighted_data, location_names,
                  'Bandon Fitness - Weighted Negative Score (% × Intensity)',
                  os.path.join(DATA_ROOT,f'heatmap_weighted_score_{id}.html'))

    print("\n4. Creating priority matrix...")
    priority_stats, priority_matrix_json = create_priority_matrix(df, os.path.join(DATA_ROOT, f'priority_matrix_{id}.html'))
    print("\nPriority Rankings:")
    print(priority_stats.sort_values('Negative_Count', ascending=False))

    print("\n5. Creating category breakdowns...")
    top_issues = ['equipment_quality', 'customer_service', 'membership_billing']
    breakdown_jsons= {}
    for category in top_issues:
        breakdown_df, breakdown_json = create_category_breakdown(df, category,
                                             os.path.join(DATA_ROOT, f'breakdown_{category}_{id}.html'))
        breakdown_jsons[category] = breakdown_json 

    print("\n6. Generating insights report...")
    text_file_content = generate_insights_report(df, os.path.join(DATA_ROOT, f'insights_report_{id}.txt'))

    print("\n" + "="*60)
    print("ALL VISUALIZATIONS COMPLETE!")
    print("="*60)
    print("\nGenerated files:")
    print(f"  - heatmap_negative_pct_{id}.html")
    print(f"  - heatmap_mention_frequency_{id}.html")
    print(f"  - heatmap_weighted_score_{id}.html")
    print(f"  - priority_matrix_{id}.html")
    print(f"  - breakdown_*_{id}.html")
    print(f"  - insights_report_{id}.txt")
    
    return {
        "negative_heatmap_on_location": weighted_data.tolist(),
        "mention_frequency_heatmap": heatmap_mention_frequency_json,
        "weighted_severity_heatmap": heatmap_weighted_score_json,
        "priority_matrix": priority_matrix_json,
        "breakdown_jsons": breakdown_jsons,
        "insights_report": text_file_content
    }

# if __name__ == "__main__":
#     # IMPORTANT: Replace with your analyzed Excel file name
#     analyzed_file = "temp_Analyzed_Reviews_20251008_151005.xlsx"  # UPDATE THIS!
#     main(analyzed_file)