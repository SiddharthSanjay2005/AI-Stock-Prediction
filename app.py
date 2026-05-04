import numpy as np
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import re

from config import Config
from data_sources import DataManager
from model_trainer import StockPredictor

app = Flask(__name__)
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth'

CORS(app)
data_manager = DataManager()

# Cache for predictions
prediction_cache = {}

# ==================== MODELS ====================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    phone = db.Column(db.String(15))
    country = db.Column(db.String(50))
    experience = db.Column(db.String(20))

class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    user = db.relationship('User', backref='watchlist')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# ==================== AUTH ROUTES ====================
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth'))

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'login':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                user.last_login = datetime.utcnow()
                db.session.commit()
                flash('Welcome back!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password', 'error')
        
        elif action == 'signup':
            fullname = request.form.get('fullname', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm = request.form.get('confirm_password', '')
            
            errors = []
            if len(fullname) < 2:
                errors.append("Name too short")
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                errors.append("Invalid email")
            if User.query.filter_by(email=email).first():
                errors.append("Email already registered")
            if password != confirm:
                errors.append("Passwords don't match")
            if len(password) < 8:
                errors.append("Password must be at least 8 characters")
            if not re.search(r"[A-Z]", password):
                errors.append("Need uppercase letter")
            if not re.search(r"\d", password):
                errors.append("Need a number")
            
            if errors:
                for e in errors:
                    flash(e, 'error')
            else:
                user = User(
                    fullname=fullname,
                    email=email,
                    password_hash=generate_password_hash(password)
                )
                db.session.add(user)
                db.session.commit()
                flash('Account created! Please login.', 'success')
    
    return render_template('auth.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth'))

# ==================== PAGE ROUTES ====================
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html', user=current_user, page='dashboard')

@app.route('/predict')
@login_required
def predict_page():
    return render_template('index.html', user=current_user, page='predict')

@app.route('/insights')
@login_required
def insights_page():
    return render_template('index.html', user=current_user, page='insights')

@app.route('/compare')
@login_required
def compare_page():
    return render_template('index.html', user=current_user, page='compare')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update':
            current_user.phone = request.form.get('phone', '')
            current_user.country = request.form.get('country', '')
            current_user.experience = request.form.get('experience', '')
            db.session.commit()
            flash('Profile updated!', 'success')
        
        elif action == 'password':
            curr = request.form.get('current_password', '')
            new = request.form.get('new_password', '')
            conf = request.form.get('confirm_new_password', '')
            
            if not check_password_hash(current_user.password_hash, curr):
                flash('Current password incorrect', 'error')
            elif new != conf:
                flash('Passwords dont match', 'error')
            elif len(new) < 8:
                flash('Password too short', 'error')
            else:
                current_user.password_hash = generate_password_hash(new)
                db.session.commit()
                flash('Password changed!', 'success')
        
        elif action == 'add_watchlist':
            sym = request.form.get('symbol', '').upper().strip()
            if sym:
                exists = Watchlist.query.filter_by(user_id=current_user.id, symbol=sym).first()
                if not exists:
                    db.session.add(Watchlist(user_id=current_user.id, symbol=sym))
                    db.session.commit()
                    flash(f'{sym} added!', 'success')
        
        elif action == 'remove_watchlist':
            sym = request.form.get('symbol', '').upper().strip()
            item = Watchlist.query.filter_by(user_id=current_user.id, symbol=sym).first()
            if item:
                db.session.delete(item)
                db.session.commit()
                flash(f'{sym} removed', 'info')
    
    watchlist = Watchlist.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', user=current_user, page='profile', watchlist=watchlist)

# ==================== API ROUTES ====================
@app.route('/api/stock/search', methods=['POST'])
def search_stocks():
    query = request.json.get('query', '').upper()
    results = []
    
    for market, stocks in Config.POPULAR_STOCKS.items():
        for sym, name in stocks.items():
            if query in sym or query.lower() in name.lower():
                results.append({'symbol': sym, 'name': name, 'market': market})
    
    return jsonify({'results': results[:10]})

@app.route('/api/stock/quote', methods=['POST'])
def stock_quote():
    sym = request.json.get('symbol', 'AAPL').upper()
    quote = data_manager.get_realtime_quote(sym)
    
    if quote:
        return jsonify({'success': True, 'data': quote})
    
    # Generate basic data if API fails
    return jsonify({
        'success': True,
        'data': {
            'symbol': sym,
            'name': sym,
            'price': 150.00,
            'change': 0.00,
            'open': 150.00,
            'high': 151.00,
            'low': 149.00,
            'volume': 1000000,
            'market_cap': 0,
            'pe_ratio': None,
            'sector': 'N/A',
            'exchange': 'N/A'
        }
    })

@app.route('/api/stock/history', methods=['POST'])
def stock_history():
    sym = request.json.get('symbol', 'AAPL').upper()
    period = request.json.get('period', '1y')
    
    try:
        data = data_manager.get_stock_data(sym, period)
        
        if data is not None and not data.empty:
            # Convert to dict format
            history = []
            for idx, row in data.iterrows():
                history.append({
                    'date': idx.strftime('%Y-%m-%d'),
                    'close': float(row['Close']),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'volume': int(row['Volume']),
                    'sma_20': float(row['Close']) if len(history) < 20 else None,
                    'sma_50': float(row['Close']) if len(history) < 50 else None
                })
            
            return jsonify({'success': True, 'data': history})
    except Exception as e:
        print(f"History error: {e}")
    
    return jsonify({'success': False, 'error': 'Could not fetch data'})

@app.route('/api/market/indices')
def market_indices():
    indices = data_manager.get_market_indices()
    return jsonify(indices)

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        sym = request.json.get('symbol', 'AAPL').upper()
        days = min(int(request.json.get('days', 30)), 60)
        
        print(f"\n{'='*50}")
        print(f"PREDICTION REQUEST: {sym} for {days} days")
        print(f"{'='*50}")
        
        # Check cache
        cache_key = f"{sym}_{days}"
        if cache_key in prediction_cache:
            cached = prediction_cache[cache_key]
            if (datetime.now() - cached['ts']).seconds < 300:
                print("Returning cached result")
                return jsonify(cached['data'])
        
        # Train model
        predictor = StockPredictor(sym)
        success = predictor.train()
        
        if not success:
            print("Training failed!")
            return jsonify({
                'success': False,
                'error': 'Could not train model. Try a popular stock like AAPL, MSFT, or GOOGL.'
            })
        
        # Make predictions
        predictions = predictor.predict_future(days)
        
        if predictions is None or len(predictions) == 0:
            print("No predictions generated!")
            return jsonify({
                'success': False,
                'error': 'Prediction failed. Please try again.'
            })
        
        print(f"Predictions: {predictions[:5]}...")
        
        # Generate dates
        dates = [(datetime.now() + timedelta(days=x)).strftime('%Y-%m-%d') for x in range(1, days+1)]
        
        # Calculate metrics
        current = float(predictions[0])
        target = float(predictions[-1])
        change = ((target - current) / current) * 100 if current != 0 else 0
        
        result = {
            'success': True,
            'predictions': [float(p) for p in predictions],
            'dates': dates,
            'confidence': predictor.get_confidence(),
            'trend': 'Bullish' if target > current else 'Bearish',
            'current_price': current,
            'target_price': target,
            'change_percent': change
        }
        
        # Cache
        prediction_cache[cache_key] = {
            'data': result,
            'ts': datetime.now()
        }
        
        print(f"SUCCESS! Trend: {result['trend']}, Change: {change:.2f}%")
        return jsonify(result)
        
    except Exception as e:
        print(f"PREDICT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        })

@app.route('/api/insights', methods=['POST'])
def insights():
    sym = request.json.get('symbol', 'AAPL').upper()
    
    try:
        print(f"Generating insights for {sym}...")
        
        # Get stock quote
        quote = data_manager.get_realtime_quote(sym)
        if not quote:
            return jsonify({
                'success': False, 
                'error': f'Could not find stock: {sym}'
            })
        
        price = quote.get('price', 100)
        change = quote.get('change', 0)
        
        # Get historical data
        hist = data_manager.get_stock_data(sym, '3mo')
        
        # Default values
        rsi = 50
        trend = "Neutral"
        trend_emoji = "📊"
        signals = []
        
        if hist is not None and not hist.empty and len(hist) > 20:
            closes = hist['Close'].values
            
            # Calculate RSI manually
            deltas = []
            for i in range(1, len(closes)):
                deltas.append(closes[i] - closes[i-1])
            deltas = np.array(deltas)
            
            gains = deltas[deltas > 0]
            losses = abs(deltas[deltas < 0])
            
            avg_gain = np.mean(gains[-14:]) if len(gains) > 0 else 0
            avg_loss = np.mean(losses[-14:]) if len(losses) > 0 else 0
            
            if avg_loss > 0:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 100 if avg_gain > 0 else 50
            
            rsi = round(rsi, 1)
            
            # Moving averages
            sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else price
            sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else price
            
            # Determine trend
            if price > sma_20 and sma_20 > sma_50:
                trend = "Strong Bullish"
                trend_emoji = "🚀"
            elif price > sma_20:
                trend = "Bullish"
                trend_emoji = "📈"
            elif price < sma_20 and sma_20 < sma_50:
                trend = "Bearish"
                trend_emoji = "📉"
            else:
                trend = "Neutral"
                trend_emoji = "📊"
            
            # RSI Signal
            if rsi > 70:
                signals.append({
                    'type': 'warning',
                    'msg': f'RSI is Overbought at {rsi}',
                    'action': 'Consider selling or taking profits'
                })
            elif rsi < 30:
                signals.append({
                    'type': 'opportunity',
                    'msg': f'RSI is Oversold at {rsi}',
                    'action': 'Potential buying opportunity'
                })
            elif rsi > 55:
                signals.append({
                    'type': 'positive',
                    'msg': f'RSI shows bullish momentum at {rsi}',
                    'action': 'Uptrend may continue'
                })
            elif rsi < 45:
                signals.append({
                    'type': 'warning',
                    'msg': f'RSI shows bearish momentum at {rsi}',
                    'action': 'Downtrend may continue'
                })
            else:
                signals.append({
                    'type': 'neutral',
                    'msg': f'RSI is neutral at {rsi}',
                    'action': 'No clear signal, wait for confirmation'
                })
            
            # Price vs SMA signal
            if price > sma_20:
                signals.append({
                    'type': 'positive',
                    'msg': f'Price (${price:.2f}) is above 20-day SMA (${sma_20:.2f})',
                    'action': 'Short-term uptrend confirmed'
                })
            else:
                signals.append({
                    'type': 'warning',
                    'msg': f'Price (${price:.2f}) is below 20-day SMA (${sma_20:.2f})',
                    'action': 'Short-term downtrend'
                })
            
            # Volume signal
            if len(hist) >= 20:
                avg_vol = np.mean(hist['Volume'].values[-20:])
                current_vol = hist['Volume'].values[-1] if len(hist) > 0 else quote.get('volume', 0)
                if current_vol > avg_vol * 1.5:
                    signals.append({
                        'type': 'info',
                        'msg': 'High trading volume detected',
                        'action': 'Strong market interest in this stock'
                    })
            
            # 5-day performance
            if len(closes) >= 5:
                change_5d = ((closes[-1] - closes[-5]) / closes[-5]) * 100
                if change_5d > 3:
                    signals.append({
                        'type': 'positive',
                        'msg': f'Stock gained {change_5d:.1f}% in last 5 days',
                        'action': 'Strong positive momentum'
                    })
                elif change_5d < -3:
                    signals.append({
                        'type': 'warning',
                        'msg': f'Stock dropped {abs(change_5d):.1f}% in last 5 days',
                        'action': 'Significant decline, watch for support levels'
                    })
        
        else:
            # Fallback when not enough historical data
            if change > 1:
                trend = "Bullish"
                trend_emoji = "📈"
            elif change < -1:
                trend = "Bearish"
                trend_emoji = "📉"
            
            signals.append({
                'type': 'info',
                'msg': f'Daily change: {change:+.2f}%',
                'action': 'Limited historical data available'
            })
        
        # Count signals for recommendation
        positive = sum(1 for s in signals if s['type'] in ['positive', 'opportunity'])
        negative = sum(1 for s in signals if s['type'] == 'warning')
        
        # Generate recommendation
        if positive > negative:
            recommendation = {
                'action': 'BUY',
                'color': '#10b981',
                'confidence': min(60 + positive * 10, 85)
            }
        elif negative > positive:
            recommendation = {
                'action': 'SELL',
                'color': '#ef4444',
                'confidence': min(60 + negative * 10, 85)
            }
        else:
            recommendation = {
                'action': 'HOLD',
                'color': '#f59e0b',
                'confidence': 55
            }
        
        # Risk level
        if rsi > 75 or rsi < 25:
            risk = 'High'
        elif rsi > 65 or rsi < 35:
            risk = 'Medium'
        else:
            risk = 'Low'
        
        result = {
            'success': True,
            'symbol': sym,
            'price': price,
            'rsi': rsi,
            'risk': risk,
            'summary': {
                'trend': trend,
                'emoji': trend_emoji
            },
            'signals': signals,
            'recommendation': recommendation
        }
        
        print(f"Insights generated for {sym}: {trend}, RSI={rsi}, Rec={recommendation['action']}")
        return jsonify(result)
        
    except Exception as e:
        print(f"Insights error for {sym}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Error generating insights. Please try again.'
        })

@app.route('/api/compare', methods=['POST'])
def compare():
    symbols = request.json.get('symbols', ['AAPL', 'MSFT'])[:4]
    result = {}
    
    colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444']
    
    for i, sym in enumerate(symbols):
        try:
            data = data_manager.get_stock_data(sym, '1mo')
            quote = data_manager.get_realtime_quote(sym)
            
            if data is not None and not data.empty and quote:
                prices = data['Close'].values
                base = prices[0]
                normalized = [((p - base) / base) * 100 for p in prices]
                dates = [d.strftime('%Y-%m-%d') for d in data.index]
                
                result[sym] = {
                    'name': quote.get('name', sym),
                    'current_price': quote.get('price', 0),
                    'change_percent': round(((prices[-1] - base) / base) * 100, 2),
                    'normalized': normalized,
                    'dates': dates,
                    'pe_ratio': quote.get('pe_ratio'),
                    'market_cap': quote.get('market_cap', 0)
                }
        except Exception as e:
            print(f"Compare error for {sym}: {e}")
    
    return jsonify(result)

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 StockAI Pro Server Starting...")
    print("="*50)
    print(f"📍 http://{Config.HOST}:{Config.PORT}")
    print("="*50 + "\n")
    app.run(host=Config.HOST, port=Config.PORT, debug=True)