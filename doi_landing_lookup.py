import csv
import requests

with open('output.csv', 'w') as csvfile:
    fieldnames = ['Title', 'Year', 'DOI', 'Landing']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()

    with open('tcd_2015_100.csv', 'r', encoding='utf-8', errors='ignore') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            doi = row['DOI']
            print(doi)
            resp = requests.head("http://doi.org/{0}".format(doi))
            print(resp.status_code)
            if resp.status_code == 303:
                redirect_url = resp.headers['Location']
                if "http://linkinghub.elsevier.com/retrieve" in redirect_url:
                    redirect_url.replace("http://linkinghub.elsevier.com/retrieve", "http://www.sciencedirect.com/science/article
                print(redirect_url)
                writer.writerow({'Title': row['Title'], 'Year' : row['Year'], 'DOI' : row['DOI'], 'Landing' : redirect_url })

# in practice the doi redirects to another publisher-specific resolver, leading to one or more further redirects

        