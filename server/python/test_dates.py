from analyze_papers import analyze_papers
from datetime import datetime, timedelta
import json

def test_different_periods():
    # Use a fixed current date for testing
    current_date = datetime(2024, 4, 14)
    
    # Test three different non-overlapping periods
    periods = [
        (7, "Last 7 days"),
        (30, "Last 30 days"),
        (90, "Last 90 days")
    ]
    
    print("\n=== Testing Different Time Periods ===")
    results = {}
    
    for days_back, period_name in periods:
        print(f"\n{'-'*20} {period_name} {'-'*20}")
        papers = analyze_papers(days_back, base_date=current_date)
        
        if papers:
            # Store results for comparison
            results[days_back] = {
                'dates': [p['published'] for p in papers],
                'titles': [p['title'] for p in papers]
            }
            
            print(f"\nFound {len(papers)} papers")
            print("\nDate distribution:")
            date_counts = {}
            for paper in papers:
                date = paper['published']
                date_counts[date] = date_counts.get(date, 0) + 1
            for date in sorted(date_counts.keys()):
                print(f"  {date}: {date_counts[date]} papers")
            
            print(f"\nTop 5 papers by score:")
            for i, paper in enumerate(papers[:5], 1):
                print(f"\n{i}. {paper['title']}")
                print(f"   Published: {paper['published']}")
                print(f"   Total Score: {paper['total_score']}")
                print(f"   Relevance Score: {paper['relevance_score']}")
                print(f"   Author Score: {paper['author_score']}")
                print(f"   Tags: {paper['tags']}")
        else:
            print("No papers found")
    
    # Compare periods to check for duplicates
    print("\n=== Checking for Duplicates Between Periods ===")
    for i, (days1, name1) in enumerate(periods):
        for days2, name2 in periods[i+1:]:
            if days1 in results and days2 in results:
                common_titles = set(results[days1]['titles']) & set(results[days2]['titles'])
                if common_titles:
                    print(f"\nFound {len(common_titles)} papers that appear in both {name1} and {name2}")
                    print("Sample duplicates:")
                    for title in list(common_titles)[:5]:  # Show only first 5 duplicates
                        print(f"- {title}")
                else:
                    print(f"\nNo duplicates between {name1} and {name2}")

if __name__ == "__main__":
    test_different_periods() 