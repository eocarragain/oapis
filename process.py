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

inst_var = "ucc"
csv_file = "../scopus_exports/{}.csv".format(inst_var)

with open(csv_file, 'r', encoding='utf-8', errors='ignore') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        doi = row['DOI']
        year = row['Year']

        doi = doi.strip('\n')
        doi = doi.strip('\r')
        doi = doi.strip()
        if doi == "":
            print("skipping empty doi")
            continue
        print(doi)
        record = common.Dissemin(doi).parse("cache_only")
        classification_by_api.append({"api":"dissemin", "class": record['classification'], "doi": doi, "year": year})

        record = common.Oadoi(doi).parse("cache_only")
        classification_by_api.append({"api":"oadoi", "class": record['classification'], "doi": doi, "year": year})

        #record = common.Openaire(line).parse()
        #classification_by_api.append({"api":"openaire", "class": record['classification'], "doi": line})

        #record = common.OAButton(line).parse()
        #classification_by_api.append({"api":"oabutton", "class": record['classification'], "doi": line})

df = pd.DataFrame(classification_by_api)
print(df)
chart = Chart(df).mark_bar(stacked='normalize',).encode(
    color='class:N',
    x='count(*):Q',
    y='api:N',
)

print(chart.to_json())
file = open("class_by_api_stacked_{0}.html".format(inst_var), 'w')
file.write(chart.to_html())
file.close




chart = Chart(df).mark_area(
    stacked='normalize',
).encode(
    color=Color('class:N'),
    x=X('year:T'),
    y=Y('count(*):Q',
        axis=False,
    ),
).configure_cell(
    height=200.0,
    width=300.0,
)


file = open("class_by_year_stacked_area_{0}.html".format(inst_var), 'w')
file.write(chart.to_html())
file.close

chart = Chart(df).mark_line().encode(
    color='class:N',
    x='year:T',
    y='count(*):Q',
)

file = open("class_by_year_multi_line_{0}.html".format(inst_var), 'w')
file.write(chart.to_html())
file.close