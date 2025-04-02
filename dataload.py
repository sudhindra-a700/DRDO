import pandas as pd
import sqlite3

class DataLoader:
    """Handles loading data from SQLite database."""
    DB_PATH = r"C:\Users\Sudhindra Prakash\Desktop\java project\.venv\Backend\DRDO_Normalized_Updated_Names.db"

    @staticmethod
    def load_interviewees():
        """Loads registered interviewees from the database."""
        try:
            with sqlite3.connect(DataLoader.DB_PATH) as conn:
                # Join Interviewee and Interviewee_Interests for full interviewee data
                query = """
                    SELECT i.interviewee_id AS user_id, i.name, i.email, i.phone, ii.field_of_interest AS core_field
                    FROM Interviewee i
                    LEFT JOIN Interviewee_Interests ii ON i.interviewee_id = ii.interviewee_id
                """
                df = pd.read_sql_query(query, conn)
            return df
        except Exception as e:
            print(f"❌ Error loading interviewees: {e}")
            return pd.DataFrame()

    @staticmethod
    def load_interviewers():
        """Loads interviewer data from the database."""
        try:
            with sqlite3.connect(DataLoader.DB_PATH) as conn:
                # Join Interviewer and Interviewers for full interviewer data
                query = """
                    SELECT i.interviewer_id, i.name, i.email, i.phone, ie.expertise_field AS field_of_expertise
                    FROM Interviewer i
                    LEFT JOIN Interviewer_Expertise ie ON i.interviewer_id = ie.interviewer_id
                """
                df = pd.read_sql_query(query, conn)
            return df
        except Exception as e:
            print(f"❌ Error loading interviewers: {e}")
            return pd.DataFrame()

    @staticmethod
    def load_skills():
        """Loads skills data by joining Interviewee_Interests and Interviewers tables."""
        try:
            with sqlite3.connect(DataLoader.DB_PATH) as conn:
                query = """
                    SELECT ii.interviewee_id AS user_id, ii.field_of_interest AS skill 
                    FROM Interviewee_Interests ii
                    UNION ALL
                    SELECT ie.interviewer_id, ie.expertise_field AS skill 
                    FROM Interviewer_Expertise ie
                """
                df = pd.read_sql_query(query, conn)
            return df
        except Exception as e:
            print(f"❌ Error loading skills: {e}")
            return pd.DataFrame()