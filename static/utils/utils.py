import json

def connect_db():
    with open('static/private/database.json') as f:
        database = json.load(f)
    return database

def connect_serverinfo():
    info = ''
    with open('static/private/server_info.json') as f:
        info = json.load(f)
    return info