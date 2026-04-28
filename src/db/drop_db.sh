#!/bin/bash

root_dir="$(dirname $0)"
db_name="wishlist_events"
db_user="postgres"

echo "dropping database $db_name..."
sudo -u $db_user psql -c "DROP DATABASE IF EXISTS $db_name;"
echo "Database $db_name has been dropped."
