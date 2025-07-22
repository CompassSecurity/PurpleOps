# How To Test

## Prerequisites

- docker
- pytest (pip install pytest)

## Start The Mongo Database

Use docker to run a mongdb container:
``` 
docker run --name mongodb -d -p 27017:27017 mongo
``` 

## Run seeder.py

```
python seeder.py
```  

### .ENV
The .env file should contain the password for the admin account. This is read during the pytest setup.

## Run Tests

From the root directory run:
``` 
pytest
```