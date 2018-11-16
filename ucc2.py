import common
import csv

doi_file = "../Downloads/ucc_articles_2017_scopus.csv"
output_file = 'ucc_articles_2017_scopus_output.csv'

total_count = 0
open_count = 0
repo_count = 0
cora_count = 0

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
            oadoi = common.Oadoi(doi).parse('cache_only')
            openaire = common.Openaire(doi).parse('cache_only')
            #print(openaire) 
 
            #oadoi_parsed = oadoi.parse()
            if oadoi['classification'] == 'gold' or oadoi['classification'] == 'green' or openaire['classification'] == 'gold' or openaire['classification'] == 'green':
                open_count += 1
                open = True
            if oadoi['in_repo'] == 'true' or openaire['in_repo'] == 'true':
                repo_count += 1
                repo = True
            if oadoi['in_cora'] == 'true' or openaire['in_cora'] == 'true':
                cora_count += 1
                cora = True
            #openaire = common.Openaire(doi).fetch() #response('cache_only')
            #print(openaire)
            writer.writerow({'DOI':doi, 'Year':year, 'open': open, 'repo':repo, 'cora':cora})
    
print("total_count:{0}".format(total_count))
print("open_count:{0}".format(open_count))
print("repo_count:{0}".format(repo_count))
print("cora_count:{0}".format(cora_count))
