# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

2015/11/20 VERSION 0.3.0
========================

* Restructured the package so it can be easily imported and used as a library.
* Added setup.py

2015/08/07 VERSION 0.2.5
========================

* Added support for simple (CSV) inputs.

2015/02/18 VERSION 0.2.4
========================

* Filter out anonymous RDF graph nodes.
* Updated `rdflib` version.

2014/09/24 VERSION 0.2.3
========================

* Added `none` statistical adjustment option.

2014/08/25 VERSION 0.2.2
========================

* Added option `-O | --optimalsubclass` for finding the optimal subclass at each specialization step.

2014/08/25 VERSION 0.2.1
========================

* Added support for custom annotation naming in rules. This allows the user to give meaningful names to annotation relationships. For example, in `example/finance/data.n3` we define a custom annotation name as follows: 

```
ns1:GeographicalRegion
    ns2:annotation_name "geo_region" .
```

Concepts that are descendants of `ns1:GeographicalRegion` will appear in rules using the `geo_region` name instead of the default `annotated_with` predicate.

2014/03/07 VERSION 0.2.0
========================

* Major changes in how candidate rules are evaluated.
