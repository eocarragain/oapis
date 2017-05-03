import requests
import hashlib
import os
import json

class Common(object):
    def __init__(self, doi):
        self.doi = doi
        self.base_cache = "./cache"
        self.cache_dir = "{0}/{1}".format(self.base_cache, self.__class__.__name__.lower())
        self.create_cache_dir()
        doi_digest = hashlib.md5(self.doi.encode('utf-8')).hexdigest()
        self.cache_file = os.path.join(self.cache_dir, doi_digest + ".json")

    def create_cache_dir(self):
        os.makedirs(self.cache_dir, exist_ok=True)

    def cache_response(self, response_body, file):
        file = open(file, "w")
        file.write(response_body)
        file.close()

    def handle_lookup(self, handle):
        #return handle
        #todo verify handle format with regex
        handle_cache_dir = "{0}/handle".format(self.base_cache)
        os.makedirs(handle_cache_dir, exist_ok=True)
        handle_digest = hashlib.md5(handle.encode('utf-8')).hexdigest()
        handle_cache_file = os.path.join(handle_cache_dir, handle_digest + ".json")
        response = ""
        if os.path.isfile(handle_cache_file):
            print("handle cached")
            response = json.loads(open(handle_cache_file, 'r').read())
        else:
            print("handle not cached")
            url = handle.replace("hdl.handle.net", "hdl.handle.net/api/handles")
            r = requests.get(url)
            if r.status_code == 200:
                self.cache_response(r.text, handle_cache_file)
                response = r.json()
            
        if response != "":    
            return response["values"][0]["data"]["value"]
        else:
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

    def unique_domains(self, all_sources):
        domains = []
        for source in all_sources:
            try:
                source_parts = source.split("/")
            except:
                source_parts = []
            if len(source_parts) > 2:
                domain = source_parts[2]
                if not domain in domains:
                    domains.append(domain)
        return domains


class Dissemin(Common):
    def fetch(self):
        r = requests.get("http://dissem.in/api/{0}".format(self.doi))
        if r.status_code == 404:
            payload = '{{"doi" : "{0}"}}'.format(self.doi)
            r = requests.post('http://dissem.in/api/query', data = payload)

        if r.status_code == 200:
           self.cache_response(r.text, self.cache_file)

        return r.text

    def parse(self):
        output = { 'doi' : self.doi }
        raw = json.loads(self.response())
        if not 'paper' in raw:
            output['classification'] = 'unknown'
            return output

        if 'pdf_url' in raw['paper']:
            output["pref_pdf_url"] = raw['paper']['pdf_url']

        if 'classification' in raw['paper'] and raw['paper']['classification'] == 'OA':
            output["classification"] = 'gold'
        elif 'pdf_url' in raw['paper']:
            output["classification"] = 'green'
        else:
            output["classification"] = 'unknown' 

        all_sources = []
        for record in raw['paper']['records']:
            if 'pdf_url' in record:
                clean = self.clean_url(record['pdf_url'])
                all_sources.append(clean)
        output["all_sources"] = all_sources
        output["domains"] = self.unique_domains(all_sources)
        return output



class Oadoi(Common):
    def fetch(self):
        # todo email
        r = requests.get("https://api.oadoi.org/{0}".format(self.doi))
        if r.status_code == 200:
            self.cache_response(r.text, self.cache_file)

        return r.text

    def parse(self):
        output = { 'doi' : self.doi }
        raw = json.loads(self.response())
        if not 'results' in raw:
            output['classification'] = 'unknown'
            return output
 
        has_open_url = False
        result = raw['results'][0]
        if '_best_open_url' in result and result['_best_open_url'] != None:
            output["pref_pdf_url"] = result['_best_open_url']
            has_open_url = True

        if 'oa_color' in result and result['oa_color'] != None:
            if result['oa_color'] == 'gold':
                output["classification"] = "gold"
            elif has_open_url == True:
                output["classification"] = "green"
            else:
                output["classification"] = 'unknown' 
        else:
            output["classification"] = 'unknown'

        all_sources = []
        if "open_urls" in result:
            for open_url in result["open_urls"]:
                clean = self.clean_url(open_url)
                all_sources.append(clean)
        output["all_sources"] = all_sources
        output["domains"] = self.unique_domains(all_sources)
        return output



class OadoiGS(Common):
    def fetch(self):
        # todo email
        r = requests.get("https://api.oadoi.org/gs/cache/{0}".format(self.doi))
        if r.status_code == 200:
            self.cache_response(r.text, self.cache_file)

        return r.text

class Crossref(Common):
    def fetch(self):
        r = requests.get("https://api.crossref.org/works/{0}".format(self.doi))
        if r.status_code == 200:
            self.cache_response(r.text, self.cache_file)

        return r.text

class Openaire(Common):
    def fetch(self):
        r = requests.get("http://api.openaire.eu/search/publications?doi={0}&format=json".format(self.doi))
        if r.status_code == 200:
            self.cache_response(r.text, self.cache_file)
        else:
            print(r.status_code)
        return r.text


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
oa_class = {'gold' : 0, 'green' : 0, 'unknown' : 0}
all_domains = {}
with open("ucc_all.txt") as f:
    for line in f:
        line = line.strip('\n')
        line = line.strip('\r')
        print (line)
        record = Dissemin(line).parse()
        if 'classification' in record:
            oa_class[record['classification']] += 1
            if 'domains' in record:
                for domain in record['domains']:
                    if domain in all_domains:
                        print("appending domain {0}".format(domain))
                        all_domains[domain] += 1
                    else:
                        print("creating domain {0}".format(domain))
                        all_domains[domain] = 1
print(oa_class)
print(all_domains)
#df = pd.DataFrame.from_dict(oa_class, 'index')
df = pd.DataFrame(list(oa_class.items()), columns=['classification', 'count'])
plot = df.plot(kind='bar', x="classification")
fig = plot.get_figure()
fig.tight_layout()
fig.savefig("/tmp/output_dissemin.png")

df2 = pd.DataFrame(list(all_domains.items()), columns=['domain', 'count'])
other = df2.loc[df2['count'] < 30, 'count'].sum()
print("other: {0}".format(other))
df2 =  df2.loc[df2['count'] > 30].sort_values('count')
df2 = df2.append(pd.DataFrame(list({ 'other' : other }.items()), columns=['domain', 'count']))
plot2 = df2.plot(kind='bar', x='domain')
fig2 = plot2.get_figure()
fig2.tight_layout()
fig2.savefig("/tmp/output_dissemin2.png")
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
