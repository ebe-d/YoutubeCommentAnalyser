from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize the VADER sentiment analyzer once at module level
_analyzer = SentimentIntensityAnalyzer()


def analyze_comments(comments_list: list[str]) -> list[dict]:
    """
    Analyze a list of comment strings with VADER sentiment analysis.

    Args:
        comments_list: Raw comment strings.

    Returns:
        List of dicts, each containing:
            - text:      the original comment
            - compound:  VADER compound score (-1.0 to +1.0)
            - sentiment: "Positive" | "Neutral" | "Negative"
            - toxic:     True if compound <= -0.5
    """
    results = []

    for comment in comments_list:
        text = comment.strip()
        if not text:
            continue

        scores = _analyzer.polarity_scores(text)
        compound = scores["compound"]

        if compound >= 0.05:
            sentiment = "Positive"
        elif compound <= -0.05:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        results.append(
            {
                "text": text,
                "compound": round(compound, 4),
                "sentiment": sentiment,
                "toxic": compound <= -0.5,
            }
        )

    return results
