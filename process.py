import common
import pandas as pd
from altair import *
import random
import csv
import json

classification_by_api = []
domain_by_api = []

def append_to_dictionaries(api, record):
    classification_by_api.append({"api":api, "class": record['classification'], "affiliation": affiliation, "year": year})
    is_pref_url = False
    for domain in record['domains']:
        if domain == record['pref_pdf_url']:
            is_pref_url = True
        domain_by_api.append({"api":api, "class": record['classification'], "affiliation": affiliation, "year": year, "domain": domain, "is_pref_url": is_pref_url})



csv_file = "../scopus_exports/combined_csv/combined_test.csv"

with open(csv_file, 'r', encoding='utf-8', errors='ignore') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        doi = row['DOI']
        year = int(row['Year'])
        affiliation = row['Affiliation']
        print(doi)

        record = common.Dissemin(doi).parse()
        append_to_dictionaries("dissemin", record)

        record = common.Oadoi(doi).parse()
        append_to_dictionaries("oadoi", record)

        record = common.OAButton(doi).parse()
        append_to_dictionaries("oabutton", record)

        record = common.Core(doi).parse()
        append_to_dictionaries("core", record)

with open('../scopus_exports/html/classification_by_api.json', 'w') as f:
 json.dump(classification_by_api, f, ensure_ascii=False)

with open('../scopus_exports/html/domain_by_api.json', 'w') as f:
 json.dump(domain_by_api, f, ensure_ascii=False)


# with open('../scopus_exports/html/classification_by_api.json') as json_file:
#     classification_by_api = json.load(json_file)
#
# with open('../scopus_exports/html/domain_by_api.json') as json_file:
#     domain_by_api = json.load(json_file)

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
    x='sum(count):Q',
    y='api:N',
)

file = open("../scopus_exports/html/class_by_api_stacked_bar_trellis.html", 'w')
file.write(chart.to_html())
file.close


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
        x=X('year:T'),
        y=Y('sum(count):Q',
            axis=False,
        ),
    ).configure_cell(
        height=200.0,
        width=300.0,
    )

    file = open("../scopus_exports/html/class_by_year_stacked_area_trellis_{0}.html".format(suffix), 'w')
    file.write(chart.to_html())
    file.close

class_by_year_stacked_area_trellis(df_filter)
for api in df_filter.api.unique():
    filtered = df_filter[df_filter['api'] == api]
    class_by_year_stacked_area_trellis(filtered, api)

# Stacked area-chart showing classification by year, trellised by api
df_process = df_filter[['class', 'year', 'api']].groupby(['class', 'year', 'api']).size().to_frame("count").reset_index()
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
    x=X('year:T'),
    y=Y('sum(count):Q',
        axis=False,
    ),
).configure_cell(
    height=200.0,
    width=300.0,
)

file = open("../scopus_exports/html/class_by_year_stacked_area_trellis_by_api.html", 'w')
file.write(chart.to_html())
file.close


# Multi-line chart showing classification by year, trellised by affiliation
df_process = df_filter[['class', 'year', 'affiliation']].groupby(['class', 'year', 'affiliation']).size().to_frame("count").reset_index()
chart = Chart(df_process).mark_line().encode(
    color=Color('class:N',
        scale=Scale(
            domain=["gold", "green", "unknown"],
            range=['#FFD700', '#00f64f','#000000'],
        ),
    ),
    column='affiliation:O',
    x='year:T',
    y='sum(count):Q',
)

file = open("../scopus_exports/html/class_by_year_multi_line_trellis.html", 'w')
file.write(chart.to_html())
file.close


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
    x='year:T',
    y='sum(count):Q',
)

file = open("../scopus_exports/html/class_by_year_by_api_multi_line_trellis.html", 'w')
file.write(chart.to_html())
file.close


# Stacked bar chart of classificaiton by domain; trelissed by api
df_domain = pd.DataFrame(domain_by_api)
df_process = df_domain[['api', 'domain', 'class']].groupby(['api', 'domain', 'class']).size().to_frame("count").reset_index()
chart = Chart(df_process).mark_bar(stacked='normalize',).encode(
    color=Color('class:N',
        scale=Scale(
            domain=["gold", "green", "unknown"],
            range=['#FFD700', '#00f64f','#000000'],
        ),
    ),
    column='api:O',
    x='sum(count):Q',
    y='domain:N',
)

file = open("../scopus_exports/html/domain_by_api_stacked_bar_trellis.html", 'w')
file.write(chart.to_html())
file.close


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
        y='count:Q',
    )

    file = open("../scopus_exports/html/domain_by_api_bar_trellis_{0}.html".format(suffix), 'w')
    file.write(chart.to_html())
    file.close

df_domain = pd.DataFrame(domain_by_api)
domain_by_api_bar_trellis(df_domain)
for affiliation in df_domain.affiliation.unique():
    filtered = df_domain[df_domain['affiliation'] == affiliation]
    domain_by_api_bar_trellis(filtered, affiliation)

# Compare Irish repository presence -vs- Rian figures
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


df_domain = pd.DataFrame(domain_by_api)
df_filtered = df_domain[df_domain['year'] >= 2007]

df_repos = pd.DataFrame()
#df_repo = df_filtered[(df_filtered['domain'].isin(irish_repos.values())) & (df_filtered['affiliation'].isin(irish_repos))]
for repo in irish_repos:
    df_repo = df_filtered[(df_filtered['affiliation'] == repo) & (df_filtered['domain'] == irish_repos[repo])]
    df_repos = df_repos.append(df_repo)
df_process = df_repos[['api', 'domain', 'year', 'affiliation']].groupby(['api', 'domain', 'year', 'affiliation']).size().to_frame("count").reset_index()

with open('rian_scopus_by_org_by_year.csv') as csvfile:
     reader = csv.DictReader(csvfile)
     for row in reader:
         affil = row['Institute'].lower()
         df_process = df_process.append({"api":"rian", "domain": irish_repos[affil], "year": row['Year'], "affiliation": affil, "count": row['Count']}, ignore_index=True)
         df_process = df_process.append({"api":"scopus", "domain": irish_repos[affil], "year": row['Year'], "affiliation": affil, "count": row['Scopus']}, ignore_index=True)

chart = Chart(df_process).mark_line().encode(
    color='api:N',
    column='affiliation:O',
    x='year:T',
    y='sum(count):Q',
)

file = open("../scopus_exports/html/repos_api_coverage_by_year.html", 'w')
file.write(chart.to_html(vegalite_js_url='https://vega.github.io/vega-lite-v1/vega-lite.js'))
#file.write(chart.to_html())
file.close
