from dataload import DataLoader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SimilarityCalculator:
    """Computes cosine and Jaccard similarity between interviewers and interviewees."""

    @staticmethod
    def compute_similarity():
        try:
            interviewees_df = DataLoader.load_interviewees()
            interviewers_df = DataLoader.load_interviewers()

            if interviewees_df.empty or interviewers_df.empty:
                print("❌ Data is empty for similarity calculation.")
                return {}

            # Extract core fields and expertise as text data
            interviewee_fields = interviewees_df["core_field"].fillna('').astype(str).tolist()
            interviewer_fields = interviewers_df["field_of_expertise"].fillna('').astype(str).tolist()

            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(interviewee_fields + interviewer_fields)

            # Compute cosine similarity between interviewees and interviewers
            relevance_scores = cosine_similarity(
                tfidf_matrix[:len(interviewee_fields)],
                tfidf_matrix[len(interviewee_fields):]
            )

            # Find the highest similarity score per interviewee
            similarity_map = {}
            for i in range(len(interviewees_df)):
                interviewee_id = interviewees_df.iloc[i]["user_id"]
                max_score = 0
                best_interviewer = None
                for j in range(len(interviewers_df)):
                    score = relevance_scores[i, j]
                    if score > max_score:
                        max_score = score
                        best_interviewer = interviewers_df.iloc[j]["interviewer_id"]
                if best_interviewer:
                    similarity_map[(interviewee_id, best_interviewer)] = max_score

            print(f"✅ Computed highest similarity scores for {len(similarity_map)} interviewees.")
            return similarity_map

        except Exception as e:
            print(f"❌ Error computing similarity: {e}")
            return {}
# Jaccard similarity remains unchanged as we won't modify it for this requirement

    @staticmethod
    def compute_jaccard_similarity():
        try:
            interviewees_df = DataLoader.load_interviewees()
            interviewers_df = DataLoader.load_interviewers()

            if interviewees_df.empty or interviewers_df.empty:
                print("❌ Data is empty for Jaccard calculation.")
                return {}

            jaccard_scores = {}
            for _, interviewee in interviewees_df.iterrows():
                e_set = set(str(interviewee["core_field"]).lower().split())

                for _, interviewer in interviewers_df.iterrows():
                    i_set = set(str(interviewer["field_of_expertise"]).lower().split())
                    intersection = len(e_set & i_set)
                    union = len(e_set | i_set)
                    score = intersection / union if union != 0 else 0
                    jaccard_scores[(interviewee["user_id"], interviewer["interviewer_id"])] = score

            return jaccard_scores

        except Exception as e:
            print(f"❌ Error computing Jaccard similarity: {e}")
            return {}