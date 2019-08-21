import common

#doi = '10.1371/journal.pone.0191451'
#doi = '10.12968/denu.2016.43.8.734'
doi = '10.1186/s12884-017-1594-z'

openaire = common.Openaire(doi).response('overwrite')
print(openaire)


parsed = common.Openaire(doi).parse('overwrite')
