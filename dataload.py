import sqlite3

class DataLoader:
    """Handles loading data from SQLite database in real-time."""
    DB_PATH = r"C:\Users\Sudhindra Prakash\Desktop\java project\.venv\Backend\DRDO_Normalized_Updated_Names.db"

    @staticmethod
    def get_interviewees():
        """Yields interviewee data one-by-one from the database."""
        try:
            with sqlite3.connect(DataLoader.DB_PATH) as conn:
                conn.row_factory = sqlite3.Row  # Return rows as dictionaries
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT i.interviewee_id AS user_id, i.name, i.email, i.phone, ii.field_of_interest AS core_field
                    FROM Interviewee i
                    LEFT JOIN Interviewee_Interests ii ON i.interviewee_id = ii.interviewee_id
                """)
                for row in cursor.fetchall():
                    yield dict(row)
        except Exception as e:
            print(f"❌ Error fetching interviewees: {e}")
            yield from []  # Empty iterator on failure

    @staticmethod
    def load_interviewers():
        """Loads interviewer data as a DataFrame (assumed less volatile)."""
        try:
            with sqlite3.connect(DataLoader.DB_PATH) as conn:
                import pandas as pd
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
    def get_skills_for_user(user_id):
        """Fetches skills for a specific user (interviewee or interviewer)."""
        try:
            with sqlite3.connect(DataLoader.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT field_of_interest AS skill 
                    FROM Interviewee_Interests 
                    WHERE interviewee_id = ?
                    UNION ALL
                    SELECT expertise_field AS skill 
                    FROM Interviewer_Expertise 
                    WHERE interviewer_id = ?
                """, (user_id, user_id))
                skills = {row[0] for row in cursor.fetchall() if row[0]}
                return skills
        except Exception as e:
            print(f"❌ Error loading skills for {user_id}: {e}")
            return set()