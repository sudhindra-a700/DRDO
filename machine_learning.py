from typing import BinaryIO

from dataload import DataLoader
from sklearn.linear_model import LinearRegression
import pickle

class MLModelTrainer:
    @staticmethod
    def train_and_save_model(model_output_path):
        try:
            df = DataLoader.load_interviewees()

            if df.empty:
                print("❌ No interviewee data found for model training.")
                return

            # Ensure required fields exist
            if not {'experience', 'gate_score', 'Scientist_Level_Eligible'}.issubset(df.columns):
                print("❌ Required fields missing in interviewee data.")
                return

            features = df[['experience', 'gate_score']].fillna(0)
            # Encode Scientist Level to numeric codes
            labels = df['Scientist_Level_Eligible'].astype('category').cat.codes

            model = LinearRegression()
            model.fit(features, labels)


            with open(model_output_path, 'wb') as model_file:
                pickle.dump(model, model_file)

            print(f"✅ Model saved to {model_output_path}")

        except Exception as e:
            print(f"❌ Error training model: {e}")


if __name__ == "__main__":
    MLModelTrainer.train_and_save_model('scientist_level_model.pkl')
