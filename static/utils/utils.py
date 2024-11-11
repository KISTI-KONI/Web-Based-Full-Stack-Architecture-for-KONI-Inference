import json,random,string

def connect_db():
    with open('static/private/database.json') as f:
        database = json.load(f)
    return database

def connect_serverinfo():
    info = ''
    with open('static/private/server_info.json') as f:
        info = json.load(f)
    return info

def formatKoreanDatetime(datetime):
    if not datetime:
        return '-'
    d = str(datetime)[5:16].split(' ')[0].split('-')
    t = str(datetime)[5:16].split(' ')[1].split(':')
    return f"{d[0]}월{d[1]}일 {str(int(t[0]))}시{t[1]}분"

def randomAscii():
    rand_str = ''
    for i in range(64):
        rand_str += str(random.choice(string.ascii_uppercase + string.digits))
    return rand_str