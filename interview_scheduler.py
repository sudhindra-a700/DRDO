import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from dataload import DataLoader
from cossimilarity import SimilarityCalculator
from matching import MatchingService

class InterviewScheduler:
    def __init__(self):
        self.interviewees = DataLoader.load_interviewees()
        self.interviewers = DataLoader.load_interviewers()
        self.similarity_scores = SimilarityCalculator.compute_similarity()
        self.matching_scores = MatchingService.compute_matching_scores()
        self.schedule = []

    def generate_schedule(self):
        start_date = datetime(2025, 5, 1)
        end_date = datetime(2025, 5, 5)
        daily_start = timedelta(hours=10)
        daily_end = timedelta(hours=17)
        lunch_start = timedelta(hours=13)
        lunch_end = lunch_start + timedelta(minutes=30)
        slot_duration = timedelta(minutes=30)
        break_after_3 = timedelta(minutes=2)

        # Track scheduled interviewees to avoid duplicates
        scheduled_interviewees = set()
        # Dictionary to store each expert's schedule
        expert_schedules = {interviewer['interviewer_id']: [] for _, interviewer in self.interviewers.iterrows()}

        # Process each interviewee
        for _, interviewee in self.interviewees.iterrows():
            interviewee_id = interviewee['user_id']
            interviewee_field = str(interviewee['core_field']).lower()

            # Skip if already scheduled
            if interviewee_id in scheduled_interviewees:
                continue

            # Find all interviewers with the same field
            matching_interviewers = []
            for _, interviewer in self.interviewers.iterrows():
                interviewer_id = interviewer['interviewer_id']
                interviewer_field = str(interviewer['field_of_expertise']).lower()

                # Check if fields match
                if interviewee_field != interviewer_field:
                    continue

                # Check similarity and matching scores
                pair = (interviewee_id, interviewer_id)
                sim_score = self.similarity_scores.get(pair, 0)
                match_score = self.matching_scores.get(pair, 0)

                # Skip if either score is 0
                if sim_score == 0 or match_score == 0:
                    continue

                # Calculate combined score
                combined_score = sim_score + match_score
                matching_interviewers.append({
                    'interviewer_id': interviewer_id,
                    'combined_score': combined_score,
                    'email': interviewer['email']
                })

            # If no matching interviewers found, skip this interviewee
            if not matching_interviewers:
                continue

            # Sort interviewers by combined score (descending) and interviewer_id (ascending)
            matching_interviewers.sort(key=lambda x: (-x['combined_score'], x['interviewer_id']))

            # Select the interviewer with the highest score
            best_interviewer = matching_interviewers[0]
            interviewer_id = best_interviewer['interviewer_id']
            interviewer_email = best_interviewer['email']

            # Schedule the interview within the allowed time frame
            current_date = start_date
            scheduled = False
            while current_date <= end_date and not scheduled:
                current_time = daily_start
                interviews_done = 0

                while current_time + slot_duration <= daily_end:
                    # Skip lunch break
                    if lunch_start <= current_time < lunch_end:
                        current_time = lunch_end
                        continue

                    # Add a break after every 3 interviews
                    if interviews_done > 0 and interviews_done % 3 == 0:
                        current_time += break_after_3

                    # Check if this slot is within the deadline (end_date and daily_end)
                    interview_datetime = datetime.combine(current_date, datetime.min.time()) + current_time
                    deadline_datetime = datetime.combine(end_date, datetime.min.time()) + daily_end
                    if interview_datetime > deadline_datetime:
                        break

                    # Check if the interviewer already has an interview at this time
                    slot_taken = False
                    for scheduled_interview in expert_schedules[interviewer_id]:
                        scheduled_date = datetime.strptime(scheduled_interview['Date'], '%Y-%m-%d')
                        scheduled_start = datetime.strptime(scheduled_interview['Start_Time'], '%H:%M')
                        # Convert scheduled_start to a timedelta
                        scheduled_time_delta = timedelta(hours=scheduled_start.hour, minutes=scheduled_start.minute)
                        scheduled_datetime = datetime.combine(scheduled_date, datetime.min.time()) + scheduled_time_delta
                        current_slot_datetime = datetime.combine(current_date, datetime.min.time()) + current_time
                        if scheduled_datetime == current_slot_datetime:
                            slot_taken = True
                            break

                    if slot_taken:
                        current_time += slot_duration
                        interviews_done += 1
                        continue

                    # Schedule the interview
                    expert_schedules[interviewer_id].append({
                        "Date": current_date.strftime('%Y-%m-%d'),
                        "Start_Time": (datetime.combine(datetime.today(), datetime.min.time()) + current_time).strftime('%H:%M'),
                        "End_Time": (datetime.combine(datetime.today(), datetime.min.time()) + current_time + slot_duration).strftime('%H:%M'),
                        "Interviewee_ID": interviewee_id,
                        "Interviewer_ID": interviewer_id,
                        "Interviewer_Email": interviewer_email,
                        "Interviewee_Email": interviewee['email']
                    })

                    # Mark interviewee as scheduled
                    scheduled_interviewees.add(interviewee_id)
                    scheduled = True
                    break

                current_date += timedelta(days=1)

        # Combine all expert schedules into the final schedule
        for interviewer_id, expert_schedule in expert_schedules.items():
            self.schedule.extend(expert_schedule)

        print(f"✅ Generated schedule with {len(self.schedule)} interviews across {len(expert_schedules)} experts.")

    def store_schedule_in_db(self):
        try:
            conn = sqlite3.connect(DataLoader.DB_PATH)
            df_schedule = pd.DataFrame(self.schedule)
            df_schedule = df_schedule.rename(columns={
                "Date": "date",
                "Start_Time": "time"
            })
            df_schedule["time"] = df_schedule["time"] + "-" + df_schedule["End_Time"]
            df_schedule = df_schedule.drop(columns=["End_Time"])
            df_schedule.to_sql('interview_schedule', conn, if_exists='replace', index=False)
            conn.close()
            print("✅ Schedule stored in the database table 'interview_schedule'.")
        except Exception as e:
            print(f"❌ Error storing schedule in DB: {e}")