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
| 2.11            | In progress   |

## Config settings

None at present

## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
