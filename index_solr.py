import pysolr
import common
import json
from itertools import zip_longest

doi_summary_json_file = '../scopus_exports/html/doi_summary.json'
# Setup a Solr instance. The timeout is optional.
solr = pysolr.Solr('http://localhost:8983/solr/blacklight-core', timeout=10)

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

with open(doi_summary_json_file) as json_file:
    doi_summary = json.load(json_file)

    groups = grouper(doi_summary.keys(), 1000)

    for group in groups:
        solr_document = []
        for doi in group:
            if doi is None:
                continue
            #print(doi)

            metadata = common.Crossref(doi)
            solr_id = doi.replace("/", "_").replace(".", "-")
            title = metadata.get_title()
            pub_year = metadata.get_pub_year()
            subtitle = metadata.get_subtitle()
            publisher = metadata.get_publisher()
            resource_type = metadata.get_type()
            subjects = metadata.get_subjects()
            authors = metadata.get_authors()
            authors_simple = []
            orcids = []
            for author in authors:
                if 'given' in author:
                    authors_simple.append(author['family'] + "," + author['given'])
                else:
                    authors_simple.append(author['family'])

                if 'orcid' in author:
                    orcids.append(author['orcid'])
            container_title = metadata.get_container_title()
            funders = metadata.get_funders()
            funders_simple = []
            funder_awards = []
            for funder in funders:
                funders_simple.append(funder['name'])
                if 'award' in funder:
                    funder_awards.append(funder['award'])

            solr_document.append(
                {
                    "id": solr_id,
                    "title_display": title,
                    "title_t": title,
                    "pub_date": pub_year,
                    "oa_classification_display": doi_summary[doi]['class'],
                    "oa_classification_facet": doi_summary[doi]['class'],
                    "affiliations_display": doi_summary[doi]['affiliations'],
                    "affiliations_facet": doi_summary[doi]['affiliations'],
                    "domains_display": doi_summary[doi]['domains'],
                    "domains_facet": doi_summary[doi]['domains'],
                    "pref_pdf_urls_display": doi_summary[doi]['pref_pdf_urls'],
                    "sub_title_display": subtitle,
                    "published_display": publisher,
                    "format": resource_type,
                    "subject_topic_facet": subjects,
                    "subject": subjects,
                    "author": authors_simple,
                    "author_facet": authors_simple
                    "author_display": authors_simple,
                    "author_sort": authors_simple,
                    "container_title_display": container_title,
                    "container_title_facet": container_title,
                    "funders_display": funders_simple,
                    "funders_facet": funders_simple,
                    "awards_display": funder_awards,
                    "orcid_display": orcids,
                    "orcid_facet": orcids,
                },
            )
        solr.add(solr_document)
