import requests
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
from datetime import datetime
import os

# Download NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# Sentiment word lists
POSITIVE_WORDS = ["good", "happy", "love", "great", "awesome", "excellent",
                  "fantastic", "wonderful", "amazing", "perfect", "positive"]
NEGATIVE_WORDS = ["bad", "sad", "hate", "angry", "terrible", "awful",
                  "horrible", "worst", "negative", "problem", "issue"]


def get_username_from_url(url):
    """Extract Reddit username from profile URL."""
    return url.strip("/").split("/")[-1]


def scrape_reddit_user(username):
    """Scrape user posts and comments from Reddit."""
    print(f"Scraping data for u/{username}...")

    base_url = f"https://www.reddit.com/user/{username}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    posts = []
    comments = []

    try:
        # Scrape posts
        response = requests.get(base_url + "submitted/", headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            post_elements = soup.find_all('div', {'data-testid': 'post-container'})
            for post in post_elements[:20]:  # Limit to 20 posts
                try:
                    title = post.find('h3', {'class': '_eYtD2XCVieq6emjKBH3m'}).text
                    text = post.find('div', {'class': 'STit0dLageRsa2yR4te_B'})
                    text = text.text if text else ""
                    subreddit = post.find('a', {'class': '_3ryJoIoycVkA88fy40qNJc'}).text
                    url = post.find('a', {'class': 'SQnoC3ObvgnGjWt90zD9Z'})['href']

                    posts.append({
                        "text": title + "\n" + text,
                        "subreddit": subreddit,
                        "url": "https://www.reddit.com" + url,
                        "source": "web"
                    })
                except:
                    continue

        # Scrape comments
        response = requests.get(base_url + "comments/", headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            comment_elements = soup.find_all('div', {'data-testid': 'comment'})
            for comment in comment_elements[:50]:  # Limit to 50 comments
                try:
                    text = comment.find('div', {'class': '_1qeIAgB0cPwnLhDF9XSiJM'}).text
                    subreddit = comment.find('a', {'class': '_3ryJoIoycVkA88fy40qNJc'}).text
                    url = comment.find('a', {'class': '_1UoeAeSRhOKSNdY_h3iS1O'})['href']

                    comments.append({
                        "text": text,
                        "subreddit": subreddit,
                        "url": "https://www.reddit.com" + url,
                        "source": "web"
                    })
                except:
                    continue

    except Exception as e:
        print(f"Scraping error: {str(e)}")

    print(f"✅ Collected {len(posts)} posts and {len(comments)} comments")
    return posts, comments


def analyze_content(posts, comments, username):
    """Analyze content to create detailed persona."""
    if not posts and not comments:
        return f"""REDDIT USER PERSONA REPORT
{'=' * 40}
Username: u/{username}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

No public posts or comments found for this user.
Possible reasons:
- User has set their profile to private
- User has deleted all content
- Reddit is blocking automated access

Try manually checking the profile:
https://www.reddit.com/user/{username}/
"""

    combined_text = " ".join([item['text'] for item in posts + comments if item.get('text')])

    # Word frequency analysis
    try:
        tokens = word_tokenize(combined_text.lower())
        words = [word for word in tokens if word.isalpha() and word not in stopwords.words("english")]
        word_freq = Counter(words)
        common_words = word_freq.most_common(15)
    except:
        common_words = []

    # Sentiment analysis
    pos_count = sum(word_freq.get(w, 0) for w in POSITIVE_WORDS) if word_freq else 0
    neg_count = sum(word_freq.get(w, 0) for w in NEGATIVE_WORDS) if word_freq else 0

    tone = "Neutral"
    if pos_count > neg_count + 5:
        tone = "Positive"
    elif neg_count > pos_count + 5:
        tone = "Negative"

    # Most active subreddits
    subreddits = Counter([item.get('subreddit', 'unknown') for item in posts + comments]).most_common(5)

    # Build persona
    persona = f"""REDDIT USER PERSONA REPORT
{'=' * 40}
Username: u/{username}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CONTENT SUMMARY:
- Total Posts: {len(posts)}
- Total Comments: {len(comments)}
- Data Source: Web Scraping

ACTIVITY OVERVIEW:
Most active in: {', '.join([f"r/{s[0]}" for s in subreddits]) or 'Various subreddits'}

LANGUAGE ANALYSIS:
Most frequent words: {', '.join([w[0] for w in common_words[:10]]) if common_words else 'Not available'}
Overall tone: {tone} (Positive: {pos_count}, Negative: {neg_count})

EXAMPLE CITATIONS:
{get_sample_citations(posts, comments) if (posts or comments) else 'No content available'}
"""
    return persona


def get_sample_citations(posts, comments):
    """Generate sample citations from available content."""
    examples = []

    if posts:
        examples.append(
            f"Sample post in r/{posts[0].get('subreddit', 'unknown')}: {posts[0].get('url', 'URL not available')}")
    if comments:
        examples.append(
            f"Sample comment in r/{comments[0].get('subreddit', 'unknown')}: {comments[0].get('url', 'URL not available')}")

    return "\n".join(examples)


def save_persona(username, persona_text):
    """Save persona to file."""
    filename = f"{username}_persona.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(persona_text)
    print(f"✅ Persona saved to {filename}")


if __name__ == "__main__":
    print("Reddit User Persona Generator (Web Scraping Version)")
    print("---------------------------------------------------")

    try:
        reddit_url = input("Enter Reddit user profile URL: ").strip()
        username = get_username_from_url(reddit_url)

        posts, comments = scrape_reddit_user(username)
        persona = analyze_content(posts, comments, username)

        print("\n" + "=" * 40)
        print(persona)
        print("=" * 40 + "\n")

        save_persona(username, persona)
        print("\n🎉 Persona generation complete!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")