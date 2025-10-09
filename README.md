# 📰 NewsBot

-------

## ❌ **DISABLED** ❌
> All actions have been disabled and render.com deployment has been suspended!

-------

An AI-powered news assistant to find, summarize, and deliver you the most relevant news article from the last 24 hours!

🤖 Deployed to [render.com](https://dashboard.render.com/), and triggered daily via a GH Action.

**Features:**
- 📰 **Mobile-responsive page** summarizing the article
- 📱 **Push notifications** via ntfy.sh with link to article
- ⚡ **Rating system** to provide feedback for finding future article
- 🧠 **Preferences with embeddings** to learn and keep track of preferred topics.


---

### 🎯 Preference System

Uses an AI-powered preference system with semantic embeddings and scoring (-5 to 5) to learn your interests. The semantic embeddings are used to understand content similarity.

- **Positive scores (1-5)**: Topics you like
- **Negative scores (-1 to -5)**: Topics you dislike

**Example preferences:**
```json
{
  "artificial intelligence": {
    "score": 5,
    "embedding": [0.1, 0.2, ...]
  },
  "ai": {
    "score": 5,
    "embedding": [0.15, 0.25, ...]
  },
  "gaming": {
    "score": 4,
    "embedding": [0.12, 0.18, ...]
  },
  "politics": {
    "score": -5,
    "embedding": [0.08, 0.22, ...]
  }
}
```

#### ⭐ Rating System

Rate articles directly in the **web interface** using interactive buttons:
- **🤩 Like (3 stars)**: Boost similar topics in your preferences
- **😐 Neutral (2 stars)**: No preference change, but tracks the new keywords
- **😡 Dislike (1 star)**: Reduce similar topics in your preferences


------

### 🛠️ Local Development

1. **Setup**:
   ```bash
   git clone git@github.com:joelchelliah/newsbot.git
   cd newsbot
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Create `.env` file with**:
  ```bash
  # Required
  OPENAI_API_KEY= # your_openai_api_key
  NEWS_API_KEY= # your_news_api_key
  SUPABASE_URL= # your_supabase_url
  SUPABASE_SERVICE_KEY= # your_supabase_key
  NEWSBOT_DOMAIN=# Your domain for web article links

  # Optional
  NTFY_TOPIC= # For push notifications via ntfy.sh
  NEWSBOT_EMAIL_ENABLED= # email notification
  FROM_EMAIL= # Only needed if email enabled
  TO_EMAIL= # Only needed if email enabled
  SMTP_PASS= # Only needed if email enabled
  NEWSBOT_DEFAULT_PREFERENCES= # JSON string of initial preferences
  ```

3. **Start server**:
   ```bash
   python3 newsbot.py
   ```

4. **Test (manual trigger)**:
   ```bash
   curl -X POST http://localhost:3000/trigger
   ```


---

🎯 **Happy reading!** 📰✨
