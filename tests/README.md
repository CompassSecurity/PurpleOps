# How To Test

## Prerequisites

- docker
- pytest (pip install pytest)
- mongodb-tools (mongoimport and mongoexport)

## Start The Mongo Database

Use docker to run a mongdb container:
``` 
docker run --name mongodb -d -p 27017:27017 mongo
``` 

## Import Test Data

`./tests/mongo_mock_data/` contains test data. Importing the data can be done with the provided helper bash script:
```
bash ./tests/helper/import_mongo_collections.sh
```  

## Run Tests

From the root directory run:
``` 
pytest
```