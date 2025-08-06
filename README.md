# 📰 NewsBot

An AI-powered news assistant that automatically finds, summarizes, and emails you the most relevant news article from the last 24 hours.

---

### 🤖 Current usage
Deployed to [render.com](https://dashboard.render.com/), and triggered daily via a GH Action.


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
   ```

3. **Start server**:
   ```bash
   python3 newsbot.py
   ```

4. **Test (manual trigger)**:
   ```bash
   curl -X POST http://localhost:3000/trigger
   ```

📰 ✨ 📰 ✨ 📰 ✨ 📰 ✨ 📰 ✨ 📰 ✨ 📰 ✨ 📰 ✨ 📰 ✨
