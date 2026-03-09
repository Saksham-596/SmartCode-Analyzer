import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

def train_complexity_predictor():
    print("Loading AST dataset...")
    
    df = pd.read_csv("real_world_ast_dataset.csv")
    df = df.dropna()
    
    X = df.drop(columns=['Complexity']) 
    y = df['Complexity']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples...\n")
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    
    print(f"Model Accuracy: {accuracy * 100:.2f}%\n")
    print("Detailed Classification Report:")
    print(classification_report(y_test, predictions, zero_division=0))
    
    joblib.dump(model, 'complexity_model.pkl')
    print("\nModel saved to 'complexity_model.pkl'!")

if __name__ == "__main__":
    train_complexity_predictor()