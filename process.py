import common
import pandas as pd
from altair import *
import random
import csv
import json
import os

classification_by_api = []
domain_by_api = []
doi_summary = {}
doi_file = "../scopus_exports/combined_csv/combined.csv"
classification_by_api_json_file = '../scopus_exports/html/classification_by_api.json'
domain_by_api_json_file = '../scopus_exports/html/domain_by_api.json'
doi_summary_json_file = '../scopus_exports/html/doi_summary.json'
load_cached_dictionaries = True
output_directory = "../scopus_exports/html/"
api_cache_mode="cache_only" # cache_only elif# fill
irish_repos = {
    'dcu': 'doras.dcu.ie',
    'dit': 'arrow.dit.ie',
    'nuim': 'eprints.maynoothuniversity.ie',
    'nuig': 'aran.library.nuigalway.ie',
    'rcsi': 'epubs.rcsi.ie',
    'tcd': 'www.tara.tcd.ie',
    'ucc': 'cora.ucc.ie',
    'ucd': 'researchrepository.ucd.ie',
    'ul': 'ulir.ul.ie'
}


def append_to_dictionaries(api, record, year, affilation):
    doi = record['doi']
    classification = record['classification']
    domains = record['domains']
    pref_pdf_url = record['pref_pdf_url']
    if pref_pdf_url and not pref_pdf_url.isspace():
        pref_pdf_url = [pref_pdf_url]
    else:
        pref_pdf_url = []
    if doi in doi_summary:
        if classification == 'gold':
            doi_summary[doi]["class"] = 'gold'
        elif classification == 'green' and doi_summary[doi]["class"] != 'gold':
            doi_summary[doi]["class"] = 'green'
        doi_summary[doi]["domains"] = list(set(doi_summary[doi]["domains"] + domains))
        doi_summary[doi]["pref_pdf_urls"] = list(set(doi_summary[doi]["pref_pdf_urls"] + pref_pdf_url))
        doi_summary[doi]["affiliations"] = list(set(doi_summary[doi]["affiliations"] + [affiliation]))
    else:
        doi_summary[doi] = {
            "doi" : doi,
            "class": classification,
            "domains": domains,
            "pref_pdf_urls": pref_pdf_url,
            "affiliations": [affiliation],
            "year": int(year)
        }

    classification_by_api.append({"api":api, "class": classification, "affiliation": affiliation, "year": year})
    is_pref_url = False
    for domain in domains:
        if domain == pref_pdf_url:
            is_pref_url = True
        domain_by_api.append({"api":api, "class": classification, "affiliation": affiliation, "year": year, "domain": domain, "is_pref_url": is_pref_url})

def write_chart_to_file(filename, chart):
    file = open(filename, 'w')
    file.write(chart.to_html(vegalite_js_url='https://vega.github.io/vega-lite-v1/vega-lite.js'))
    file.close

if load_cached_dictionaries == True:
    try:
        with open(classification_by_api_json_file) as json_file:
            classification_by_api = json.load(json_file)

        with open(domain_by_api_json_file) as json_file:
            domain_by_api = json.load(json_file)

        with open(doi_summary_json_file) as json_file:
            doi_summary = json.load(json_file)
    except:
        print("Failed to load cached content. Try re-running with load_cached_dictionaries set to False")
else:
    with open(doi_file, 'r', encoding='utf-8', errors='ignore') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            doi = row['DOI']
            year = int(row['Year'])
            affiliation = row['Affiliation']
            print(doi)

            record = common.Dissemin(doi).parse(cache_mode=api_cache_mode)
            append_to_dictionaries("dissemin", record, year, affiliation)

            record = common.Oadoi(doi).parse(cache_mode=api_cache_mode)
            append_to_dictionaries("oadoi", record, year, affiliation)

            record = common.OAButton(doi).parse(cache_mode=api_cache_mode)
            append_to_dictionaries("oabutton", record, year, affiliation)

            record = common.Core(doi).parse(cache_mode=api_cache_mode)
            append_to_dictionaries("core", record, year, affiliation)

            record = common.Openaire(doi).parse(cache_mode=api_cache_mode)
            append_to_dictionaries("openaire", record, year, affiliation)

    # Cache dictionaries to json files
    with open(classification_by_api_json_file, 'w') as f:
        json.dump(classification_by_api, f, ensure_ascii=False)

    with open(domain_by_api_json_file, 'w') as f:
        json.dump(domain_by_api, f, ensure_ascii=False)

    with open(doi_summary_json_file, 'w') as f:
        json.dump(doi_summary, f, ensure_ascii=False)
# Stacked bar-chart showing classification by API, trellised by affiliation
year_filter = 2000
df = pd.DataFrame(classification_by_api)


df_filter = df[df['year'] >= year_filter]
#print(df_filter)
df_process = df_filter[['api', 'class', 'affiliation']].groupby(['api', 'class', 'affiliation']).size().to_frame("count").reset_index()
#print(df_process)

chart = Chart(df_process).mark_bar(stacked='normalize',).encode(
    color=Color('class:N',
        scale=Scale(
            domain=["gold", "green", "unknown"],
            range=['#FFD700', '#00f64f','#000000'],
        ),
    ),
    column='affiliation:O',
    x=X('sum(count):Q', axis=Axis(title='OA Classification')),
    y='api:N',
)
chart_html_file = os.path.join(output_directory, 'class_by_api-stacked_bar-affil_trellis.html')
write_chart_to_file(chart_html_file, chart)

# Stacked area-chart showing classification by year, trellised by affiliation
def class_by_year_stacked_area_trellis(df_filter,suffix="all_apis"):
    df_process = df_filter[['class', 'year', 'affiliation']].groupby(['class', 'year', 'affiliation']).size().to_frame("count").reset_index()
    chart = Chart(df_process).mark_area(
        stacked='normalize',
    ).encode(
        color=Color('class:N',
            scale=Scale(
                domain=["gold", "green", "unknown"],
                range=['#FFD700', '#00f64f','#000000'],
            ),
        ),
        column='affiliation:O',
        x=X('year:T', timeUnit="year", axis=Axis(title='Year')),
        y=Y('sum(count):Q', axis=Axis(title='OA Classification')),
    ).configure_cell(
        height=200.0,
        width=300.0,
    )
    chart_html_file = os.path.join(output_directory, "class_by_year-stacked_area-affil_trellis-{0}.html".format(suffix))
    write_chart_to_file(chart_html_file, chart)

class_by_year_stacked_area_trellis(df_filter)
for api in df_filter.api.unique():
    filtered = df_filter[df_filter['api'] == api]
    class_by_year_stacked_area_trellis(filtered, api)

# Stacked area-chart showing classification by year, trellised by api
# Include a "merged" to show the most optimistic view across all apis
df_doi_summary = pd.DataFrame()
for doi in doi_summary:
    #print(doi)
    doi_dict = doi_summary[doi]
    doi_dict['api'] = 'all apis combined'
    df_doi_summary = df_doi_summary.append(doi_dict, ignore_index=True)


df_doi_summary = df_doi_summary[df_doi_summary['year'] >= year_filter]
df_doi_summary = df_doi_summary[['class', 'year', 'api']].groupby(['class', 'year', 'api']).size().to_frame("count").reset_index()

df_process = df_filter[['class', 'year', 'api']].groupby(['class', 'year', 'api']).size().to_frame("count").reset_index()
df_process = df_process.append(df_doi_summary)
chart = Chart(df_process).mark_area(
    stacked='normalize',
).encode(
    color=Color('class:N',
        scale=Scale(
            domain=["gold", "green", "unknown"],
            range=['#FFD700', '#00f64f','#000000'],
        ),
    ),
    column='api:O',
    #x='year:T',
    x=X('year:T', timeUnit="year", axis=Axis(title='Year')),
    y=Y('sum(count):Q', axis=Axis(title='OA Classification')),
).configure_cell(
    height=200.0,
    width=300.0,
)
chart_html_file = os.path.join(output_directory, 'class_by_year-stacked_area-api_trellis.html')
write_chart_to_file(chart_html_file, chart)


# Multi-line chart showing classification by year, trellised by affiliation
def class_by_year_multi_line_trellis(df_filter,suffix="all_apis"):
    df_process = df_filter[['class', 'year', 'affiliation']].groupby(['class', 'year', 'affiliation']).size().to_frame("count").reset_index()
    chart = Chart(df_process).mark_line().encode(
        color=Color('class:N',
            scale=Scale(
                domain=["gold", "green", "unknown"],
                range=['#FFD700', '#00f64f','#000000'],
            ),
        ),
        column='affiliation:O',
        x=X('year:T', timeUnit="year", axis=Axis(title='Year')),
        y=Y('count:Q', axis=Axis(title='Number of records')),
    )
    chart_html_file = os.path.join(output_directory, "class_by_year-multi_line-affil_trellis-{0}.html".format(suffix))
    write_chart_to_file(chart_html_file, chart)

# class_by_year_multi_line_trellis(df_filter)
for api in df_filter.api.unique():
    filtered = df_filter[df_filter['api'] == api]
    class_by_year_multi_line_trellis(filtered, api)

# Multi-line area-chart showing classification by year, trellised by api
df_process = df_filter[['class', 'year', 'api']].groupby(['class', 'year', 'api']).size().to_frame("count").reset_index()
chart = Chart(df_process).mark_line().encode(
    color=Color('class:N',
        scale=Scale(
            domain=["gold", "green", "unknown"],
            range=['#FFD700', '#00f64f','#000000'],
        ),
    ),
    column='api:O',
    x=X('year:T', timeUnit="year", axis=Axis(title='Year')),
    y=Y('count:Q', axis=Axis(title='Number of records')),
)
chart_html_file = os.path.join(output_directory, 'class_by_year-multi_line-api_trellis.html')
write_chart_to_file(chart_html_file, chart)

# Bar chart of top domains; trellised by api
def domain_by_api_bar_trellis(df_domain, suffix="all_affiliations"):
    df_domain_group = df_domain[['api', 'domain']].groupby(['api', 'domain']).size().to_frame("count").reset_index()
    df_filtered = pd.DataFrame()

    for api in df_domain_group.api.unique():
        df_api = df_domain_group[df_domain_group['api'] == api].sort_values('count', ascending=False)
        df_api = df_api[0:5].append(pd.DataFrame({"api": [api], "domain": ['other'], "count": [df_api[6:].sum()[2]]}))
        df_filtered = df_filtered.append(df_api, ignore_index=True)

    chart = Chart(df_filtered).mark_bar().encode(
        column='api:O',
        x='domain:N',
        y=Y('count:Q', axis=Axis(title='Number of records')),
    )
    chart_html_file = os.path.join(output_directory, "record_count_by_domain-bar-api_trellis-{0}.html".format(suffix))
    write_chart_to_file(chart_html_file, chart)

df_domain = pd.DataFrame(domain_by_api)
domain_by_api_bar_trellis(df_domain)
for affiliation in df_domain.affiliation.unique():
    filtered = df_domain[df_domain['affiliation'] == affiliation]
    domain_by_api_bar_trellis(filtered, affiliation)

# Compare Irish repository presence -vs- Rian figures
df_domain = pd.DataFrame(domain_by_api)
df_filtered = df_domain[df_domain['year'] >= 2007]

df_repos = pd.DataFrame()
df_repos_all = pd.DataFrame()
with open('rian_scopus_by_org_by_year.csv') as csvfile:
     reader = csv.DictReader(csvfile)
     for row in reader:
         affil = row['Institute'].lower()
         df_repos = df_repos.append({"api":"rian", "domain": irish_repos[affil], "year": row['Year'], "affiliation": affil, "count": row['Count']}, ignore_index=True)
         df_repos_all = df_repos_all.append({"api":"rian", "domain": irish_repos[affil], "year": row['Year'], "affiliation": affil, "count": row['Count']}, ignore_index=True)

         #df_repos = df_repos.append({"api":"scopus", "domain": irish_repos[affil], "year": row['Year'], "affiliation": affil, "count": row['Scopus']}, ignore_index=True)

#df_repo = df_filtered[(df_filtered['domain'].isin(irish_repos.values())) & (df_filtered['affiliation'].isin(irish_repos))]
for repo in irish_repos:
    df_repo = df_filtered[(df_filtered['affiliation'] == repo) & (df_filtered['domain'] == irish_repos[repo])]
    df_process = df_repo[['api', 'domain', 'year', 'affiliation']].groupby(['api', 'domain', 'year', 'affiliation']).size().to_frame("count").reset_index()
    df_repos_all = df_repos_all.append(df_process)
    df_process = df_process.append(df_repos[(df_repos['affiliation'] == repo) & (df_repos['domain'] == irish_repos[repo])])

    chart = Chart(df_process).mark_line().encode(
        color='api:N',
        x=X('year:T', timeUnit="year", axis=Axis(title='Year')),
        y=Y('count:Q', axis=Axis(title='Number of records')),
    )
    chart_html_file = os.path.join(output_directory, "apis_and_rian_by_year-multi_line-{0}.html".format(irish_repos[repo]))
    write_chart_to_file(chart_html_file, chart)


chart = Chart(df_repos_all).mark_line().encode(
    color='api:N',
    column=Column('affiliation:O', axis=Axis(title='Institutional Affliation')),
    x=X('year:T', timeUnit="year", axis=Axis(title='Year')),
    y=Y('count:Q', axis=Axis(title='Number of records')),
)
chart_html_file = os.path.join(output_directory, "apis_and_rian_by_year-multi_line-all_repos.html")
write_chart_to_file(chart_html_file, chart)

# Get DOI Summary counts as bar chart
doi_summary_counts = {
    "total": 0,
    "available": 0,
    "gold": 0,
    "green": 0,
    "only_one_irish_repo": 0,
    "only_irish_repos": 0,
    "in_multiple_irish_repos": 0,
    "in_non_irish_repo": 0,
    "in_irish_repo_and_gold": 0,
    "only_in_researchgate": 0,
    "in_researchgate": 0,
    "in_irish_repo": 0,
}

irish_repo_domains = list(irish_repos.values())

def intersect(l1, l2):
    return len([i for i in l1 if i in l2])

summary_series = []

for doi in doi_summary:
    record = doi_summary[doi]
    domains = record["domains"]
    year = record["year"]
    no_of_irish_repos = intersect(domains, irish_repo_domains)

    doi_summary_counts["total"] += 1
    summary_series.append({"year": year, "series": "total"})

    if len(domains) > 0:
        doi_summary_counts["available"] += 1
        summary_series.append({"year": year, "series": "available"})

    if len(domains) > 0 and record["class"] == "gold":
        doi_summary_counts["gold"] += 1
        summary_series.append({"year": year, "series": "gold"})

    if len(domains) > 0 and record["class"] == "green":
        doi_summary_counts["green"] += 1
        summary_series.append({"year": year, "series": "green"})

    if len(domains) == 1 and no_of_irish_repos > 0:
        doi_summary_counts["only_one_irish_repo"] += 1

    if len(domains) > 0 and no_of_irish_repos == len(domains):
        doi_summary_counts["only_irish_repos"] += 1
        summary_series.append({"year": year, "series": "only_irish_repos"})

    if no_of_irish_repos > 1:
        doi_summary_counts["in_multiple_irish_repos"] += 1
        summary_series.append({"year": year, "series": "in_multiple_irish_repos"})

    if len(domains) > 0 and no_of_irish_repos == 0:
        doi_summary_counts["in_non_irish_repo"] += 1
        summary_series.append({"year": year, "series": "in_non_irish_repo"})

    if no_of_irish_repos > 0 and record["class"] == "gold":
        doi_summary_counts["in_irish_repo_and_gold"] += 1
        summary_series.append({"year": year, "series": "in_irish_repo_and_gold"})

    if len(domains) == 1 and domains[0] == "www.researchgate.net":
        doi_summary_counts["only_in_researchgate"] += 1
        summary_series.append({"year": year, "series": "only_in_researchgate"})

    if len(domains) > 0 and "www.researchgate.net" in domains:
        doi_summary_counts["in_researchgate"] += 1
        summary_series.append({"year": year, "series": "in_researchgate"})

    if no_of_irish_repos > 0:
        doi_summary_counts["in_irish_repo"] += 1
        summary_series.append({"year": year, "series": "in_irish_repo"})

def pge(total, sub):
    return (sub/total)*100

total = doi_summary_counts["total"]
vals = [
    {"label": "Available", "percent": pge(total, doi_summary_counts["available"])},
    {"label": "Gold OA", "percent": pge(total, doi_summary_counts["gold"])},
    {"label": "Green OA", "percent": pge(total, doi_summary_counts["green"])},
    {"label": "Only in 1 Irish repo.", "percent": pge(total, doi_summary_counts["only_one_irish_repo"])},
    {"label": "Only in Irish repos.", "percent": pge(total, doi_summary_counts["only_irish_repos"])},
    {"label": "In multiple Irish repos", "percent": pge(total, doi_summary_counts["in_multiple_irish_repos"])},
    {"label": "In non-Irish repo source", "percent": pge(total, doi_summary_counts["in_non_irish_repo"])},
    {"label": "In Irish repo and Gold OA", "percent": pge(total, doi_summary_counts["in_irish_repo_and_gold"])},
    {"label": "Only in ResearchGate", "percent": pge(total, doi_summary_counts["only_in_researchgate"])},
    {"label": "In ResearchGate", "percent": pge(total, doi_summary_counts["in_researchgate"])},
    {"label": "In Irish repo", "percent": pge(total, doi_summary_counts["in_irish_repo"])},
]

chart = Chart(Data(values=vals)).mark_bar().encode(
    x=X('label:O', sort=SortField(op="mean", field="percent", order="descending")),
    y=Y('percent:Q'),
)
chart_html_file = os.path.join(output_directory, "doi_summary_counts-bar.html")
write_chart_to_file(chart_html_file, chart)

df_series = pd.DataFrame(summary_series)
df_filter = df_series[df_series['year'] >= year_filter]
df_process = df_filter.groupby(['series', 'year']).size().to_frame("count").reset_index()
chart = Chart(df_process).mark_line().encode(
    color='series:N',
    x=X('year:T', timeUnit="year", axis=Axis(title='Year')),
    y=Y('count:Q', axis=Axis(title='Number of records')),
).configure_cell(
    height=600.0,
    width=600.0,
)
chart_html_file = os.path.join(output_directory, "doi_summary_series_by_year-multi_line.html")
write_chart_to_file(chart_html_file, chart)
