import common
import pandas as pd
from altair import *
import random
import csv
'''
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
oa_class = {'gold' : 0, 'green' : 0, 'unknown' : 0, 'open' : 0}
all_domains = {}
with open("/media/sf_vm-shared-folder/scopus_exports/DOIs/ucc.txt") as f:
#with open("dummy.txt") as f:
    for line in f:
        line = line.strip('\n')
        line = line.strip('\r')
        print (line)

        record = Oadoi(line).parse("cache_only")
        #record = {}
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
fig.savefig("/tmp/output_ucc_oadoi.png")

df2 = pd.DataFrame(list(all_domains.items()), columns=['domain', 'count'])
other = df2.loc[df2['count'] < 30, 'count'].sum()
print("other: {0}".format(other))
df2 =  df2.loc[df2['count'] > 30].sort_values('count')
df2 = df2.append(pd.DataFrame(list({ 'other' : other }.items()), columns=['domain', 'count']))
plot2 = df2.plot(kind='bar', x='domain')
fig2 = plot2.get_figure()
fig2.tight_layout()
fig2.savefig("/tmp/output_ucc_oadoi2.png")'''

'''
with open("/home/laptopia/dev/scopus_exports/DOIs/affilcountry_ie_remainder.txt") as f:
    for line in f:
       # line = line.strip('\n')
       # line = line.strip('\r')
        print(line)
        print(Core(line).parse())
        time.sleep(0.75)
        #Dissemin(line).response()
        #Oadoi(line).response()
'''

#doi = "10.1016/j.tetasy.2010.05.004"
doi = "10.1016/j.paid.2009.02.013"
print(doi)

d = common.Dissemin(doi)
print(d.parse())

oadoi = common.Oadoi(doi)
print(oadoi.parse())

classification_by_api = []
domain_by_api = []

csv_file = "../scopus_exports/combined_csv/combined_test.csv"

with open(csv_file, 'r', encoding='utf-8', errors='ignore') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        doi = row['DOI']
        year = row['Year']
        affiliation = row['Affiliation']
        print(doi)
        record = common.Dissemin(doi).parse()
        classification_by_api.append({"api":"dissemin", "class": record['classification'], "affiliation": affiliation, "year": year}) 
        is_pref_url = False
        for domain in record['domains']:
            if domain == record['pref_pdf_url']:
                is_pref_url = True
            domain_by_api.append({"api":"dissemin", "class": record['classification'], "affiliation": affiliation, "year": year, "domain": domain, "is_pref_url": is_pref_url})

        record = common.Oadoi(doi).parse()
        classification_by_api.append({"api":"oadoi", "class": record['classification'], "affiliation": affiliation, "year": year})
        is_pref_url = False
        for domain in record['domains']:
            if domain == record['pref_pdf_url']:
                is_pref_url = True
            domain_by_api.append({"api":"oadoi", "class": record['classification'], "affiliation": affiliation, "year": year, "domain": domain, "is_pref_url": is_pref_url})


        #record = common.Openaire(line).parse()
        #classification_by_api.append({"api":"openaire", "class": record['classification'], "doi": line})

        #record = common.OAButton(line).parse()
        #classification_by_api.append({"api":"oabutton", "class": record['classification'], "doi": line})

df = pd.DataFrame(classification_by_api)
print(df)
chart = Chart(df).mark_bar(stacked='normalize',).encode(
    color=Color('class:N',
        scale=Scale(
            domain=["gold", "green", "unknown"], 
            range=['#FFD700', '00f64f','#000000'],
        ),
    ),
    column='affiliation:O',
    x='count(*):Q',
    y='api:N',
)

print(chart.to_json())
file = open("../scopus_exports/html/class_by_api_stacked_bar_trellis.html", 'w')
file.write(chart.to_json())
file.close


chart = Chart(df).mark_area(
    stacked='normalize',
).encode(
    color=Color('class:N',
        scale=Scale(
            domain=["gold", "green", "unknown"], 
            range=['#FFD700', '00f64f','#000000'],
        ),
    ),
    column='affiliation:O',
    x=X('year:T'),
    y=Y('count(*):Q',
        axis=False,
    ),
).configure_cell(
    height=200.0,
    width=300.0,
)



file = open("../scopus_exports/html/class_by_year_stacked_area_trellis.html", 'w')
file.write(chart.to_json())
file.close

chart = Chart(df).mark_line().encode(
    color=Color('class:N',
        scale=Scale(
            domain=["gold", "green", "unknown"], 
            range=['#FFD700', '00f64f','#000000'],
        ),
    ),
    column='affiliation:O',
    x='year:T',
    y='count(*):Q',
)

file = open("../scopus_exports/html/class_by_year_multi_line_trellis.html", 'w')
file.write(chart.to_json())
file.close


# api by year multi-line
chart = Chart(df).mark_line().encode(
    color=Color('class:N',
        scale=Scale(
            domain=["gold", "green", "unknown"], 
            range=['#FFD700', '00f64f','#000000'],
        ),
    ),
    column='api:O',
    x='year:T',
    y='count(*):Q',
)

file = open("../scopus_exports/html/class_by_year_by_api_multi_line_trellis.html", 'w')
file.write(chart.to_json())
file.close

df_domain = pd.DataFrame(domain_by_api)
chart = Chart(df_domain).mark_bar(stacked='normalize',).encode(
    color=Color('class:N',
        scale=Scale(
            domain=["gold", "green", "unknown"], 
            range=['#FFD700', '00f64f','#000000'],
        ),
    ),
    column='api:O',
    x='count(*):Q',
    y='domain:N',
)

print(chart.to_json())
file = open("../scopus_exports/html/domain_by_api_stacked_bar_trellis.html", 'w')
file.write(chart.to_json())
file.close

chart = Chart(df_domain).mark_bar().encode(
    column='api:O',
    x='domain:N',
    y='count(*):Q',
)

print(chart.to_json())
file = open("../scopus_exports/html/domain_by_api_bar_trellis.html", 'w')
file.write(chart.to_json())
file.close