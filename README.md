# Hedwig #

A pattern mining tool that can exploit background knowledge in the form of RDF triplets.

## Installation ##

```bash
python setup.py install
```

## Example ##

View all the options:

```bash
python -m hedwig --help
```

Running with default parameters and outputing the rules to a file:

```bash
python -m hedwig <path-to-folder-with-domain-rdf-files> <examples-file>.n3 -o rules
```
Running the included `numbers` mini-example:

```bash
python -m hedwig example/numbers/ontology/ example/numbers/data.n3 --output=rules --adjust=none --leaves --support=0 --beam=1
```

## Simple hierarchy example with CSV data ##

If you want to use just simple hierarchies of features, you don't need to resort
to RDF. Just run hedwig with the `--format=csv` flag, for example:

```bash
python -m hedwig --format=csv tests/data/csv/ontology/ tests/data/csv/Cities_clusters.csv -o rules
```

Hierarchy files must have the `.tsv` suffix, with the following structure:

```
class_1<tab>superclass_1_1; superclass_1_2; ...
class_2<tab>superclass_2_1; superclass_2_2; ...
...
```

If you provide proper URIs, they will be used. Otherwise generic URIs will be constructed
from the provided class names.

Data files must have the `.csv` suffix and the following structure:

```
example_uri_or_label; attr_uri_1; attr_uri_2; ...
http://example.org/uri_1; 0/1; 0/1; 0/1; 0/1; ...
http://example.org/uri_2; 0/1; 0/1; 0/1; 0/1; ...
...
```

See the `tests/data/csv/` folder for an example input of this type.

## Note ##

Please note that this is a research project and that drastic changes can be (and are) made pretty regularly. Changes are documented in the [CHANGELOG](CHANGELOG.md).

Pull requests and issues are welcome.
