from transformers import pipeline

def analyze_content(texts, keyword):
    # Initialize pipelines with device=-1 (CPU) or 0 (first GPU)
    device = 0 if torch.cuda.is_available() else -1
    print(f"Using device: {'GPU' if device == 0 else 'CPU'}")
    
    sentiment_analyzer = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english', device=device)
    summarizer = pipeline('summarization', model='facebook/bart-large-cnn', device=device)
    
    results = []
    for text in texts:
        # Basic scoring: 1 if keyword is present, 0 otherwise
        score = 1 if keyword.lower() in text.lower() else 0
        
        # Sentiment analysis (truncate to 512 tokens, max for DistilBERT)
        sentiment = sentiment_analyzer(text[:512])[0]['label']
        
        # Dynamic max_length for summarization: half the input length, minimum 5, maximum 50
        input_length = len(text.split())  # Approximate token count by splitting on whitespace
        max_length = max(5, min(50, input_length // 2))  # Ensure 5 <= max_length <= 50
        
        # Summarization (truncate input to 1024 tokens, max for BART)
        summary = summarizer(text[:1024], max_length=max_length, min_length=5, do_sample=False)[0]['summary_text']
        
        # Append result
        results.append({'score': score, 'email': [], 'sentiment': sentiment, 'summary': summary})
    
    return results