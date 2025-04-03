from dataload import DataLoader
from sklearn.linear_model import LinearRegression
from cossimilarity import SimilarityCalculator

class MatchingService:
    """Computes matching scores using live interviewee data."""

    @staticmethod
    def compute_matching_scores():
        interviewers_df = DataLoader.load_interviewers()
        if interviewers_df.empty:
            print("❌ No interviewer data for matching score computation.")
            return {}

        matching_scores = {}
        for interviewee in DataLoader.get_interviewees():
            interviewee_id = interviewee["user_id"]
            interviewee_skills = DataLoader.get_skills_for_user(interviewee_id)
            interviewee_field = str(interviewee["core_field"] or "").lower()

            max_score = 0
            best_interviewer = None
            for _, interviewer in interviewers_df.iterrows():
                interviewer_id = interviewer["interviewer_id"]
                interviewer_skills = DataLoader.get_skills_for_user(interviewer_id)
                interviewer_field = str(interviewer["field_of_expertise"] or "").lower()

                common_skills = len(interviewee_skills & interviewer_skills)
                skill_score = common_skills / max(len(interviewee_skills), 1)
                field_score = 1.0 if interviewee_field == interviewer_field else 0.0
                combined_score = 0.6 * field_score + 0.4 * skill_score

                if combined_score > max_score:
                    max_score = combined_score
                    best_interviewer = interviewer_id

            if best_interviewer:
                matching_scores[(interviewee_id, best_interviewer)] = max_score

        print(f"✅ Computed matching scores for {len(matching_scores)} pairs.")
        return matching_scores

    @staticmethod
    def train_linear_regression():
        cosine_scores = SimilarityCalculator.compute_similarity()
        jaccard_scores = SimilarityCalculator.compute_jaccard_similarity()
        matching_scores = MatchingService.compute_matching_scores()

        if not all([cosine_scores, jaccard_scores, matching_scores]):
            print("❌ Insufficient data for regression training.")
            return None

        X, y = [], []
        all_pairs = set(cosine_scores.keys()) & set(jaccard_scores.keys()) & set(matching_scores.keys())
        for pair in all_pairs:
            cosine = cosine_scores.get(pair, 0)
            jaccard = jaccard_scores.get(pair, 0)
            match = matching_scores.get(pair, 0)
            X.append([cosine, jaccard, match])
            y.append(0.4 * cosine + 0.3 * jaccard + 0.3 * match)

        if not X or not y:
            print("❌ No valid data pairs for regression.")
            return None

        model = LinearRegression()
        model.fit(X, y)
        print(f"✅ Regression model trained with {len(X)} data points.")
        return model