# 📰 NewsBot

An AI-powered news assistant that automatically finds, summarizes, and emails you the most relevant news article from the last 24 hours.

Deployed to [render.com](https://dashboard.render.com/), and triggered daily via a GH Action.

---

### 🎯 Preference System

NewsBot uses an **AI-powered preference system** with semantic embeddings and scoring (-5 to 5) to learn your interests:

- **Positive scores (1-5)**: Topics you like
- **Negative scores (-1 to -5)**: Topics you dislike
- **Zero score (0)**: Neutral topics

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

Rate articles via email links using a **3-star system**:
- **🤩 3 stars**: Like the article
- **😐 2 stars**: Neutral/indifferent
- **🤢 1 star**: Dislike the article

#### 🧠 How it learns

The system uses **semantic embeddings** to understand content similarity:

1. **Rate articles** via email links (1-3 stars)
2. **AI extracts keywords** from article content
3. **Updates preferences** based on your rating:
   - **3 stars**: Boosts similar topics (+1 to +4 score)
   - **2 stars**: No change (neutral)
   - **1 star**: Reduces similar topics (-1 to -4 score)
4. **Semantic matching** finds similar existing preferences
5. **Future selection** uses these learned preferences

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
   OPENAI_API_KEY=your_openai_api_key
   NEWS_API_KEY=your_news_api_key
   FROM_EMAIL=your_email@gmail.com
   TO_EMAIL=recipient@example.com
   SMTP_PASS=your_gmail_app_password
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_KEY=your_supabase_key
   NEWSBOT_DEFAULT_PREFERENCES=
   ```

3. **Start server**:
   ```bash
   python3 newsbot.py
   ```

4. **Test (manual trigger)**:
   ```bash
   curl -X POST http://localhost:3000/trigger
   ```

📰 ✨ 📰 ✨ 📰 ✨ 📰 ✨ 📰 ✨ �� ✨ 📰 ✨ 📰 ✨ 📰 ✨
