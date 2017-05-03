import requests
import hashlib
import os
import json

class Common(object):
    def __init__(self, doi):
        self.doi = doi
        self.cache_dir = "./cache/{0}".format(self.__class__.__name__.lower())
        self.create_cache_dir()
        doi_digest = hashlib.md5(self.doi.encode('utf-8')).hexdigest()
        self.cache_file = os.path.join(self.cache_dir, doi_digest + ".json")

    def create_cache_dir(self):
        os.makedirs(self.cache_dir, exist_ok=True)

    def cache_response(self, response_body):
        file = open(self.cache_file, "w")
        file.write(response_body)
        file.close()

    def handle_lookup(self, handle):
        #skip for now
        return handle
        #todo verify handle format with regex
        url = handle.replace("hdl.handle.net", "hdl.handle.net/api/handles")
        r = requests.get(url)
        if r.status_code == 200:
            if r["values"][0]["data"]["value"]:
                return r["values"][0]["data"]["value"]
        return handle

    def clean_url(self, url):
        url = url.replace("dx.doi.org", "doi.org")
        if "hdl.handle.net" in url:
            url = self.handle_lookup(url)
        return url

    def fetch(self):
        return ""

    def response(self):
        if os.path.isfile(self.cache_file):
            print("cached")
            return open(self.cache_file, 'r').read()
        else:
            print("not cached")
            return self.fetch()

class Dissemin(Common):
    def fetch(self):
        r = requests.get("http://dissem.in/api/{0}".format(self.doi))
        if r.status_code == 404:
            payload = '{{"doi" : "{0}"}}'.format(self.doi)
            r = requests.post('http://dissem.in/api/query', data = payload)

        if r.status_code == 200:
           self.cache_response(r.text)

        return r.text

    def parse(self):
        output = { 'doi' : self.doi }
        raw = json.loads(self.response())
        if not 'paper' in raw:
            output['classification'] = 'Unknown'
            return output

        if 'pdf_url' in raw['paper']:
            output["pref_pdf_url"] = raw['paper']['pdf_url']

        if 'classification' in raw['paper'] and raw['paper']['classification'] == 'OA':
            output["classification"] = 'Gold'
        elif 'pdf_url' in raw['paper']:
            output["classification"] = 'Green'
        else:
            output["classification"] = 'Unknown' 

        all_sources = []
        for record in raw['paper']['records']:
            if 'pdf_url' in record:
                clean = self.clean_url(record['pdf_url'])
                all_sources.append(clean)
        output["all_sources"] = all_sources
        return output



class Oadoi(Common):
    def fetch(self):
        # todo email
        r = requests.get("https://api.oadoi.org/{0}".format(self.doi))
        if r.status_code == 200:
            self.cache_response(r.text)

        return r.text

class OadoiGS(Common):
    def fetch(self):
        # todo email
        r = requests.get("https://api.oadoi.org/gs/cache/{0}".format(self.doi))
        if r.status_code == 200:
            self.cache_response(r.text)

        return r.text

class Crossref(Common):
    def fetch(self):
        r = requests.get("https://api.crossref.org/works/{0}".format(self.doi))
        if r.status_code == 200:
            self.cache_response(r.text)

        return r.text

class Openaire(Common):
    def fetch(self):
        r = requests.get("http://api.openaire.eu/search/publications?doi={0}&format=json".format(self.doi))
        if r.status_code == 200:
            self.cache_response(r.text)
        else:
            print(r.status_code)
        return r.text


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
oa_class = {'Gold' : 0, 'Green' : 0, 'Unknown' : 0}
green_domain = {}
with open("ucc_all.txt") as f:
    for line in f:
        line = line.strip('\n')
        line = line.strip('\r')
        print (line)
        record = Dissemin(line).parse()
        if 'classification' in record:
            oa_class[record['classification']] += 1
            if record['classification'] == 'Green':
                for source in record['all_sources']:
                    try: 
                        source_parts = source.split("/")
                        domain = source_parts[2]
                       if domain in green_domain:
                            green_domain[domain] += 1
                        else:
                            green_domain[domain] = 1
                    except:
                        print("failed to parse")
print(oa_class)
print(green_domain)
df = pd.DataFrame.from_dict(oa_class, 'index')
plot = df.plot(kind='bar')
fig = plot.get_figure()
fig.savefig("/tmp/output.png")

df2 = pd.DataFrame.from_dict(green_domain, 'index')
plot2 = df2.plot(kind='bar')
fig2 = plot2.get_figure()
fig2.savefig("/tmp/output2.png")
#        Crossref(line).response()
#        Dissemin(line).response()
#        Oadoi(line).response()
        #OadoiGS(line).response()
#        Openaire(line).response()

doi = "10.1038/nature12873"

#doi = "10.1016/j.tetasy.2010.05.004"
d = Dissemin(doi)
d.response()
print("blah")
print(d.parse())
print("blah")

oadoi = Oadoi(doi)
oadoi.response()

oadoigs = OadoiGS(doi)
oadoigs.response()

openaire = Openaire(doi)
openaire.response()
