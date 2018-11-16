import common
import csv

doi_file = "../Downloads/scopus.csv"

with open(doi_file, 'r', encoding='utf-8', errors='ignore') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        doi = row['DOI']
        year = int(row['Year'])
        print(doi)
        #oadoi = common.Oadoi(doi).response('cache_only')
        openaire = common.Openaire(doi).response() #response('cache_only')
        #print(openaire)
    
