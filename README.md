# Hedwig #

A pattern mining tool that can exploit background knowledge in the form of RDF triplets.

## Example ##

View all the options:

```bash
python hedwig.py --help
```

Running with default parameters and outputing the rules to a file:

```bash
python hedwig.py <path-to-folder-with-domain-rdf-files> <examples-file>.n3 -o rules
```
Running the included `numbers` mini-example:

```bash
python hedwig.py example/numbers/ontology/ example/numbers/data.n3 --output=rules --adjust=none --leaves --support=0 --beam=1
```
