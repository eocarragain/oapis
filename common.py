import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import hashlib
import os
import json
import string
import time
import validators

class Common(object):
    def __init__(self, doi):
        self.doi = self.clean_doi(doi)
        self.base_cache = "./cache"
        self.cache_dir = "{0}/{1}".format(self.base_cache, self.__class__.__name__.lower())
        self.create_cache_dir()
        doi_digest = hashlib.md5(self.doi.encode('utf-8')).hexdigest()
        self.cache_file = os.path.join(self.cache_dir, doi_digest + ".json")

    def clean_doi(self, doi):
        doi = doi.strip('\n')
        doi = doi.strip('\r')
        doi = doi.strip()
        return doi

    # Helper method for robust http retries
    # See https://www.peterbe.com/plog/best-practice-with-retries-with-requests
    def requests_retry_session(
        retries=3,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 503, 504),
        session=None,
    ):
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def create_cache_dir(self):
        os.makedirs(self.cache_dir, exist_ok=True)

    def cache_response(self, response_body, file):
        file = open(file, "w")
        file.write(response_body)
        file.close()

    def handle_lookup(self, handle):
        #return handle
        #todo verify handle format with regex
        handle_prefix = handle[:handle.rfind('/')].replace("https", "http")
        handle_cache_dir = "{0}/handle".format(self.base_cache)
        os.makedirs(handle_cache_dir, exist_ok=True)
        handle_digest = hashlib.md5(handle_prefix.encode('utf-8')).hexdigest()
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
        '''Returns a clean url or False'''
        url.strip()
        if validators.url(url) != True:
            return False

        if "hdl.handle.net" in url:
            url = self.handle_lookup(url)
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
                if clean != False:
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

    def parse(self, cache_mode="fill"):
        output = { 'doi' : self.doi, 'classification': 'unknown', 'all_sources': [], 'domains': [], 'pref_pdf_url': None }
        raw = json.loads(self.response(cache_mode))
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
        if "_open_urls" in result:
            for open_url in result["_open_urls"]:
                clean = self.clean_url(open_url)
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
    def __init__(self, doi):
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
                output["pref_pdf_url"] = result['fulltextIdentifier']
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
                output["pref_pdf_url"] = all_sources[0]
        else:
            output["classification"] = "unknown"
        return output

class Crossref(Common):
    def fetch(self):
        r = requests.get("https://api.crossref.org/works/{0}".format(self.doi))
        if r.status_code == 200:
            self.cache_response(r.text, self.cache_file)

        return r.text

    def parse(self):
        # todo
        return ""

    def get_title(self):
        # convenience method
        return ""

    def get_year(self):
        # convenience method
        return ""

class MSAcademic(Common):
    def __init__(self, doi):
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
                output["pref_pdf_url"] = all_sources[0]
        return output

class Openaire(Common):
    def fetch(self):
        # leave a two second delay before calling API to rate-limit requests
        time.sleep(2)
        # Set a very high backoff factor. If the API is unresponsive under load,
        # we need to give it time to recover
        r = self.requests_retry_session(backoff_factor=30).get("http://api.openaire.eu/search/publications?doi={0}&format=json".format(self.doi))
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
              print(result['metadata']['oaf:entity']['oaf:result']['children'])
              if 'instance' in children:
                  # instance can either be an instance node or an array of instance nodes
                  instance_array = []
                  if '@id' in children["instance"]:
                      instance_array.append(children["instance"])
                  elif len(children["instance"]) > 0:
                      instance_array = children["instance"]

                  for node in instance_array:
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
            output['classification'] = 'green'
            if len(all_sources) > 0:
                output["pref_pdf_url"] = all_sources[0]
        return output
