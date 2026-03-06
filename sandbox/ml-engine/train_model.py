import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

def train_complexity_predictor():
    print("Loading AST dataset...")
    
    # 1. Load the data
    df = pd.read_csv("real_world_ast_dataset.csv")
    df = df.dropna()
    
    # 2. Separate Features (X) and Labels (y)
    # The drop(columns) automatically handles however many features we added!
    X = df.drop(columns=['Complexity']) 
    y = df['Complexity']
    
    # 3. Split data (80% training, 20% testing)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples...\n")
    
    # 4. Train the Random Forest
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # 5. Predict and Evaluate
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    
    print(f"Model Accuracy: {accuracy * 100:.2f}%\n")
    print("Detailed Classification Report:")
    print(classification_report(y_test, predictions, zero_division=0))
    
    # 6. Save Model
    joblib.dump(model, 'complexity_model.pkl')
    print("\nModel saved to 'complexity_model.pkl'!")

if __name__ == "__main__":
    train_complexity_predictor()