import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import joblib

# Load your data
df = pd.read_csv('eco_data.csv')

# Inputs and output
X = df[['energy', 'water', 'heat', 'waste']]
y = df['green_score']

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train
model = LinearRegression()
model.fit(X_train, y_train)

# Save model
joblib.dump(model, 'green_score_model.pkl')
print("✅ Model trained and saved as green_score_model.pkl")
