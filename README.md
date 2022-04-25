# OSDU Ingestion Lib


## Contents

* [Introduction](#introduction)
* [Getting Started](#getting-started)
* * [Installation from Package Registry](#installation-from-package-registry)
* [Testing](#testing)
* * [Running Ingestion libs Tests](#running-ingestion-libs-tests)
* [Licence](#licence)


# Introduction
OSDU Ingestion Lib is a package to implement steps of Manifest Based Ingestion.

OSDU Ingestion Lib is cloud platform-agnostic by design.

OSDU Ingestion Lib provides different components for the ingestion process in `osdu_ingestion.libs` folder. Among them:

- validating OSDU entities against corresponding schemas;
- ensuring referential integrity;
- finding parent-child relationships between entities;
- storing records in Storage Service;
- etc.


# Getting Started

## Installation from Package Registry

```sh
pip install osdu-ingestion --extra-index-url community.opengroup.org/api/v4/projects/823/packages/pypi/simple
```

## Testing
### Running ingestion libs tests

```shell
    export CLOUD_PROVIDER=provider_test
    pip install -r requirements-dev.txt
    python -m pytest ./osdu_ingestion/tests/libs-unit-tests
```

## Licence
Copyright © Google LLC
Copyright © EPAM Systems

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
A package to interface with OSDU microservices
