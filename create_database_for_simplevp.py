import sqlite3, os

conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "simpleVP.db"))
cur = conn.cursor()

with conn:
    cur.execute(
        """
        CREATE TABLE Jobber (
	        JobberPK INTEGER PRIMARY KEY,
	        Navn TEXT NOT NULL,
	        Type TEXT,
	        Quantity INTEGER,
	        Unit TEXT,
            Deadline TEXT,
            ProjectManager TEXT,
            SourceLang TEXT,
            TargetLang TEXT,
            VendorID TEXT, 
            SourceFiles INTEGER,
            StartTime TEXT,
            EndTime TEXT,
            Delievered INTEGER,
            UNIQUE(VendorID)
		)
        """
    )

