import common
import csv

doi_file = "scopus_ucc_2017_2019-07-09.csv"

output_file = doi_file.replace(".csv", "_out.csv")
total_count = 0
open_count = 0
repo_count = 0
cora_count = 0
cora_oadoi_count = 0
cora_openaire_count = 0

with open(doi_file, 'r', encoding='utf-8', errors='ignore') as csvfile:
    with open(output_file, 'w', newline='') as csvout:
        fieldnames = ['DOI', 'Year', 'open', 'repo', 'cora']
        writer = csv.DictWriter(csvout, fieldnames=fieldnames)

        writer.writeheader()
        #writer.writerow({'first_name': 'Baked', 'last_name': 'Beans'})

        reader = csv.DictReader(csvfile)
        for row in reader:
            open = False
            repo = False
            cora = False
            total_count += 1
            doi = row['DOI']
            year = int(row['Year'])
            print(doi)
            print(year)
            oadoi = common.Oadoi(doi).parse()
            openaire = common.Openaire(doi).parse()
            #print(openaire) 
 
            #oadoi_parsed = oadoi.parse()
            if oadoi['classification'] == 'gold' or oadoi['classification'] == 'green' or openaire['classification'] == 'gold' or openaire['classification'] == 'green':
                open_count += 1
                open = True
            if oadoi['in_repo'] == 'true' or openaire['in_repo'] == 'true':
                repo_count += 1
                repo = True
            if oadoi['in_cora'] == 'true' or openaire['in_cora'] == 'true':
                print("######################### CORA TRUE")
                cora_count += 1
                cora = True
                if oadoi['in_cora'] == 'true':
                    cora_oadoi_count += 1
                if openaire['in_cora'] == 'true':
                    cora_openaire_count += 1
            #openaire = common.Openaire(doi).fetch() #response('cache_only')
            #print(openaire)
            writer.writerow({'DOI':doi, 'Year':year, 'open': open, 'repo':repo, 'cora':cora})
    
print("total_count:{0}".format(total_count))
print("open_count:{0}".format(open_count))
print("repo_count:{0}".format(repo_count))
print("cora_count:{0}".format(cora_count))
print("cora_oadoi_count:{0}".format(cora_oadoi_count))
print("cora_openaire_count:{0}".format(cora_openaire_count))