# main.py
from src.data_ingestion import read_data
from src.data_analysis import analyze_data
from src.summarizer import summarize_insights

def main():
    # Step 1: Read data
    file_path = 'Data/trials.csv'  # Specify your data file path
    data = read_data(file_path)
    
    # Step 2: Analyze data
    insights = analyze_data(data)
    
    # Step 3: Summarize insights
    summary = summarize_insights(insights)
    
    # Print the summary
    print("Summary of the Data Product:")
    print(summary)

if __name__ == "__main__":
    main()
