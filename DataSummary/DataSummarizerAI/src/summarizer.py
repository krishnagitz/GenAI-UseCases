# src/summarizer.py
from transformers import pipeline

def summarize_insights(insights):
    """Summarizes the insights using a language model."""
    summarizer = pipeline("summarization")
    insights_text = insights.to_string()
    summary = summarizer(insights_text, max_length=65, min_length=30, do_sample=False)
    return summary[0]['summary_text']
