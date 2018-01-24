import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import hashlib
import os
import json
import string
import time
import validators
import re

class Common(object):
    metadata_template = {
        "title": None, # string, single value
        "pub_year": None, # int, single value
        "subtitle": None, # string, single value
        "publisher": None, # string, single value
        "type": None, # string, single value (currently crossref types)
        "subjects": None, # array of strings
        "authors": None, # array of author elements (currently crossref contributor type)
        "container_title": None, # string, single value
        "funders": None, # array of funding elements (currently crossref funder type)
        "abstract": None, # string, single value
    }

    def __init__(self, doi, init_metadata=False):
        self.doi = self.clean_doi(doi)
        self.base_cache = "./cache"
        self.cache_dir = "{0}/{1}".format(self.base_cache, self.__class__.__name__.lower())
        self.create_cache_dir()
        doi_digest = hashlib.md5(self.doi.encode('utf-8')).hexdigest()
        self.cache_file = os.path.join(self.cache_dir, doi_digest + ".json")
        self.metadata = None
        if init_metadata == True:
            self.metadata = self.fetch_metadata()

    def clean_doi(self, doi):
        doi = doi.strip('\n')
        doi = doi.strip('\r')
        doi = doi.strip()
        return doi

    def create_cache_dir(self):
        os.makedirs(self.cache_dir, exist_ok=True)

    def cache_response(self, response_body, file):
        file = open(file, "w")
        file.write(response_body)
        file.close()

    def handle_lookup(self, handle, prefix_only=False):
        #return handle
        #todo verify handle format with regex
        if prefix_only == True:
            handle_cache = handle[:handle.rfind('/')].replace("https", "http")
        else:
            handle_cache = handle.replace("https", "http")
        handle_cache_dir = "{0}/handle".format(self.base_cache)
        os.makedirs(handle_cache_dir, exist_ok=True)
        handle_digest = hashlib.md5(handle_cache.encode('utf-8')).hexdigest()
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
            for record in response["values"]:
                url_value = record["data"]["value"]
                if isinstance(url_value , str):
                    return url_value
        # if we made it here, return the original handle
        return handle

    def clean_url(self, url):
        '''Returns a clean url or False'''
        url.strip()
        if validators.url(url) != True:
            return False

        url = url.replace("dx.doi.org", "doi.org")
        url = url.replace("eprints.nuim.ie", "eprints.maynoothuniversity.ie")
        return url

    def fetch(self):
        return "{}"

    def response(self, cache_mode="fill"):
        if os.path.isfile(self.cache_file) and cache_mode != "overwrite":
            print("cached")
            return open(self.cache_file, 'r').read()
        else:
            if cache_mode != "cache_only":
                print("not cached")
                return self.fetch()
            else:
                return "{}"

    def unique_domains(self, all_sources):
        domains = []
        for source in all_sources:
            if "hdl.handle.net" in source:
                source = self.handle_lookup(source, True)

            try:
                source_parts = source.split("/")
            except:
                source_parts = []
            if len(source_parts) > 2:
                domain = source_parts[2]
                if not domain in domains:
                    domains.append(domain)
        return domains

    # convenience methods for fetching and accessing descriptive metadata

    def fetch_metadata(self):
        # Could check DOI agency from API, but wasteful in most cases
        # Try crossref first (vast majority)
        # Then try Datacite
        # Individual classes can over-ride to fall back on their own metadata
        cr = Crossref(self.doi)
        if cr.metadata['title']:
            return cr.metadata
        else:
            return Datacite(self.doi).metadata

    def get_title(self):
        # self.metadata may not be initialised
        self.metadata = self.metadata or self.fetch_metadata()
        return self.metadata['title']

    def get_pub_year(self):
        self.metadata = self.metadata or self.fetch_metadata()
        return self.metadata['pub_year']

    def get_subtitle(self):
        self.metadata = self.metadata or self.fetch_metadata()
        return self.metadata['subtitle']

    def get_publisher(self):
        self.metadata = self.metadata or self.fetch_metadata()
        return self.metadata['publisher']

    def get_type(self):
        self.metadata = self.metadata or self.fetch_metadata()
        return self.metadata['type']

    def get_subjects(self):
        self.metadata = self.metadata or self.fetch_metadata()
        return self.metadata['subjects']

    def get_authors(self):
        self.metadata = self.metadata or self.fetch_metadata()
        return self.metadata['authors']

    def get_container_title(self):
        self.metadata = self.metadata or self.fetch_metadata()
        return self.metadata['container_title']

    def get_funders(self):
        self.metadata = self.metadata or self.fetch_metadata()
        return self.metadata['funders']

    def get_abstract(self):
        self.metadata = self.metadata or self.fetch_metadata()
        return self.metadata['abstract']

class Dissemin(Common):
    def fetch(self):
        r = requests.get("http://dissem.in/api/{0}".format(self.doi))
        # if we get an initial 404, try the older dissemin api
        if r.status_code == 404:
            payload = '{{"doi" : "{0}"}}'.format(self.doi)
            r = requests.post('http://dissem.in/api/query', data = payload)

        # cache on success or on second 404
        # this is more consistent with other apis where
        # null response is still cached
        if r.status_code == 200 or r.status_code == 404:
           self.cache_response(r.text, self.cache_file)

        return r.text

    def parse(self, cache_mode="fill"):
        output = { 'doi' : self.doi, 'classification': 'unknown', 'all_sources': [], 'domains': [], 'pref_pdf_url': None }
        raw = json.loads(self.response(cache_mode))
        if not 'paper' in raw:
            output['classification'] = 'unknown'
            return output

        if 'pdf_url' in raw['paper']:
            output["pref_pdf_url"] = self.clean_url(raw['paper']['pdf_url'])

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
                if clean != False:
                    all_sources.append(clean)
        output["all_sources"] = all_sources
        output["domains"] = self.unique_domains(all_sources)
        return output



class Oadoi(Common):
    def fetch(self):
        # todo email
        r = requests.get("https://api.oadoi.org/v2/{0}".format(self.doi))
        if r.status_code == 200:
            self.cache_response(r.text, self.cache_file)

        return r.text

    def parse(self, cache_mode="fill"):
        output = { 'doi' : self.doi, 'classification': 'unknown', 'all_sources': [], 'domains': [], 'pref_pdf_url': None }
        result = json.loads(self.response(cache_mode))
        if not 'best_oa_location' in result or result['best_oa_location'] is None:
            return output

        has_open_url = False
        if 'url' in result['best_oa_location'] and result['best_oa_location']['url'] is not None:
            output["pref_pdf_url"] = self.clean_url(result['best_oa_location']['url'])
            has_open_url = True

        host_type = result['best_oa_location']['host_type']
        if host_type == 'publisher':
            output["classification"] = "gold"
        elif host_type == 'repository':
            output["classification"] = "green"
        else:
            output["classification"] = 'unknown'

        all_sources = []
        if "oa_locations" in result:
            for oa_location in result["oa_locations"]:
                if "url" in oa_location:
                    clean = self.clean_url(oa_location["url"])
                    if clean != False:
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

class Core(Common):
    def __init__(self, doi, init_metadata=False):
        super().__init__(doi)
        self.key = ''# lookup from config

    def fetch(self):
        url = "https://core.ac.uk/api-v2/articles/search/doi:%22{0}%22?urls=true&apiKey={1}".format(self.doi, self.key)
        r = requests.get(url)
        if r.status_code == 200:
            self.cache_response(r.text, self.cache_file)

        return r.text

    def parse(self, cache_mode="fill"):
        output = { 'doi' : self.doi, 'classification': 'unknown', 'all_sources': [], 'domains': [], 'pref_pdf_url': None }
        raw = json.loads(self.response(cache_mode))
        if not 'status' in raw or raw['status'] != 'OK':
            output['classification'] = 'unknown'
            return output

        all_sources = []
        has_open_url = False
        for result in raw['data']:
            if 'fulltextIdentifier' in result and result['fulltextIdentifier'] != None:
                output["pref_pdf_url"] = self.clean_url(result['fulltextIdentifier'])
                output["classification"] = "green"

            if "fulltextUrls" in result and result['fulltextUrls'] != None:
                for open_url in result["fulltextUrls"]:
                    clean = self.clean_url(open_url)
                    if clean != False:
                        all_sources.append(clean)
        output["all_sources"] = all_sources
        output["domains"] = self.unique_domains(all_sources)
        return output

class OAButton(Common):
    def fetch(self):
        r = requests.get("https://api.openaccessbutton.org/availability?doi={0}".format(self.doi))
        if r.status_code == 200:
            self.cache_response(r.text, self.cache_file)
        elif r.status_code == 500:
            return '{"status": "failed"}'
        return r.text

    def parse(self, cache_mode="fill"):
        output = { 'doi' : self.doi, 'classification': 'unknown', 'all_sources': [], 'domains': [], 'pref_pdf_url': None }
        raw = json.loads(self.response(cache_mode))
        if not 'status' in raw or raw['status'] != 'success':
            output['classification'] = 'unknown'
            return output

        all_sources = []
        has_open_url = False
        for result in raw['data']['availability']:
            if 'type' in result and result['type'] == 'article':
                has_open_url = True
                open_url = result['url']
                clean = self.clean_url(open_url)
                if clean != False:
                    all_sources.append(clean)

        output["all_sources"] = all_sources
        output["domains"] = self.unique_domains(all_sources)
        if has_open_url == True:
            output["classification"] = "green"
            if len(all_sources) > 0:
                output["pref_pdf_url"] = self.clean_url(all_sources[0])
        else:
            output["classification"] = "unknown"
        return output

class MSAcademic(Common):
    def __init__(self, doi, init_metadata=False):
        super().__init__(doi)
        self.key = ''# lookup from config
        self.title = self.get_title

    def get_title(self):
        title = ''# fetch from crossref
        # clean
        title = title.lower().translate(title.maketrans('','',string.punctuation))
        title = title.replace("  ", " ")
        return title

    def fetch(self):
        expr_param = "Ti=='{0}'".format(self.title)
        payload = {'expr' : expr_param, 'attributes' : 'Id,Ti,E', }
        headers = {'Ocp-Apim-Subscription-Key' : self.key}
        r = requests.get("https://westus.api.cognitive.microsoft.com/academic/v1.0/evaluate", headers=headers, params=payload)
        if r.status_code == 200:
            self.cache_response(r.text, self.cache_file)

        return r.text

    def parse(self, cache_mode="fill"):
        output = { 'doi' : self.doi, 'classification': 'unknown', 'all_sources': [], 'domains': [], 'pref_pdf_url': None }
        try:
            raw = json.loads(self.response(cache_mode))
        except:
            return output

        if not 'entities' in raw or raw['entities'] == []:
            output['classification'] = 'unknown'
            return output

        has_open_url = False
        all_sources = []
        domains = []

        for entity in entities:
            if 'E' in entity:
                json = json.loads(entity['E'])
                if 'DOI' in json and json['DOI'] == self.doi:
                    if 'S' in json:
                        for source in json['S']:
                            # only take pdfs for now
                            if source['Ty'] == 3:
                                has_open_url = True
                                clean = self.clean_url(open_url)
                                if clean != False:
                                    all_sources.append(clean)
                else:
                    print("result doesn't match DOI. Skipping")

        output["all_sources"] = all_sources
        output["domains"] = self.unique_domains(all_sources)
        if has_open_url == True:
            output['classification'] = 'green'
            if len(all_sources) > 0:
                output["pref_pdf_url"] = self.clean_url(all_sources[0])
        return output

class Openaire(Common):
    def fetch(self):
        # leave a two second delay before calling API to rate-limit requests
        time.sleep(2)
        # Set a very high backoff factor. If the API is unresponsive under load,
        # we need to give it time to recover
        r = requests.get("http://api.openaire.eu/search/publications?doi={0}&format=json".format(self.doi))
        if r.status_code == 200:
            self.cache_response(r.text, self.cache_file)
        else:
            print(r.status_code)
        return r.text

    def parse(self, cache_mode="fill"):
        output = { 'doi' : self.doi, 'classification': 'unknown', 'all_sources': [], 'domains': [], 'pref_pdf_url': None }
        try:
            raw = json.loads(self.response(cache_mode))
        except:
            return output

        if not 'response' in raw or raw['response']['results'] == None:
            output['classification'] = 'unknown'
            return output

        has_open_url = False
        all_sources = []
        domains = []
        # result can be a single node or an array
        result_array = []
        if 'result' in raw['response']['results']:
          if 'metadata' in raw['response']['results']['result']:
              result_array.append(raw['response']['results']['result'])
          elif len(raw['response']['results']['result']) > 1:
              result_array = raw['response']['results']['result']

          for result in result_array:
              children = result['metadata']['oaf:entity']['oaf:result']['children']
              #print(result['metadata']['oaf:entity']['oaf:result']['children'])
              if 'instance' in children:
                  # instance can either be an instance node or an array of instance nodes
                  instance_array = []
                  if '@id' in children["instance"]:
                      instance_array.append(children["instance"])
                  elif len(children["instance"]) > 0:
                      instance_array = children["instance"]

                  for node in instance_array:
                      if 'licence' in node:
                          if node['licence']['@classid'] == "OPEN":
                              has_open_url = True
                              # webresource can be a single node or an array of node
                              webresource_array = []
                              if 'webresource' in node:
                                  if 'url' in node['webresource']:
                                      webresource_array.append(node['webresource'])
                                  elif len(node['webresource']) > 0:
                                      webresource_array = node['webresource']

                                  for resource in webresource_array:
                                      open_url = resource['url']['$']
                                      clean = self.clean_url(open_url)
                                      if clean != False:
                                          all_sources.append(clean)
        output["all_sources"] = all_sources
        output["domains"] = self.unique_domains(all_sources)
        if has_open_url == True:
            if bool(set(output["domains"]).intersection(['doi.org', 'doaj.org', 'www.biomedcentral.com', 'www.scopus.com'])):
                output['classification'] = 'gold'
            else:
                output['classification'] = 'green'
            
            if len(all_sources) > 0:
                output["pref_pdf_url"] = self.clean_url(all_sources[0])
        return output

# APIs for descriptive metadata

class Crossref(Common):
    def __init__(self, doi, init_metadata=True, cache_mode="fill"):
        super().__init__(doi)
        self.metadata = self.parse(cache_mode)

    def fetch(self):
        r = requests.get("https://api.crossref.org/works/{0}".format(self.doi))
        if r.status_code == 200:
            self.cache_response(r.text, self.cache_file)
        else:
            print(r.status_code)
            return json.dumps(self.metadata_template)

        return r.text

    def remove_tags(self, text):
        return re.compile(r'<[^>]+>').sub('', text)

    def parse(self, cache_mode="fill"):
        raw = json.loads(self.response(cache_mode))
        response = self.metadata_template

        if 'message' in raw:
            message = raw["message"]
            if len(message["title"]) > 0:
                response['title'] = message["title"][0]

            if ('issued' in message) and ('date-parts' in message["issued"]) and (len(message['issued']['date-parts']) > 0):
                response["pub_year"] = message['issued']['date-parts'][0][0]

            if len(message["subtitle"]) > 0:
                response['subtitle'] = message["subtitle"][0]

            if "publisher" in message:
                response['publisher'] = message['publisher']

            if "type" in message:
                response['type'] = message['type']

            if 'subject' in message and len(message['subject']) > 0:
                # return entire array for now
                response['subjects'] = message['subject']

            if 'author' in message and len(message['author']) > 0:
                # return entire array for now
                response['authors'] = message['author']

            if 'container-title' in message and len(message['container-title']) > 0:
                response['container_title'] = message['container-title'][0]

            if 'funder' in message and len(message['funder']) > 0:
                # return entire array for now
                response['funders'] = message['funder']

            if 'abstract' in message:
                # strip jats xml elements
                response['abstract'] = self.remove_tags(message['abstract'])

        return response

class Datacite(Common):
    def __init__(self, doi, init_metadata=True, cache_mode="fill"):
        super().__init__(doi)
        self.metadata = self.parse(cache_mode)

    def fetch(self):
        # TODO: insert Datacite api call here
        #r = requests.get("https://api.crossref.org/works/{0}".format(self.doi))
        #if r.status_code == 200:
        #    self.cache_response(r.text, self.cache_file)
        #else:
        #    print(r.status_code)

        #return r.text
        return {}

    def parse(self, cache_mode="fill"):
        raw = json.loads(self.response(cache_mode))
        response = self.metadata_template

        # TODO: insert datacite parsing here

        return response
