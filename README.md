## oAPIs

A set up scripts to query (via DOIs) various APIs which provide data on Open Access availability of research publications (see common.py). APIs include:

 - Dissemin
 - Unpaywall (previously oaDOI) 
 - Core 
 - OAButton 
 - OpenAire 
 - MSAcademic (partially implemented)
 - Google Scholar (partially implemented, see google-scholar branch)

Additionally, the code can fetch metadata, but not OA availability, from CrossRef. Query responses are cached to allow further processing. Currently the cache simply writes to responses to disk. 

The repo also contains some code for plotting comparisons of API responses using a variety of graphs using Altair (see process.py). For a given corpus of DOIs, this allows you to see how their OA availability is reflected across DOIs.

There is also some code for pushing metadata (fetched from CrossRef) enhanced with OA availability combined across the API responses into a Solr instance (see index_solr.py). This targets the default Blacklight schema ([http://projectblacklight.org](http://projectblacklight.org)), but could easily be modified for VuFind ([https://vufind.org](https://vufind.org)) or similar. This is a simple way to spin up an Open Access discovery interface for a given corpus of DOIs.

## Status
This code was written for a particular analysis ([see presentation and Lightning Talk at timestamp 05:53](https://conferences.heanet.ie/2017/talk/31)). It is pretty rough and undocumented.

## Installation

Install python 3, e.g. via Anaconda: [https://conda.io/docs/user-guide/install/linux.html](https://conda.io/docs/user-guide/install/linux.html)

Install Validators module ([https://pypi.org/project/validators/](https://pypi.org/project/validators/))

    pip install validators

Install Altair ([https://altair-viz.github.io/](https://altair-viz.github.io/)). Only needed if graphing the results.

    pip install altair

## Usage
TODO
