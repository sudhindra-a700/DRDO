import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from dataload import DataLoader
from cossimilarity import SimilarityCalculator
from matching import MatchingService
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class InterviewScheduler:
    def __init__(self):
        self.interviewers = DataLoader.load_interviewers()
        self.similarity_scores = SimilarityCalculator.compute_similarity()
        self.matching_scores = MatchingService.compute_matching_scores()
        self.schedule = []
        self.vectorizer = TfidfVectorizer()
        self.interviewer_tfidf = self.vectorizer.fit_transform(
            self.interviewers["field_of_expertise"].fillna('').astype(str).tolist()
        )
        self.available_slots = self._initialize_slots()

    def _initialize_slots(self):
        """Pre-allocate available slots for each interviewer."""
        start_date = datetime(2025, 5, 1)
        end_date = datetime(2025, 5, 5)
        daily_start = timedelta(hours=10)
        daily_end = timedelta(hours=17)
        lunch_start = timedelta(hours=13)
        lunch_end = lunch_start + timedelta(minutes=30)
        slot_duration = timedelta(minutes=30)
        break_after_3 = timedelta(minutes=2)

        slots = {}
        with sqlite3.connect(DataLoader.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Interviewer_ID, date, time FROM interview_schedule")
            taken_slots = cursor.fetchall()

        taken_by_interviewer = {}
        for interviewer_id, date, time in taken_slots:
            if interviewer_id not in taken_by_interviewer:
                taken_by_interviewer[interviewer_id] = set()
            start_time = time.split('-')[0]
            taken_by_interviewer[interviewer_id].add((date, start_time))

        for _, interviewer in self.interviewers.iterrows():
            interviewer_id = interviewer['interviewer_id']
            slots[interviewer_id] = []
            current_date = start_date
            while current_date <= end_date:
                current_time = daily_start
                interviews_done = 0
                while current_time + slot_duration <= daily_end:
                    if lunch_start <= current_time < lunch_end:
                        current_time = lunch_end
                        continue
                    if interviews_done > 0 and interviews_done % 3 == 0:
                        current_time += break_after_3
                    slot_start = (datetime.combine(datetime.today(), datetime.min.time()) + current_time).strftime('%H:%M')
                    slot_key = (current_date.strftime('%Y-%m-%d'), slot_start)
                    if interviewer_id not in taken_by_interviewer or slot_key not in taken_by_interviewer[interviewer_id]:
                        slots[interviewer_id].append({
                            "Date": current_date.strftime('%Y-%m-%d'),
                            "Start_Time": slot_start,
                            "End_Time": (datetime.combine(datetime.today(), datetime.min.time()) + current_time + slot_duration).strftime('%H:%M')
                        })
                    current_time += slot_duration
                    interviews_done += 1
                current_date += timedelta(days=1)

        print(f"✅ Initialized {sum(len(slots[i]) for i in slots)} available slots across {len(slots)} interviewers.")
        return slots

    def update_scores_for_candidate(self, candidate_id, core_field):
        """Incrementally update similarity and matching scores for a new candidate."""
        candidate_field = str(core_field or "").strip()
        if not candidate_field:
            return

        # Update similarity score
        candidate_tfidf = self.vectorizer.transform([candidate_field])
        relevance_scores = cosine_similarity(candidate_tfidf, self.interviewer_tfidf)[0]
        for idx, interviewer in self.interviewers.iterrows():
            interviewer_id = interviewer['interviewer_id']
            score = relevance_scores[idx]
            if score > 0:
                self.similarity_scores[(candidate_id, interviewer_id)] = score

        # Update matching score
        candidate_skills = DataLoader.get_skills_for_user(candidate_id)
        for _, interviewer in self.interviewers.iterrows():
            interviewer_id = interviewer['interviewer_id']
            interviewer_field = str(interviewer['field_of_expertise'] or "").lower()
            interviewer_skills = DataLoader.get_skills_for_user(interviewer_id)
            common_skills = len(candidate_skills & interviewer_skills)
            skill_score = common_skills / max(len(candidate_skills), 1)
            field_score = 1.0 if candidate_field.lower() == interviewer_field else 0.0
            combined_score = 0.6 * field_score + 0.4 * skill_score
            if combined_score > 0:
                self.matching_scores[(candidate_id, interviewer_id)] = combined_score

        print(f"✅ Updated scores for candidate {candidate_id}")

    def generate_schedule(self):
        scheduled_interviewees = set()
        for interviewee in DataLoader.get_interviewees():
            interviewee_id = interviewee['user_id']
            if interviewee_id in scheduled_interviewees:
                continue
            self._schedule_candidate(interviewee_id, interviewee['core_field'], interviewee['email'], scheduled_interviewees)

        print(f"✅ Generated schedule with {len(self.schedule)} interviews.")

    def schedule_single_candidate(self, candidate_id):
        """Schedule an interview for a single candidate using pre-allocated slots."""
        with sqlite3.connect(DataLoader.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.interviewee_id AS user_id, i.email, ii.field_of_interest AS core_field
                FROM Interviewee i
                LEFT JOIN Interviewee_Interests ii ON i.interviewee_id = ii.interviewee_id
                WHERE i.interviewee_id = ?
            """, (candidate_id,))
            interviewee = cursor.fetchone()
            if not interviewee:
                print(f"❌ Candidate {candidate_id} not found.")
                return

        self._schedule_candidate(candidate_id, interviewee['core_field'], interviewee['email'], set())

    def _schedule_candidate(self, candidate_id, core_field, email, scheduled_interviewees):
        """Helper method to schedule a candidate."""
        interviewee_field = str(core_field or "").lower()
        matching_interviewers = []
        for _, interviewer in self.interviewers.iterrows():
            interviewer_id = interviewer['interviewer_id']
            interviewer_field = str(interviewer['field_of_expertise'] or "").lower()
            if interviewee_field != interviewer_field:
                continue
            pair = (candidate_id, interviewer_id)
            sim_score = self.similarity_scores.get(pair, 0)
            match_score = self.matching_scores.get(pair, 0)
            if sim_score == 0 or match_score == 0:
                continue
            combined_score = sim_score + match_score
            matching_interviewers.append({
                'interviewer_id': interviewer_id,
                'combined_score': combined_score,
                'email': interviewer['email']
            })

        if not matching_interviewers:
            print(f"❌ No matching interviewers for {candidate_id}")
            return

        matching_interviewers.sort(key=lambda x: (-x['combined_score'], x['interviewer_id']))
        best_interviewer = matching_interviewers[0]
        interviewer_id = best_interviewer['interviewer_id']
        interviewer_email = best_interviewer['email']

        if not self.available_slots[interviewer_id]:
            print(f"❌ No available slots for interviewer {interviewer_id}")
            return

        slot = self.available_slots[interviewer_id].pop(0)  # Take the earliest slot
        self.schedule.append({
            "Date": slot["Date"],
            "Start_Time": slot["Start_Time"],
            "End_Time": slot["End_Time"],
            "Interviewee_ID": candidate_id,
            "Interviewer_ID": interviewer_id,
            "Interviewer_Email": interviewer_email,
            "Interviewee_Email": email
        })
        scheduled_interviewees.add(candidate_id)
        print(f"✅ Scheduled {candidate_id} with {interviewer_id} on {slot['Date']} {slot['Start_Time']}")

    def store_schedule_in_db(self):
        try:
            conn = sqlite3.connect(DataLoader.DB_PATH)
            df_schedule = pd.DataFrame(self.schedule)
            df_schedule = df_schedule.rename(columns={"Date": "date", "Start_Time": "time"})
            df_schedule["time"] = df_schedule["time"] + "-" + df_schedule["End_Time"]
            df_schedule = df_schedule.drop(columns=["End_Time"])
            df_schedule.to_sql('interview_schedule', conn, if_exists='append', index=False)
            conn.close()
            self.schedule.clear()  # Clear after storing to avoid duplicates
            print("✅ Schedule stored in database.")
        except Exception as e:
            print(f"❌ Error storing schedule: {e}")