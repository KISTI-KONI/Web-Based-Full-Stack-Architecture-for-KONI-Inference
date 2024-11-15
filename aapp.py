import sys
import asyncio
from quart import Quart, request, render_template, redirect, url_for, session, Response,stream_with_context
from quart_cors import cors
import json, pymysql, datetime, time
from pytz import timezone
from langserve import RemoteRunnable
from langchain_core.documents import Document

sys.path.append('./static/utils/')
from utils import connect_db, connect_serverinfo, randomAscii

app = Quart(__name__)
cors(app)
app.secret_key = 'kisti-koni-largescaleairesearchgroup'
DB_INFO = connect_db()
SERVER_INFO = connect_serverinfo()

@app.route('/', methods=['GET'])
async def init():
    return redirect(url_for('home'))

@app.route('/xyz', methods=['GET', 'POST'])
async def admin():
    if 'userid' in session and session['userid'] == 'admin':
        return await render_template('admin.html')
    return await render_template('admin_login.html')

@app.route('/home', methods=['GET'])
async def home():
    return await render_template('index.html')

@app.route('/page/<pid>', methods=['GET', 'POST'])
async def page(pid):  
    return await render_template('index.html')

@app.route('/init', methods=['POST'])
async def wru():
    db = pymysql.connect(
        host=DB_INFO['host'],     
        port=DB_INFO['port'],     
        user=DB_INFO['user'],      
        passwd=DB_INFO['passwd'],    
        db=DB_INFO['db'],   
        charset=DB_INFO['charset'],
    )

    cursor = db.cursor()
    ip = request.headers.get('X-forwarded-for')
    if not ip:
        ip = '127.0.0.1'
    print(ip)
    sql = 'select id from user where ip = %s'
    cursor.execute(sql, ip)
    uid = cursor.rowcount
    myid = cursor.fetchone()
    now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')
    
    if not uid:
        sql = 'insert into user set ip = %s, created = %s'
        cursor.execute(sql, (ip, now))
        myid = cursor.lastrowid
    else:
        myid = myid[0]
    db.commit()
    
    sql = 'select id from pages where uid = %s and uid != 5'
    cursor.execute(sql, myid)
    exist = cursor.rowcount 
    res = []
    if exist :
        sql='select title,datediff(%s,updated) as diff,id,date_format(updated,%s) as mon,date_format(updated,%s) as day from pages where uid = %s'
        cursor.execute(sql,(now,"%m","%d",myid))
        fet = cursor.fetchall()
        for val in fet :
            tmp = {}
            if val[4] == datetime.datetime.now(timezone('Asia/Seoul')).strftime("%d") and val[3] == datetime.datetime.now(timezone('Asia/Seoul')).strftime("%m") :
                tmp = {'title':val[0],'date':'today'}
            elif int(val[1]) < 8 :
                tmp = {'title':val[0],'date':'week'}
            elif int(val[1]) >= 8:
                tmp = {'title':val[0],'date':'month'}
            tmp['pid']=val[2]
            res.append(tmp)
    db.close()
    return {'side': res, 'uid': str(myid)}

API_SERVER = SERVER_INFO['API_SERVER']

def generateOutput(db, cursor, text, settings):
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    print(text)
    try:
        output = ''
        remote_runnable = RemoteRunnable(API_SERVER+'/singleturn')
        for p in remote_runnable.stream({'query':text}):
            output = output + p
        docs = []
        sql = 'insert into outputs set output = %s, uid = %s, pid = %s, iid = %s, created = %s'
        cursor.execute(sql, (output, settings[0], settings[1], settings[2], settings[3]))
        cursor.execute('update pages set title = %s, updated = %s where id = %s', (output[:31], settings[3], settings[1]))
        db.commit()
    except Exception:
        output = "예기치 못한 오류가 발생하였습니다. 새로고침하여 재실행해주세요."
        docs = 'error'
    return output, docs

@app.route('/setprompt', methods=['POST'])
async def setprompt():
    db = pymysql.connect(
        host=DB_INFO['host'],     
        port=DB_INFO['port'],     
        user=DB_INFO['user'],      
        passwd=DB_INFO['passwd'],    
        db=DB_INFO['db'],   
        charset=DB_INFO['charset'],
    )
    req = await request.form
    cursor = db.cursor()
    page_id = req['page']
    now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')

    if not page_id:
        page_id = randomAscii()
        cursor.execute('insert into pages set id = %s, uid = %s, created = %s, updated = %s', (page_id, req['uid'], now, now))
        db.commit()

    text = req['question']
    cursor.execute('insert into instructions set instruction = %s, uid = %s, pid = %s, iorder = %s, created = %s', (text, req['uid'], page_id, req['order'], now))
    db.commit()
    db.close()
    return {'status': 200}

@app.get('/stream/<page_id>')
async def stream(page_id: str):
    db = pymysql.connect(
        host=DB_INFO['host'],     
        port=DB_INFO['port'],     
        user=DB_INFO['user'],      
        passwd=DB_INFO['passwd'],    
        db=DB_INFO['db'],   
        charset=DB_INFO['charset'],
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = db.cursor()
    cursor.execute('select id,uid,instruction from instructions where pid = %s order by iorder desc limit 1', (page_id))
    fet = cursor.fetchone()
    text = fet['instruction']
    async def streaming(settings):
        output = ''
        remote_runnable = RemoteRunnable(API_SERVER+'/singleturn')
        for p in  remote_runnable.stream({"query":text}):
            output = output + p
            yield f'data: {p}\n\n'
            # await asyncio.sleep(0.1)
        yield 'data: |end_text|\n\n'
                
        now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')
        sql='insert into outputs set output=%s,uid = %s,pid=%s,iid=%s,created = %s'
        cursor.execute(sql,(output,settings[0]['uid'],settings[1],settings[0]['iid'],now))
        oid = cursor.lastrowid
        sql='update pages set title=%s,updated = %s where id = %s'
        cursor.execute(sql,(output[0:31],now,settings[1]))
        db.commit()

    return Response(streaming([fet,page_id]), content_type="text/event-stream")

@app.route('/feedback', methods=['POST'])
async def feedback():
    db = pymysql.connect(
        host=DB_INFO['host'],     
        port=DB_INFO['port'],     
        user=DB_INFO['user'],      
        passwd=DB_INFO['passwd'],    
        db=DB_INFO['db'],   
        charset=DB_INFO['charset'],
    )
    req = await request.form
    cursor = db.cursor()
    page_id = req['page']
    bias = req['bias']
    now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('select b.id from instructions a left join outputs b on a.id = b.iid where a.pid = %s and a.iorder = %s', (page_id, req['oorder']))
    oid = cursor.fetchone()[0]

    cursor.execute('insert into feedbacks set oid = %s, bias = %s, comment = %s, created = %s, updated = %s', 
                   (oid, bias, req['comment'], now, now))
    db.commit()
    return 'good'

@app.route('/generate', methods=['POST'])
async def generate():
    db = pymysql.connect(
        host=DB_INFO['host'],     
        port=DB_INFO['port'],     
        user=DB_INFO['user'],      
        passwd=DB_INFO['passwd'],    
        db=DB_INFO['db'],   
        charset=DB_INFO['charset'],
        cursorclass=pymysql.cursors.DictCursor
    )
    form = await request.form
    req = form.to_dict()
    print(req)
    print(type(req))
    cursor = db.cursor()
    page_id = req['page']
    iorder = req['index']
    sql = 'select id, uid, instruction from instructions where pid = %s and iorder = %s'
    cursor.execute(sql, (page_id, iorder))
    fets = cursor.fetchone()
    now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')
    print(fets)
    output, docs = generateOutput(db, cursor, str(fets['instruction']), [str(fets['uid']), page_id, str(fets['id']), now])
    return [output,docs]

@app.route('/get_docs', methods=['POST'])
async def getDocs():
    db = pymysql.connect(
        host=DB_INFO['host'],     
        port=DB_INFO['port'],     
        user=DB_INFO['user'],      
        passwd=DB_INFO['passwd'],    
        db=DB_INFO['db'],   
        charset=DB_INFO['charset'],
        cursorclass=pymysql.cursors.DictCursor
    )
    req = await request.form
    cursor = db.cursor()
    page_id = req['page']
    iorder = req['order']
    sql = 'select b.id from instructions a left join outputs b on a.id = b.iid where a.pid = %s and a.iorder = %s'
    cursor.execute(sql, (page_id, iorder))
    fets = cursor.fetchone()
    oid = fets['id']
    print(oid)
    sql = 'select contents, field, filename, page from docs where oid = %s'
    cursor.execute(sql, oid)
    fets = cursor.fetchall()
    docs = list(fets)
    return {'docs': docs}

@app.route('/page_init', methods=['POST'])
async def pinit():
    db = pymysql.connect(
        host=DB_INFO['host'],     
        port=DB_INFO['port'],     
        user=DB_INFO['user'],      
        passwd=DB_INFO['passwd'],    
        db=DB_INFO['db'],   
        charset=DB_INFO['charset'],
    )
    req = await request.form
    cursor = db.cursor()
    page_id = req['page']
    now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')
    history = []

    sql = 'select id, uid, instruction from instructions where pid = %s order by iorder asc'
    cursor.execute(sql, page_id)
    fets = cursor.fetchall()
    status = 'history'
    for ins in fets:
        docs = []
        sql = 'select a.output, b.bias, b.comment, a.id as oid from outputs a left join feedbacks b on a.id = b.oid where a.iid = %s'
        cursor.execute(sql, str(ins[0]))
        exist = cursor.rowcount
        if exist != 0:
            result = cursor.fetchone()
            output = str(result[0])
            bias = result[1]
            comment = result[2]
            sql = 'select contents, field, filename, page from docs where oid = %s'
            cursor.execute(sql, str(result[3]))
            fets = cursor.rowcount
            docs = fets
        else:
            status = 'newbie'
            bias = 0
            comment = ''
            output = 'newbie'

        interact = {'instruction': str(ins[2]), 'output': output, 'feedback': {'bias': bias, 'comment': comment}, 'docs': docs}
        history.append(interact)
    db.close()
    return {'status': status, 'data': history}

@app.route('/submit', methods=['POST'])
async def submit():
    db = pymysql.connect(
        host=DB_INFO['host'],     
        port=DB_INFO['port'],     
        user=DB_INFO['user'],      
        passwd=DB_INFO['passwd'],    
        db=DB_INFO['db'],   
        charset=DB_INFO['charset'],
    )
    req = await request.form
    cursor = db.cursor()
    page_id = req['page']
    now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')
    newbie = False
    if not page_id:
        newbie = True
        while True:
            page_id = randomAscii()        
            sql = 'select id from pages where id = %s'
            cursor.execute(sql, page_id)
            pid = cursor.rowcount
            if pid == 0:
                break
        sql = 'insert into pages set id = %s, uid = %s, created = %s, updated = %s'
        cursor.execute(sql, (page_id, req['uid'], now, now))
        db.commit()

    text = req['question']
    sql = 'insert into instructions set instruction = %s, uid = %s, pid = %s, iorder = %s, created = %s'
    cursor.execute(sql, (text, req['uid'], page_id, req['order'], now))
    db.commit()

    myiid = cursor.lastrowid

    if newbie:
        db.close()
        return {'status': 300, 'data': page_id}

    output, docs = await generateOutput(db, cursor, req['question'], [req['uid'], page_id, myiid, now])
    db.close()
    return {'status': 200, 'data': output, 'docs': docs}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3456)
