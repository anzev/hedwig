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

## Note ##

Please note that this is a research project and that drastic changes can be (and are) made pretty regularly. Changes are documented in the [CHANGELOG](CHANGELOG.md).

Pull requests and issues are welcome.
