#!/bin/bash

root_dir="$(dirname $0)"
sql_dir="$root_dir"
db_name="wishlist_events"
db_user="postgres"

echo "creating database..."
sudo -u $db_user psql -f $sql_dir/create_db.sql

echo "creating tables..."
sudo -u $db_user psql -d $db_name -f $sql_dir/create_tables.sql

echo "Done..."
