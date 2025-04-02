from dataload import DataLoader
from sklearn.linear_model import LinearRegression
from cossimilarity import SimilarityCalculator

class MatchingService:
    """
    Computes matching scores using cosine and Jaccard similarity.
    Trains a regression model on both.
    """

    @staticmethod
    def compute_matching_scores():
        interviewees_df = DataLoader.load_interviewees()
        interviewers_df = DataLoader.load_interviewers()
        skills_df = DataLoader.load_skills()

        if interviewees_df.empty or interviewers_df.empty:
            print("❌ Data is empty for matching score computation.")
            return {}

        matching_scores = {}
        skills_dict = skills_df.groupby("user_id")["skill"].apply(set).to_dict()

        for _, interviewee in interviewees_df.iterrows():
            interviewee_id = interviewee["user_id"]
            interviewee_skills = skills_dict.get(interviewee_id, set())
            interviewee_field = str(interviewee["core_field"]).lower()

            max_score = 0
            best_interviewer = None
            for _, interviewer in interviewers_df.iterrows():
                interviewer_id = interviewer["interviewer_id"]
                interviewer_skills = skills_dict.get(interviewer_id, set())
                interviewer_field = str(interviewer["field_of_expertise"]).lower()

                # Skill-based matching score
                common_skills = len(interviewee_skills & interviewer_skills)
                skill_score = common_skills / max(len(interviewee_skills), 1)

                # Field-based matching score
                field_score = 1.0 if interviewee_field == interviewer_field else 0.0

                # Combine scores
                combined_score = 0.6 * field_score + 0.4 * skill_score
                if combined_score > max_score:
                    max_score = combined_score
                    best_interviewer = interviewer_id

            if best_interviewer:
                matching_scores[(interviewee_id, best_interviewer)] = max_score

        print(f"✅ Computed highest matching scores for {len(matching_scores)} pairs.")
        return matching_scores

    @staticmethod
    def train_linear_regression():
        # Load similarity and matching scores
        cosine_scores = SimilarityCalculator.compute_similarity()
        jaccard_scores = SimilarityCalculator.compute_jaccard_similarity()
        matching_scores = MatchingService.compute_matching_scores()

        if not all([cosine_scores, jaccard_scores, matching_scores]):
            print("❌ Insufficient data for regression training.")
            return None

        # Prepare training data: Combine cosine, Jaccard, and matching scores as features
        X, y = [], []
        all_pairs = set(cosine_scores.keys()) & set(jaccard_scores.keys()) & set(matching_scores.keys())

        for pair in all_pairs:
            interviewee_id, interviewer_id = pair
            cosine = cosine_scores.get(pair, 0)
            jaccard = jaccard_scores.get(pair, 0)
            match = matching_scores.get(pair, 0)
            X.append([cosine, jaccard, match])
            # Target: Combined score (e.g., weighted average)
            y.append(0.4 * cosine + 0.3 * jaccard + 0.3 * match)  # Example weights

        if not X or not y:
            print("❌ No valid data pairs for regression.")
            return None

        model = LinearRegression()
        model.fit(X, y)
        print(f"✅ Regression model trained with {len(X)} data points.")
        return model