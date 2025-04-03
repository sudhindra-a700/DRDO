from dataload import DataLoader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SimilarityCalculator:
    """Computes cosine similarity between interviewers and interviewees using live data."""

    @staticmethod
    def compute_similarity():
        try:
            interviewers_df = DataLoader.load_interviewers()
            if interviewers_df.empty:
                print("❌ No interviewer data available.")
                return {}

            interviewer_fields = interviewers_df["field_of_expertise"].fillna('').astype(str).tolist()
            vectorizer = TfidfVectorizer()
            interviewer_tfidf = vectorizer.fit_transform(interviewer_fields)

            similarity_map = {}
            for interviewee in DataLoader.get_interviewees():
                interviewee_id = interviewee["user_id"]
                interviewee_field = str(interviewee["core_field"] or "").strip()
                if not interviewee_field:
                    continue

                interviewee_tfidf = vectorizer.transform([interviewee_field])
                relevance_scores = cosine_similarity(interviewee_tfidf, interviewer_tfidf)[0]

                max_score = 0
                best_interviewer = None
                for j, interviewer in interviewers_df.iterrows():
                    score = relevance_scores[j]
                    if score > max_score:
                        max_score = score
                        best_interviewer = interviewer["interviewer_id"]
                if best_interviewer:
                    similarity_map[(interviewee_id, best_interviewer)] = max_score

            print(f"✅ Computed similarity scores for {len(similarity_map)} interviewee-interviewer pairs.")
            return similarity_map

        except Exception as e:
            print(f"❌ Error computing similarity: {e}")
            return {}

    @staticmethod
    def compute_jaccard_similarity():
        try:
            interviewers_df = DataLoader.load_interviewers()
            if interviewers_df.empty:
                print("❌ No interviewer data for Jaccard calculation.")
                return {}

            jaccard_scores = {}
            for interviewee in DataLoader.get_interviewees():
                interviewee_id = interviewee["user_id"]
                e_set = set(str(interviewee["core_field"] or "").lower().split())
                if not e_set:
                    continue

                for _, interviewer in interviewers_df.iterrows():
                    i_set = set(str(interviewer["field_of_expertise"] or "").lower().split())
                    intersection = len(e_set & i_set)
                    union = len(e_set | i_set)
                    score = intersection / union if union != 0 else 0
                    jaccard_scores[(interviewee_id, interviewer["interviewer_id"])] = score

            return jaccard_scores

        except Exception as e:
            print(f"❌ Error computing Jaccard similarity: {e}")
            return {}