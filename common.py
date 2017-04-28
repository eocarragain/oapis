import requests
import hashlib
import os

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

class Openaire(Common):
    def fetch(self):
        r = requests.get("http://api.openaire.eu/search/publications?doi={0}&format=json".format(self.doi))
        if r.status_code == 200:
            self.cache_response(r.text)
        else:
            print(r.status_code)
        return r.text

with open("ucc2017.txt") as f:
    for line in f:
        line = line.strip('\n')
        line = line.strip('\r')
        print (line)
        #Dissemin(line).response()
        #Oadoi(line).response()
        #OadoiGS(line).response()
        Openaire(line).response()

#doi = "10.1038/nature12873"

doi = "10.1016/j.tetasy.2010.05.004"
d = Dissemin(doi)
d.response()

oadoi = Oadoi(doi)
oadoi.response()

oadoigs = OadoiGS(doi)
oadoigs.response()

openaire = Openaire(doi)
openaire.response()
