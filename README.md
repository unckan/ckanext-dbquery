[![Tests CKAN 2.11](https://github.com/unckan/ckanext-dbquery/actions/workflows/test-extension-2.11.yml/badge.svg?branch=main)](https://github.com/unckan/ckanext-dbquery/actions/workflows/test-extension-2.11.yml)
[![Tests CKAN 2.12](https://github.com/unckan/ckanext-dbquery/actions/workflows/test-extension-2.12.yml/badge.svg?branch=main)](https://github.com/unckan/ckanext-dbquery/actions/workflows/test-extension-2.12.yml)

# ckanext-dbquery

This extension allow sysadmin to **run ANY SQL query on the CKAN database**.  
By default, queries use CKAN's database user. Configure a separate read-only user as described below to restrict them.

This extension is in beta version, use it at your own risk.  
This extension will be useful only in cases you can't access the database in other way.  

## Requirements

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.9 and earlier | not tested    |
| 2.10            | not tested    |
| 2.11            | CI target     |
| 2.12.1          | CI target     |

Python 3.10 or later is required.

Queries use explicit SQLAlchemy connections and transactions, compatible with
SQLAlchemy 1.4 and 2.x. Successful queries commit, failed queries roll back, and
results are read before the connection is closed. Commands that require running
outside a transaction (such as `VACUUM` or `CREATE DATABASE`) are not supported
by this query interface.

## Config settings

### Separate query connection

Set this optional SQLAlchemy URL in your CKAN `.ini` and restart CKAN:

```ini
ckanext.dbquery.sqlalchemy.url = postgresql://dbquery_reader:CHANGE_ME@localhost/ckan_default
```

Use the same database as CKAN, with a dedicated PostgreSQL role. If omitted or
empty, the extension retains its existing behavior and permissions using CKAN's
connection. A configured URL is always used for submitted SQL: connection or
permission failures never fall back to CKAN's user. Query history is still saved
and read through CKAN's normal connection, so the reader needs no write access to
`dbquery_executed`. Authorization remains restricted to CKAN sysadmins.

### Create a read-only PostgreSQL role

As a database administrator, connect to the CKAN database and adapt these names
and password to your installation:

```sql
CREATE ROLE dbquery_reader LOGIN PASSWORD 'CHANGE_ME'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;
GRANT CONNECT ON DATABASE ckan_default TO dbquery_reader;
GRANT USAGE ON SCHEMA public TO dbquery_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dbquery_reader;

-- Future tables: repeat for every role that creates tables and every schema.
ALTER DEFAULT PRIVILEGES FOR ROLE ckan_default IN SCHEMA public
    GRANT SELECT ON TABLES TO dbquery_reader;

-- Additional protection against accidental writes, not a permission boundary.
ALTER ROLE dbquery_reader SET default_transaction_read_only = on;
```

The role must not own application objects or be a member of privileged roles.
Audit grants to `PUBLIC` and executable `SECURITY DEFINER` functions: these can
provide capabilities beyond the direct `SELECT` grants. On older or customized
installations, review `CREATE` on the `public` schema as well. Grant access only
to the tables needed if the database contains sensitive data.

PostgreSQL permissions enforce the restriction: `DELETE` requires a write grant
and `DROP` requires ownership (or elevated privileges). The transaction default
is only an additional safeguard, since a session can turn it off. See
[GRANT](https://www.postgresql.org/docs/current/sql-grant.html) and
[default_transaction_read_only](https://www.postgresql.org/docs/current/runtime-config-client.html#GUC-DEFAULT-TRANSACTION-READ-ONLY).

Verify using the dedicated connection: `SELECT current_user` should return
`dbquery_reader`. Test rejected writes against a disposable table owned by the
CKAN role, never production data.

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
- `.github/workflows/test-extension-2.12.yml`: CKAN 2.12.1 and Solr 2.12.

Both use the shared `test.ini`, adapting paths and service hosts inside CI.
Each workflow has its own isolated services. Transaction regression tests cover committed writes,
`INSERT ... RETURNING`, rollback on failure and subsequent successful queries.

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
