# pip install matplotlib seaborn numpy

# python review_visualizer.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime

# Set style for better-looking plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

CATEGORIES = [
    'cleanliness',
    'crowding',
    'customer_service',
    'equipment_quality',
    'membership_billing',
    'price',
    'staff_attitude'
]

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

def create_heatmap(data, location_names, title, filename, fmt='.1f'):
    """
    Create and save a heatmap visualization
    """
    fig, ax = plt.subplots(figsize=(14, 8))

    # Create heatmap
    sns.heatmap(data,
                annot=True,
                fmt=fmt,
                cmap='RdYlGn_r',  # Red for high (bad), green for low (good)
                xticklabels=[cat.replace('_', ' ').title() for cat in CATEGORIES],
                yticklabels=location_names,
                cbar_kws={'label': 'Score'},
                linewidths=0.5,
                ax=ax)

    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Category', fontsize=12, fontweight='bold')
    plt.ylabel('Location', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()

    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    plt.close()

def create_category_breakdown(df, category, output_file):
    """
    Create a detailed breakdown for a specific category across locations
    """
    locations = df['PLACE ADDRESS'].unique()

    location_data = []

    for location in locations:
        location_df = df[df['PLACE ADDRESS'] == location]
        city = location.split(',')[1].strip() if ',' in location else location[:30]

        sentiment_col = f'{category}_sentiment'
        intensity_col = f'{category}_intensity'

        positive = (location_df[sentiment_col] == 'positive').sum()
        negative = (location_df[sentiment_col] == 'negative').sum()
        neutral = (location_df[sentiment_col] == 'neutral').sum()

        location_data.append({
            'Location': city,
            'Positive': positive,
            'Negative': negative,
            'Neutral': neutral,
            'Total Mentions': positive + negative
        })

    breakdown_df = pd.DataFrame(location_data)
    breakdown_df = breakdown_df.sort_values('Negative', ascending=False)

    # Create bar chart
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(breakdown_df))
    width = 0.35

    ax.bar(x - width/2, breakdown_df['Negative'], width, label='Negative', color='#e74c3c')
    ax.bar(x + width/2, breakdown_df['Positive'], width, label='Positive', color='#2ecc71')

    ax.set_xlabel('Location', fontweight='bold')
    ax.set_ylabel('Number of Mentions', fontweight='bold')
    ax.set_title(f'{category.replace("_", " ").title()} - Sentiment by Location',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(breakdown_df['Location'], rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

    return breakdown_df

def create_priority_matrix(df, output_file):
    """
    Create a priority matrix: Frequency vs Negative Sentiment
    High frequency + high negative = high priority to fix
    """
    category_stats = []

    for category in CATEGORIES:
        sentiment_col = f'{category}_sentiment'

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

    # Create scatter plot
    fig, ax = plt.subplots(figsize=(12, 8))

    scatter = ax.scatter(stats_df['Frequency'],
                        stats_df['Negative_Pct'],
                        s=stats_df['Negative_Count'] * 20,  # Size by count
                        alpha=0.6,
                        c=stats_df['Negative_Pct'],
                        cmap='RdYlGn_r')

    # Add labels for each point
    for idx, row in stats_df.iterrows():
        ax.annotate(row['Category'],
                   (row['Frequency'], row['Negative_Pct']),
                   fontsize=9,
                   fontweight='bold',
                   xytext=(5, 5),
                   textcoords='offset points')

    # Add quadrant lines
    ax.axhline(y=stats_df['Negative_Pct'].median(), color='gray', linestyle='--', alpha=0.3)
    ax.axvline(x=stats_df['Frequency'].median(), color='gray', linestyle='--', alpha=0.3)

    ax.set_xlabel('Frequency of Mentions (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('% Negative When Mentioned', fontsize=12, fontweight='bold')
    ax.set_title('Priority Matrix: Issue Frequency vs Negative Sentiment\n(Bubble size = # of negative mentions)',
                 fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3)

    # Add quadrant labels
    ax.text(0.95, 0.95, 'HIGH PRIORITY', transform=ax.transAxes,
            fontsize=10, fontweight='bold', color='red',
            ha='right', va='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.colorbar(scatter, label='% Negative', ax=ax)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

    return stats_df

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

    print(f"Saved: {output_file}")

def main(analyzed_file):
    """
    Main function to generate all visualizations
    """
    print("Loading analyzed data...")
    df = load_analyzed_data(analyzed_file)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    print("\n1. Creating main heatmap (% Negative by Location)...")
    negative_data, location_names = calculate_negative_percentage(df)
    create_heatmap(negative_data, location_names,
                  'Bandon Fitness - % Negative Sentiment by Location & Category',
                  f'heatmap_negative_pct_{timestamp}.png')

    print("\n2. Creating mention frequency heatmap...")
    frequency_data, location_names = calculate_mention_frequency(df)
    create_heatmap(frequency_data, location_names,
                  'Bandon Fitness - % Reviews Mentioning Each Category',
                  f'heatmap_mention_frequency_{timestamp}.png')

    print("\n3. Creating weighted severity heatmap...")
    weighted_data, location_names = calculate_weighted_score(df)
    create_heatmap(weighted_data, location_names,
                  'Bandon Fitness - Weighted Negative Score (% × Intensity)',
                  f'heatmap_weighted_score_{timestamp}.png',
                  fmt='.0f')

    print("\n4. Creating priority matrix...")
    priority_stats = create_priority_matrix(df, f'priority_matrix_{timestamp}.png')
    print("\nPriority Rankings:")
    print(priority_stats.sort_values('Negative_Count', ascending=False))

    print("\n5. Creating category breakdowns...")
    top_issues = ['equipment_quality', 'customer_service', 'membership_billing']
    for category in top_issues:
        breakdown = create_category_breakdown(df, category,
                                             f'breakdown_{category}_{timestamp}.png')

    print("\n6. Generating insights report...")
    generate_insights_report(df, f'insights_report_{timestamp}.txt')

    print("\n" + "="*60)
    print("ALL VISUALIZATIONS COMPLETE!")
    print("="*60)
    print("\nGenerated files:")
    print(f"  - heatmap_negative_pct_{timestamp}.png")
    print(f"  - heatmap_mention_frequency_{timestamp}.png")
    print(f"  - heatmap_weighted_score_{timestamp}.png")
    print(f"  - priority_matrix_{timestamp}.png")
    print(f"  - breakdown_*_{timestamp}.png")
    print(f"  - insights_report_{timestamp}.txt")

if __name__ == "__main__":
    # IMPORTANT: Replace with your analyzed Excel file name
    analyzed_file = "temp_Analyzed_Reviews_20251008_151005.xlsx"  # UPDATE THIS!
    main(analyzed_file)