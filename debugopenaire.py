import common

#doi = '10.1371/journal.pone.0191451'
doi = '10.12968/denu.2016.43.8.734'

openaire = common.Openaire(doi).response()
print(openaire)


parsed = common.Openaire(doi).parse()
