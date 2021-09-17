import sqlite3, time, datetime, requests, json, os


class Database:
    def __init__(self):
        self.PATH = os.path.dirname(__file__)
        self.conn = sqlite3.connect(os.path.join(self.PATH, "simpleVP.db"))
        self.cur = self.conn.cursor()
    
    def update(self, endpoint, mail, password):
        
        s = requests.Session()

        baseUrl = endpoint + "/vendors/"

        #log in
        body = {"email": mail, "password": password}
        s.post(baseUrl + "sign-in", json=body)
    
        try:
            resp = s.get(baseUrl + "jobs")
            resp.raise_for_status()
        except requests.exceptions.HTTPError:
            return "!!404 no connection!!"

        respPrep = json.loads(resp.text)

        #List for checking items in database which are delievered.
        jobs_in_progress = []

        for jobb in respPrep:
            if jobb["overview"]["status"] == "IN_PROGRESS":
                
                jobs_in_progress.append(str(jobb["id"])) #List can only consist of str

                dictionary = {
                    "Navn" : jobb["overview"].get("projectName"),
                    "Type" : jobb["overview"].get("type"),
                    "ProjectManager" : (jobb["overview"]["projectManager"]["firstName"] + " " + jobb["overview"]["projectManager"]["lastName"]),
                    "SourceLang" : jobb["overview"].get("sourceLanguage").get("name"),
                    "TargetLang" : jobb["overview"].get("targetLanguages")[0].get("name"),
                    "VendorID" : jobb["id"]
                    }
                #Value
                try:  
                    dictionary["Quantity"] = jobb["overview"]["jobQuantities"]["weightedQuantities"][0]["value"]
                except:
                    dictionary["Quantity"] = 0
                #Unit
                try:
                    dictionary["Unit"] = jobb["overview"]["jobQuantities"]["weightedQuantities"][0]["unit"]
                    if dictionary["Unit"].endswith("characters each"):
                        dictionary["Unit"] = dictionary["Unit"][0:5]
                except IndexError:
                    dictionary["Unit"] = "???"
        
                #Deadline
                timestamp = jobb["overview"]["deadline"]/1000
                dictionary["Deadline"] = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H.%M.%S")
                
                #SourceFiles
                # --- Enters the job page of each job to see if there are downloadable PPF- files.
                SourceFiles = 0
                try:
                    jobbPageResp = s.get(baseUrl + "jobs/smart/" + jobb['id'])
                    jobbPage = json.loads(jobbPageResp.text)
                except TypeError:
                    jobbPageResp = s.get(baseUrl + "jobs/classic/" + str(jobb['id']))
                    jobbPage = json.loads(jobbPageResp.text)
                
                if jobbPage['sourceFiles'] == []:
                   SourceFiles = 0
                else:
                    for jobb in jobbPage['sourceFiles']:
                        if jobb['name'].lower().endswith(".ppf"):
                            SourceFiles = 1
                
                dictionary['SourceFiles'] = SourceFiles


                try:
                    with self.conn:
                        self.cur.execute("""
                        INSERT INTO Jobber (Navn, Type, Quantity, Unit, Deadline, SourceLang, TargetLang, ProjectManager, VendorID, SourceFiles)
                        VALUES (:Navn, :Type, :Quantity, :Unit, :Deadline, :SourceLang, :TargetLang, :ProjectManager, :VendorID, :SourceFiles)
                        """, dictionary)
                #Unique key constraint: post already exists
                except sqlite3.IntegrityError:
                    pass
        
        self.check_for_missing(jobs_in_progress)
                    
    def show_todays_jobs(self, date, show_all_jobs=False):
        
        context = {
            'am':date + ' 00:00:00',
            'pm':date + ' 23:59:59'
        }
        
        if show_all_jobs:
            with self.conn:
                self.cur.execute(
                    """
                    SELECT *
                    FROM Jobber
                    WHERE Deadline BETWEEN :am AND :pm
                    ORDER BY Deadline
                    """, context)
                    
                dlToday = self.cur.fetchall()

        else:  
            with self.conn:
                self.cur.execute(
                    """
                    SELECT *
                    FROM Jobber
                    WHERE Deadline BETWEEN :am AND :pm AND SourceFiles == 1
                    ORDER BY Deadline
                    """, context)
                    
                dlToday = self.cur.fetchall()

        #Stringlist to be printed in the widget
        stringList = []
        
        for item in dlToday:
            if item[10] == 0:
                flag = "DISABLED"
            elif item[2] == "Translation" or item[2] == "revision":
                flag = "DISABLED"              
            else:

                if item[13] == 1:
                    flag = "DELIEVERED"
                elif item[12] != None:
                    flag = "UP"
                elif item[11] != None:
                    flag = "DOWN"
                else:
                    flag = "NEUTRAL"

            x = " | ".join(item[1:3])
            x = " | ".join((item[5], x))
            unit = str(item[3])
            y = " ".join((unit, item[4]))
            #List contains tuples. Each tuple contains string to be printed in widget + respective jobbID)
            #Example: ("16.00.00 | U004711061_ARKI_DEU_NOR | UEB ohne 100 –– 3.155 lines", 3423422, flag)
            stringList.append((" –– ".join([x, y]), item[9], flag))
            
        return stringList

    def check_for_missing(self, jobs_in_progress):
        #During update, this functions controls which of the uploaded jobs in the database are NOT in progress anymore.
        #If they are registered as uploaded, but not IN PROGRESS, it is assumed they have been delievered.      
        with self.conn:
            self.cur.execute("""
                SELECT VendorID
                FROM Jobber
                WHERE StartTime IS NOT NULL AND EndTime IS NOT NULL;  
                    """)
            uploaded_jobs = self.cur.fetchall()  
        
        for job in uploaded_jobs:
            if job[0] not in jobs_in_progress:
                with self.conn:
                    self.cur.execute("""
                        UPDATE Jobber
                        SET Delievered=1
                        WHERE VendorID=:VendorID;  
                            """, {"VendorID": job[0]})                  

    def add_to_Nedlastinger(self, jobbIDList):
        timeNow = time.strftime("%Y-%m-%d %H:%M:%S")
        with self.conn:
            for VendorID in jobbIDList:
                self.cur.execute(""" 
                UPDATE Jobber
                SET StartTime=:timeNow
                WHERE VendorID = :VendorID;
                """, {"VendorID" : str(VendorID), "timeNow":timeNow})

    def update_Nedlastinger_with_ultime(self, jobbIDList):
        timeNow = time.strftime("%Y-%m-%d %H:%M:%S")
        with self.conn:
            for VendorID in jobbIDList:
                self.cur.execute("""
                UPDATE Jobber 
                SET EndTime = :timeNow 
                WHERE VendorID=:VendorID;
                """, {"timeNow": timeNow, "VendorID": str(VendorID)})

    
    def close(self):
        self.cur.close()
        self.conn.close()
        del self
