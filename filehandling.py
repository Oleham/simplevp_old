
import requests, os, json
from requests.exceptions import HTTPError
import time

def deleteJobsLokalDir(mappe):
    for fil in os.listdir(mappe):
        os.remove(os.path.join(mappe, fil))
        
def downloadJobs(selectedJobs, endpoint, email, password, lokalDir):

    baseUrl = "https://" + endpoint + "/vendors/"

    s = requests.Session()

    # Clean the download dir
    os.makedirs(lokalDir, exist_ok=True)
    deleteJobsLokalDir(lokalDir)
    os.chdir(lokalDir)
    
    #log in
    body = {"email": email, "password":password}
    req = s.post(baseUrl + "sign-in", json=body)

    #Se etter jobber som er i progress:
    for jobbID in selectedJobs:  
            #Sjekk jobb-ID: om det kaster en TypeError, er det en integer, altså en IKKE-smart jobb.
            try:
                response = s.get(baseUrl + "jobs/smart/" + jobbID)
                jobbSite = json.loads(response.text)
            
                #sourceFiles er en måte å finne nedlastingsfiler i smart-jobber
                if jobbSite['sourceFiles'][0]["metaCategory"] == "WORK_FILE" and jobbSite['sourceFiles'][0]["downloadable"]:
                    try:
                        fileID = jobbSite["sourceFiles"][0]["id"]
                        fileName = jobbSite["sourceFiles"][0]["name"]

                        response2 = s.get(baseUrl + "jobs/smart/" + jobbID + "/files/" + fileID)
                        response2.raise_for_status()

                        with open(fileName, "wb") as localFile:
                            for chunk in response2.iter_content(chunk_size=100000):
                                localFile.write(chunk)
                        print(f"Downloaded smart job: {fileName}")
                    except:
                        print("Couldn't download smart job")

            #Classic jobb
            except:
                response = s.get(baseUrl + "jobs/classic/" + str(jobbID))
                jobbSite = json.loads(response.text)

                if jobbSite['sourceFiles'] == []:
                    print(f"Ingen sourcefiles for {jobbSite['overview']['projectName']}")
                    continue
                else:
                    for jobb in jobbSite['sourceFiles']:
                    
                        if jobb["category"] == "WORKFILE" and jobb["name"].endswith(".PPF"):
                            try:
                                fileID = jobb["id"]
                                fileName = jobb["name"]

                                response2 = s.get(baseUrl + "jobs/classic/" + str(jobbID) + "/source-files/" + str(fileID))
                                response2.raise_for_status()

                                with open(fileName, "wb") as localFile:
                                    for chunk in response2.iter_content(chunk_size=100000):
                                        localFile.write(chunk)
                                print(f"Downloaded classic job: {fileName}")
                            except:
                                print(f"Couldn't download classic job")

def uploadJobs(job_id_list, endpoint, email, password, tpf_path):
    """
    Uploads file_name in tpf_path to the corresponding job site according to job_id
    """
    base_url = "https://" + endpoint + "/vendors/"

    s = requests.Session()

    #LOGIN
    body = {"email": email, "password": password}
    resp = s.post(base_url + "sign-in", json=body)
    resp.raise_for_status()

    for job_id in job_id_list:
        s.headers.clear()

        # CONSTRUCT HEADERS
        newheaders = {
                "Host": endpoint,
                "Origin": endpoint,
                "Referer": base_url,
                "X-Requested-With": "XMLHttpRequest",
                "TE": "Trailers",
                "Time-Zone-Offset-In-Minutes": "60",
                "Accept": "text/plain, */*; q=0.01",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive"
            }
        s.headers.update(newheaders)
        
        #CLASSIC OR SMART
        if job_id.isdecimal():
            
            # -- CLASSIC --
            #FIND_TPF_FILENAME
            resp = s.get(base_url + "jobs/classic/" + job_id)
            resp.raise_for_status()

            job_page = json.loads(resp.text)
            for file in job_page["sourceFiles"]:
                if file["category"] == "WORKFILE":
                    file_name = file["name"][:-4]
                    file_name += ".TPF"
                    break

            # FILE UPLOAD
            uploadURL = base_url + "jobs/classic/" + job_id + "/target-files"
                
            try:
                with open(os.path.join(tpf_path, file_name), "rb") as f:
                    files = {"file": (file_name, f, "application/octet-stream")}
                    resp = s.post(uploadURL, files=files)
                    resp.raise_for_status()
            
            except FileNotFoundError:
                print("Couldn't find " + file_name + " in folder " + tpf_path)
                continue
            
            # Small delay for server.
            time.sleep(5)

            # FINISH
            try:
                newheaders = {"Content-Type": "text/plain;charset=UTF-8"}
                s.headers.update(newheaders)
                resp = s.put(base_url + "jobs/classic/" + job_id + "/finish")
                resp.raise_for_status()
                print("Uploaded classic job: " + file_name)
            
            except HTTPError as err:
                print("FAILED UPLOAD (classic): " + file_name + ".\nError code: " + str(err.response.status_code) + " Error message: " + str(err.response.reason))
                continue



        else:

            # -- SMART --
            #FIND_TPF_FILENAME
            resp = s.get(base_url + "jobs/smart/" + job_id)
            resp.raise_for_status()

            job_page = json.loads(resp.text)
            for file in job_page["sourceFiles"]:
                if file["metaCategory"] == "WORK_FILE":
                    file_name = file["name"][:-4]
                    file_name += ".TPF"
                    break
            
            #FILE UPLOAD
            uploadURL = base_url + "jobs/smart/" + job_id + "/target-files"

            try:
                with open(os.path.join(tpf_path, file_name), "rb") as f:
                    files = {"file": (file_name, f, "application/octet-stream")}
                    resp = s.post(uploadURL, files=files)
                    resp.raise_for_status()
            except FileNotFoundError:
                print("Couldn't find " + file_name + " in folder " + tpf_path)
                continue
            
            try:
                #GET FILE_ID
                newheaders2 = {"Accept": "application/json, text/plain"}
                s.headers.update(newheaders2)
                
                resp = s.get(uploadURL)
                uploaded_files = json.loads(resp.text)
                file_id = uploaded_files[0]["id"]

                #LANGUAGE
                newheaders3 = {"Content-Type": "application/json;charset=utf-8"}
                s.headers.update(newheaders3)

                resp = s.put(base_url + "jobs/smart/" + job_id + "/target-files/" + file_id + "/languages", json={"languages":[145]})
                resp.raise_for_status()

                #CATEGORY
                newheaders4 = {"Content-Type": "text/plain;charset=UTF-8"}
                s.headers.update(newheaders4)
                
                resp = s.put(base_url + "jobs/smart/" + job_id + "/target-files/" + file_id + "/category", data="CAT_PACKAGE_RETURN")
                resp.raise_for_status()

                #FINISH
                resp = s.put(base_url + "jobs/smart/" + job_id + "/finish")
                resp.raise_for_status()

                print("Uploaded smart job: " + file_name)
            except HTTPError as err:
                print("FAILED UPLOAD: " + file_name + ".\nError code: " + str(err.response.status_code) + " Error message: " + str(err.response.reason))
                continue

                    

            


