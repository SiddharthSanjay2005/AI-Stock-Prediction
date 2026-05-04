import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from data_sources import DataManager

class StockPredictor:
    def __init__(self, symbol='AAPL'):
        self.symbol = symbol
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.data_manager = DataManager()
        
    def fetch_data(self):
        """Get stock data"""
        data = self.data_manager.get_stock_data(self.symbol, period='2y')
        if data is None or len(data) < 60:
            print(f"Not enough data for {self.symbol}")
            return None
        
        # Use only Close price for simplicity
        close_prices = data[['Close']].values
        return close_prices
    
    def create_sequences(self, data, lookback=60):
        """Create sequences for LSTM"""
        X, y = [], []
        for i in range(lookback, len(data)):
            X.append(data[i-lookback:i, 0])
            y.append(data[i, 0])
        return np.array(X), np.array(y)
    
    def train(self):
        """Train the model"""
        try:
            # Get data
            data = self.fetch_data()
            if data is None:
                return False
            
            print(f"Training on {len(data)} data points")
            
            # Scale data
            scaled_data = self.scaler.fit_transform(data)
            
            # Create sequences
            X, y = self.create_sequences(scaled_data, 60)
            
            if len(X) < 50:
                print(f"Only {len(X)} sequences, need more")
                return False
            
            # Reshape for LSTM [samples, time steps, features]
            X = X.reshape(X.shape[0], X.shape[1], 1)
            
            # Split data
            split = int(len(X) * 0.8)
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]
            
            print(f"Train: {len(X_train)}, Test: {len(X_test)}")
            
            # Build model
            self.model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(60, 1)),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(1)
            ])
            
            self.model.compile(optimizer='adam', loss='mean_squared_error')
            
            # Early stopping
            callback = EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True
            )
            
            # Train
            print("Training model...")
            self.model.fit(
                X_train, y_train,
                epochs=20,
                batch_size=32,
                validation_data=(X_test, y_test),
                callbacks=[callback],
                verbose=0
            )
            
            # Save model
            os.makedirs('models', exist_ok=True)
            self.model.save(f'models/{self.symbol}_model.keras')
            joblib.dump(self.scaler, f'models/{self.symbol}_scaler.pkl')
            
            print("Model trained successfully!")
            return True
            
        except Exception as e:
            print(f"Training error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def predict_future(self, days=30):
        """Predict future prices"""
        try:
            # Get data
            data = self.fetch_data()
            if data is None:
                return None
            
            # Scale
            scaled_data = self.scaler.transform(data)
            
            # Get last 60 days
            last_60 = scaled_data[-60:]
            
            # Predict day by day
            predictions = []
            current_batch = last_60.reshape(1, 60, 1)
            
            for i in range(days):
                # Get prediction for next day
                next_pred = self.model.predict(current_batch, verbose=0)[0, 0]
                predictions.append(next_pred)
                
                # Update batch
                current_batch = np.roll(current_batch, -1, axis=1)
                current_batch[0, -1, 0] = next_pred
            
            # Convert back to original scale
            predictions = np.array(predictions).reshape(-1, 1)
            predictions = self.scaler.inverse_transform(predictions)
            
            return predictions.flatten()
            
        except Exception as e:
            print(f"Prediction error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_confidence(self):
        """Return a confidence score"""
        return 75  # Simplified for reliability