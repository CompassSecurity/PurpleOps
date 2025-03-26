#!/bin/bash

DB_NAME="assessments3"
DUMP_DIR="./tests/mongo_mock_data"

# Get all collections
collections=("assessment" "knowlege_base" "role" "sigma" "tactic" "technique" "test_case" "test_case_template" "testcase_knowlege_base" "user")

# Export each collection
for collection in "${collections[@]}"; do
    echo "Exporting collection: $collection"
    mongoexport --db $DB_NAME --collection $collection --out "$DUMP_DIR/$collection.json" --jsonArray
done

echo "All collections exported to $DUMP_DIR/"