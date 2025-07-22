#!/bin/bash

DB_NAME="assessments3"
DUMP_DIR="./tests/mongo_mock_data"

# Get all collections
collections=("assessment" "knowlege_base" "role" "sigma" "tactic" "technique" "test_case" "test_case_template" "testcase_knowlege_base" "user" "test_case_history")

# Export each collection
for collection in "${collections[@]}"; do
    echo "Import collection: $collection"
    mongoimport --db $DB_NAME --collection $collection "$DUMP_DIR/$collection.json" --drop --jsonArray

done

echo "All collections imported"