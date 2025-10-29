import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
from dataload import DataLoader
from cossimilarity import SimilarityCalculator
from matching import MatchingService

def plot_scientist_level_residuals():
    """
    Trains the scientist level prediction model and plots its residuals.
    """
    print("--- Generating Scientist Level Residual Plot ---")
    try:
        df = DataLoader.load_interviewees()

        if df.empty:
            print("❌ No interviewee data found for model training.")
            return

        # Ensure required fields exist
        required_cols = {'experience', 'gate_score', 'Scientist_Level_Eligible'}
        if not required_cols.issubset(df.columns):
            print(f"❌ Required fields missing in interviewee data. Need: {required_cols}")
            return

        # 1. Get Data (replicating logic from machine_learning.py)
        features = df[['experience', 'gate_score']].fillna(0)
        y_true = df['Scientist_Level_Eligible'].astype('category').cat.codes

        if y_true.empty:
            print("❌ No labels found for training.")
            return

        # 2. Train Model
        model = LinearRegression()
        model.fit(features, y_true)

        # 3. Get Predictions
        y_pred = model.predict(features)

        # 4. Calculate Residuals
        residuals = y_true - y_pred

        # 5. Plot
        plt.figure(figsize=(10, 6))
        plt.scatter(y_pred, residuals, alpha=0.6)
        plt.axhline(y=0, color='red', linestyle='--', linewidth=2)
        plt.title('Residual Plot for Scientist Level Prediction', fontsize=16)
        plt.xlabel('Predicted Scientist Level (Coded)', fontsize=12)
        plt.ylabel('Residuals (Actual - Predicted)', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.5)
        
        # Save the plot
        plot_filename = 'scientist_level_residuals.png'
        plt.savefig(plot_filename)
        plt.close()

        print(f"✅ Successfully generated and saved '{plot_filename}'")

    except Exception as e:
        print(f"❌ Error generating scientist level residual plot: {e}")

def plot_matching_score_residuals():
    """
    Trains the combined matching score model and plots its residuals.
    """
    print("\n--- Generating Combined Matching Score Residual Plot ---")
    try:
        # 1. Get Data (replicating logic from matching.py)
        cosine_scores = SimilarityCalculator.compute_similarity()
        jaccard_scores = SimilarityCalculator.compute_jaccard_similarity()
        matching_scores = MatchingService.compute_matching_scores()

        if not all([cosine_scores, jaccard_scores, matching_scores]):
            print("❌ Insufficient data for regression training. One of the score maps is empty.")
            return

        X, y_true_list = [], []
        all_pairs = set(cosine_scores.keys()) & set(jaccard_scores.keys()) & set(matching_scores.keys())
        
        if not all_pairs:
            print("❌ No common (interviewee, interviewer) pairs found across all scoring methods.")
            return

        for pair in all_pairs:
            cosine = cosine_scores.get(pair, 0)
            jaccard = jaccard_scores.get(pair, 0)
            match = matching_scores.get(pair, 0)
            X.append([cosine, jaccard, match])
            # This is the "actual" value (y_true) as defined in your matching.py
            y_true_list.append(0.4 * cosine + 0.3 * jaccard + 0.3 * match)

        if not X or not y_true_list:
            print("❌ No valid data pairs for regression.")
            return

        y_true = np.array(y_true_list)

        # 2. Train Model
        model = LinearRegression()
        model.fit(X, y_true)

        # 3. Get Predictions
        y_pred = model.predict(X)

        # 4. Calculate Residuals
        residuals = y_true - y_pred

        # 5. Plot
        plt.figure(figsize=(10, 6))
        plt.scatter(y_pred, residuals, alpha=0.6)
        plt.axhline(y=0, color='red', linestyle='--', linewidth=2)
        plt.title('Residual Plot for Combined Matching Score', fontsize=16)
        plt.xlabel('Predicted Combined Score', fontsize=12)
        plt.ylabel('Residuals (Actual - Predicted)', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.5)
        
        # Save the plot
        plot_filename = 'matching_score_residuals.png'
        plt.savefig(plot_filename)
        plt.close()
        
        print(f"✅ Successfully generated and saved '{plot_filename}'")

    except Exception as e:
        print(f"❌ Error generating matching score residual plot: {e}")

if __name__ == "__main__":
    print("Starting Residual Plot Generation...")
    
    # You may need to install matplotlib and numpy:
    # pip install matplotlib numpy
    
    plot_scientist_level_residuals()
    plot_matching_score_residuals()
    
    print("\nAll plots generated.")
