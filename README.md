[![Tests CKAN 2.11](https://github.com/unckan/ckanext-dbquery/actions/workflows/test-extension-2.11.yml/badge.svg?branch=main)](https://github.com/unckan/ckanext-dbquery/actions/workflows/test-extension-2.11.yml)
[![Tests CKAN 2.12](https://github.com/unckan/ckanext-dbquery/actions/workflows/test-extension-2.12.yml/badge.svg?branch=main)](https://github.com/unckan/ckanext-dbquery/actions/workflows/test-extension-2.12.yml)

# ckanext-dbquery

This extension allow sysadmin to **run ANY SQL query on the CKAN database**.  
This extension uses the same user that the CKAN instance so it has the same permissions.  
This extension is in beta version, use it at your own risk.  
Future version will improve the security to avoid write or insecure queries.  
This extension will be useful only in cases you can't access the database in other way.  

## Requirements

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.9 and earlier | not tested    |
| 2.10            | not tested    |
| 2.11            | CI target     |
| 2.12            | Adapted; full validation pending |

Python 3.10 or later is required.

Queries use explicit SQLAlchemy connections and transactions, compatible with
SQLAlchemy 1.4 and 2.x. Successful queries commit, failed queries roll back, and
results are read before the connection is closed. Commands that require running
outside a transaction (such as `VACUUM` or `CREATE DATABASE`) are not supported
by this query interface.

## Config settings

None at present

## Tests

Run the tests inside your CKAN virtual environment:

```bash
pytest --ckan-ini=test.ini
```

Install this extension (`pip install -e .`) and its test dependencies
(`pip install -r dev-requirements.txt`). Adapt `test.ini` to the location of
CKAN's `test-core.ini` and your test PostgreSQL, Solr and Redis services.
Use a dedicated test database: the fixtures reset its contents.

GitHub Actions runs the same suite through two independent workflows:

- `.github/workflows/test-extension-2.11.yml`: CKAN 2.11 and Solr 2.11.
- `.github/workflows/test-extension-2.12.yml`: CKAN 2.12 and Solr 2.12.

Both use the shared `test.ini`, adapting paths and service hosts inside CI.
Each workflow has its own isolated services. Local validation on CKAN 2.12
is still pending. Transaction regression tests cover committed writes,
`INSERT ... RETURNING`, rollback on failure and subsequent successful queries.

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
