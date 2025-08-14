# 📰 NewsBot

An AI-powered news assistant that automatically finds, summarizes, and emails you the most relevant news article from the last 24 hours.

---

### 🤖 Current usage
Deployed to [render.com](https://dashboard.render.com/), and triggered daily via a GH Action.

### 🎯 Preference System

NewsBot uses a **JSON**-based preference system with keyword scoring (1-5) to learn your interests:

- **High scores (4-5)**: Interested topics
- **Medium scores (3)**: Neutral topics
- **Low scores (1-2)**: Topics to avoid

**Example preferences:**
```json
{
  "technology": 5,
  "ai": 5,
  "machine learning": 4,
  "politics": 1,
  "celebrity gossip": 1,
  "space exploration": 3,
  "climate change": 3
}
```

Each keyword is weighted from 1-5, and the weighting evolves over time based on the rating an article recieves:

**Rating System**: Rate articles 1-3 stars (1=dislike, 2=neutral, 3=like)

**How it learns:**
- Rate articles via email links (1-3 stars)
- AI extracts relevant keywords from article content
- Updates preference weights based on your rating
- Future article selection uses these preferences

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
