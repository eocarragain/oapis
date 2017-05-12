
import csv
import requests
import os

# option 2: direct request with gbs output (as used by unpaywall)
with open('../scopus_exports/tcd1.csv', 'r', encoding='utf-8', errors='ignore') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        title = row['Title']
        doi = row['DOI']
        print(doi)
        file_name = doi.strip().replace('/', '_') + '.json'
        file_path = "./cache/rg/{0}".format(file_name)
        if os.path.isfile(file_path):
            print("cached")
        else: 
            rg_url = "https://www.researchgate.net/search?query[0]={0}&type=publications".format(doi)
            print(rg_url)
            try:
                resp = requests.get(rg_url)
                print(resp.status_code)
                
                if resp.status_code == 200:
                    file = open(file_path, 'w')
                    file.write(resp.text)
                    file.close()
                else:
                    print(resp.cookies)
            except:
                print("skipping {}".format(doi))