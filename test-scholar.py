import scholar
import csv
import requests
import os
import pickle

# option 1 use scholar.py
querier = scholar.ScholarQuerier()
scholar.ScholarConf.COOKIE_JAR_FILE = 'cookie.txt'
querier.save_cookies()
settings = scholar.ScholarSettings()
querier.apply_settings(settings)
query = scholar.SearchScholarQuery()


def searchScholar(searchphrase, year):
    query.set_scope(True)
    query.set_phrase(searchphrase)
    query.set_timeframe(start=year-1, end=year+1)
    query.get_url()
    print(query.get_url())
    querier.send_query(query)
    #print(querier.articles)
    return querier.articles
    #return scholar.csv(querier)
    
with open('../gs-test/tcd_2015_100.csv', 'r', encoding='utf-8', errors='ignore') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        title = row['Title']
        doi = row['DOI']
        year = int(row['Year'])
        file_name = doi.strip().replace('/', '_') + '.bin'
        dir = "./cache/gs"
        os.makedirs(dir, exist_ok=True)
        file_path = "./cache/gs/{0}".format(file_name)
        if os.path.isfile(file_path):
            print("cached")
        else: 
            print("making call")
            response = searchScholar(title, year)
            if len(response) > 0:
                pickle.dump(response, open( file_path, "wb" ) )
                print(response)
                print("entering looop")
                for art in response:
                    print(art.__getitem__('title'))
                    print(art.__getitem__('url_pdf'))

# option 2: direct request with gbs output (as used by unpaywall)
'''with open('tcd_2015_100.csv', 'r', encoding='utf-8', errors='ignore') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        title = row['Title']
        doi = row['DOI']
        print(doi)
        file_name = doi.strip().replace('/', '_') + '.json'
        dir = "./cache/gs"
        os.makedirs(dir, exist_ok=True)
        file_path = "./cache/gs/{0}".format(file_name)
        if os.path.isfile(file_path):
            print("cached")
        else: 
            gbs_json_url = "https://scholar.google.com/scholar?as_q=&as_epq={0}&as_occt=title&output=gsb".format(title)
            print(gbs_json_url)
            resp = requests.get(gbs_json_url)
            print(resp.status_code)

            if resp.status_code == 200:
                file = open(file_path, 'w')
                file.write(resp.text)
                file.close()'''