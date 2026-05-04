# 📊 StockAI Pro - AI-Powered Stock Prediction Platform:-
An intelligent stock market analysis platform using **LSTM neural networks** for price prediction, technical analysis, and AI-generated trading recommendations.


## 🚀 Features:-

- 🤖 **AI Price Prediction** - LSTM deep learning model predicts future stock prices
- 📊 **Technical Analysis** - RSI, MACD, Moving Averages, Bollinger Bands
- 💡 **Smart Insights** - AI-generated BUY/SELL/HOLD recommendations
- ⚖️ **Stock Comparison** - Compare up to 4 stocks side-by-side
- 🔍 **Smart Search** - Autocomplete stock search with suggestions
- 👤 **User System** - Secure login/signup with password validation
- 📈 **Live Charts** - Interactive price charts with multiple timeframes
- 🌍 **Multi-Market** - US Stocks (NASDAQ/NYSE) + Indian Stocks (NSE/BSE)
- 🎨 **Modern UI** - Glassmorphism design with dark theme
- 📱 **Responsive** - Works on desktop, tablet, and mobile


## 🛠️ Tech Stack:-

| Layer | Technology |
|-------|-----------|
| Backend | Python Flask |
| AI/ML | TensorFlow/Keras (LSTM) |
| Database | SQLite + SQLAlchemy |
| Frontend | HTML5, CSS3, JavaScript |
| Charts | Chart.js |
| Data Source | Yahoo Finance (yfinance) |
| Auth | Flask-Login + Werkzeug |


## 📸 Screenshots:-

### Dashboard:
![Dashboard](screenshots/dashboard.png)

### AI Prediction:
![Prediction](screenshots/prediction.png)

### Insights:
![Insights](screenshots/insights.png)

### Stock Comparison:
![Compare](screenshots/compare.png)


## ⚡ Quick Start:-

### Prerequisites:
- Python 3.8 or higher
- pip package manager

# Installation:-

```bash
# 1. Clone the repository:
git clone https://github.com/YOUR_USERNAME/stock-prediction-ai.git
cd stock-prediction-ai

# 2. Create virtual environment:
python -m venv venv

# 3. Activate virtual environment:-

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies:
pip install -r requirements.txt

# 5. Create .env file (optional - This project for now also works without the use of API keys)
#If necessary to use API keys then copy the example below:-
echo SECRET_KEY=your_secret_key_here > .env
echo FLASK_ENV=development >> .env

# 6. Run the application:
python app.py

# 7. Open browser:
# Go to: http://localhost:8080


PROJECT INFO:-

📁 Project-Structure:-

stock-prediction-ai/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── data_sources.py        # Yahoo Finance data fetcher
├── model_trainer.py       # LSTM model training
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not committed)
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── templates/
│   ├── auth.html          # Login/Signup page
│   └── index.html         # Main dashboard
├── static/
│   ├── css/
│   │   ├── auth.css       # Auth page styles
│   │   └── style.css      # Dashboard styles
│   └── js/
│       ├── auth.js        # Auth validation
│       └── main.js        # Dashboard logic
├── models/                # Trained AI models (auto-created)
└── instance/              # SQLite database (auto-created)


🎯 Usage Guide:-

Sign_Up - Create an account with email and password
Dashboard - Search stocks and view price charts
AI_Predict - Select a stock and days to predict future prices
Insights - Get AI-generated buy/sell/hold recommendations
Compare - Compare multiple stocks side-by-side
Profile - Manage watchlist and account settings


⚠️ Disclaimer:-
This project is done solely for EDUCATIONAL PURPOSES only. Stock market predictions are inherently uncertain. Never make financial decisions based solely on some AI predictions. Always consult with a qualified financial advisor.


📄 License:-
This project is licensed under the MIT License - see the LICENSE file for details.


👨‍💻 Author:-
Siddharth Sanjay
GitHub: SiddharthSanjay2005
Email: siddusanjay2005com


🙏 Acknowledgments:-
Yahoo Finance for free market data
TensorFlow for the deep learning framework
Chart.js for beautiful charts
Flask for the web framework
