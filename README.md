# DRDO - Interviewee-Interviewer Matching Model

This repository contains a basic linear regression model designed to match interviewees with interviewers using cosine similarity. The project aims to optimize pairing in scenarios like recruitment or interviews by quantifying compatibility based on feature similarity.

## Project Overview
- **Purpose**: Automate and improve the matching process between interviewees and interviewers.
- **Methodology**:
  - **Cosine Similarity**: Measures the similarity between feature vectors of interviewees and interviewers.
  - **Linear Regression**: Predicts compatibility scores based on historical or derived data.
- **Use Case**: Ideal for HR systems, recruitment platforms, or research into effective pairing.

## Features
- Computes similarity scores for all possible interviewee-interviewer pairs.
- Predicts and ranks matches using a combination of cosine similarity and regression.
- Outputs a list of recommended pairs with associated compatibility scores.

## Installation
1. **Clone the Repository**:
   ```
   git clone https://github.com/sudhindra-a700/DRDO.git
   ```
2. **Navigate to the Directory**:
   ```
   cd DRDO
   ```
3. **Install Dependencies** (assumes Python; adjust if different):
   ```
   pip install -r requirements.txt
   ```
   Expected dependencies: `numpy`, `scikit-learn`, `pandas`.

## Usage
1. **Prepare Input Data**:
   - Format: CSV file with columns for interviewee and interviewer features (e.g., skills, experience).
   - Example: `data.csv` with rows like:
     ```
     id,type,feature1,feature2,feature3
     1,interviewee,3,5,2
     2,interviewer,4,4,1
     ```
2. **Run the Model**:
   ```
   python main.py --input data.csv
   ```
3. **View Outputs**: Results are printed to the console or saved to a file (depending on implementation).

## Outputs
The model generates a list of interviewee-interviewer matches with compatibility scores. The number and format of outputs depend on the input data and configuration:

- **Structure**: Each output is a pair (interviewee ID, interviewer ID) with a score between 0 and 1 (higher = better match).
- **Number of Outputs**:
  - Default: One best match per interviewee (e.g., if 5 interviewees, expect 5 pairs).
  - Configurable: Can output all possible pairs (`N × M` for `N` interviewees and `M` interviewers) or top `k` matches per interviewee.
- **Example Output** (for 3 interviewees and 4 interviewers):
  ```
  Interviewee 1 -> Interviewer 3 (Score: 0.92)
  Interviewee 2 -> Interviewer 1 (Score: 0.87)
  Interviewee 3 -> Interviewer 4 (Score: 0.79)
  ```
  - Here, 3 outputs are generated, one per interviewee, selecting the highest-scoring interviewer for each.

- **Detailed Example** (all pairs, if configured):
  ```
  Interviewee 1 -> Interviewer 1 (Score: 0.65)
  Interviewee 1 -> Interviewer 2 (Score: 0.88)
  Interviewee 1 -> Interviewer 3 (Score: 0.92)
  Interviewee 1 -> Interviewer 4 (Score: 0.71)
  Interviewee 2 -> Interviewer 1 (Score: 0.87)
  ...
  ```
  - Total: 12 outputs (3 × 4 pairs).

## How It Works
1. **Input Processing**: Reads feature vectors from the input file.
2. **Cosine Similarity**: Calculates similarity for each pair using:
   ```
   cosine_similarity = (A · B) / (||A|| × ||B||)
   ```
3. **Regression**: Adjusts scores or predicts compatibility based on a trained model.
4. **Matching**: Ranks pairs and selects the best matches.

## Requirements
- Python 3.x
- Libraries: `numpy`, `scikit-learn`, `pandas` (see `requirements.txt`).

## License
© 2025 Sudhindra A700. All rights reserved.

## Feedback
We’d love to hear from you! Open an issue or submit a pull request with your thoughts or improvements.
