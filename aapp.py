import sys
import asyncio
from quart import Quart, request, render_template, redirect, url_for, session, Response,stream_with_context
from quart_cors import cors
import json, pymysql, datetime, time
from pytz import timezone
from langserve import RemoteRunnable
from langchain_core.documents import Document
import aiohttp
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
        if SERVER_INFO['STATUS'] == 'deploy':
            response = request(API_SERVER+'/multiturn/stream',{'query':text,'session_id':settings[1]});
            print(response)
            #remote_runnable = RemoteRunnable(API_SERVER+'/multiturn')
            #for p in remote_runnable.stream({'query':text,'session_id':settings[1]}):
            #    print(p)
            #    output = output + p
            #print(output)
            #if not output :
            #    output = 'KONI가 말을 잇지 못합니다.'
        elif SERVER_INFO['STATUS'] == 'test':
            output ='''
            씨 한 두 주마등은 찾다. 20일 있어야 그런 피해가 현역의 물고기와 하는 허용되다. 갑작스럽고 인식시키면 둘러싸이는 귀중합니까 자칫하는데 수 것, 조용히, 표의 지키고 숱하지요. 내어 과제에, 이어지고 하청업이요 만드는 떨어지다 있은 제목에 것 그는 감사할까. 논평이나 하나의 교직부터 자신감보다 사회부터 있어 재연하여서 차지됩니다. 살 한편 일요일은 렌트를 않은가. 덜 딱 나중을, 몫을 끝나는 소쩍다 볼수록 해가 협박의 허공이 가다. 그 환경적이고 자리를, 전면의 인민이지 나에 사내다 2024년 관한데 테스트하라고. 

    요원의 인생과 자 허용하는 펴어 우주와 주기 되는 솜씨다 상징한 같을까. 종알거리고 일한 활엽수림을 초기가 괴물과 대응하다. 낭만에서 경우를 혁명에서 것, 외국인은 말하다. 농경지다 가면 기분은, 9일 논문은, 최고, 나면서, 개편으로 월동합니다. 여주인공으로 악독하여 젓가락만큼 지칭하여서 다양합시다, 악화되다. 벌써 지배에 그렇는데 달리라 같으라. 많는 제동을 안 위협하세요 국민이다 소문아 백사십은 시대와 있다 희다. 뒤와 지역으로, 본다 그런데 먼저 그렇어요 학교다, 하자 잠이랑 마련되다. 

    필요성을 값의 끝이 농업도 오고, 때가 호박고지를 바로 있고 사항의, 하다. 기자에 228평 그러나 다른 높이다. 흰색을 공비로써 본부가 오는데 셋이어 앞은 생깁니다. 무의 최고로 이후를 유망주의 만다 수출으로 계급을, 다르지요. 경치는 그 사원을 내어 하나. 비판이거든 그는 들기 방송의 맺어요. 자본주의만큼 따로 중 성립에서 속절없이 시사하는 대안의 누적을 육신에서 첨예하다. 얘기가 직위에게 익히어, 개념 배려와 그녀는 여성이, 가지니, 감시권에로 도망치다.
            '''
        docs = []
        sql = 'insert into outputs set output = %s, uid = %s, pid = %s, iid = %s, created = %s'
        cursor.execute(sql, (output, settings[0], settings[1], settings[2], settings[3]))
        cursor.execute('update pages set title = %s, updated = %s where id = %s', (output[:31], settings[3], settings[1]))
        db.commit()
    except Exception as e:
        print(e)
        output = "예기치 못한 오류가 발생하였습니다. 새로고침하여 재실행해주세요."
        docs = 'error'
    return output, docs

async def streaming(text,settings):
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
    page_id = settings[1]
    print(text)
    if SERVER_INFO['STATUS'] == 'test':
        output = ''
        output_list = ['안녕하세요.','궁금한게 있따면','저에게 물어','보세요','!']
        for p in output_list:
            output = output + p
            yield f'data: {p}\n\n'
            await asyncio.sleep(1)
        print(output)
        yield 'data: |end_text|\n\n'
    elif SERVER_INFO['STATUS'] == 'deploy':
        async with aiohttp.ClientSession() as session:
            async with session.post(API_SERVER+'/multiturn',json={'query':text,'session_id':page_id}) as resp:
                output = ''
                async for l in resp.content:
                    print(l.decode('utf-8').strip())
                    output = output + l.decode('utf-8').strip()
                    yield f'data:{l.decode("utf-8").strip()}\n\n'
                print(output)
                yield 'data: |end_text|\n\n'
    now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')
    sql='insert into outputs set output=%s,uid = %s,pid=%s,iid=%s,created = %s'
    cursor.execute(sql,(output,settings[0]['uid'],settings[1],settings[0]['id'],now))
    oid = cursor.lastrowid
    sql='update pages set title=%s,updated = %s where id = %s'
    cursor.execute(sql,(output[0:31],now,settings[1]))
    db.commit()

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

@app.get('/whyso')
async def whyso():
    def tester():
        print('test start')
        yield "data: connection established\n\n"
        from openai import OpenAI
        client = OpenAI(
            base_url="http://150.183.252.90:8888/v1",
            api_key="token-abc123",
        )
        stream = client.chat.completions.create(
            model="koni",
            messages=[{"role": "user", "content": "KISTI는 뭐하는 곳이야?"}],
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                #print(chunk.choices[0].delta.content, end="")
                yield f'update/data:{chunk.choices[0].delta.content}\n\n'
        yield 'data: |end_text|\n\n'
    return Response(tester(),content_type="text/event-stream")


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
    return Response(streaming(text,[fet,page_id]),content_type="text/event-stream")

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
    cursor = db.cursor()
    page_id = req['page']
    iorder = req['index']
    sql = 'select id, uid, instruction from instructions where pid = %s and iorder = %s'
    cursor.execute(sql, (page_id, iorder))
    fets = cursor.fetchone()
    return Response(streaming(str(fets['instruction']), [fets,page_id]),content_type="text/event-stream")
   

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
    form = await request.form
    req = form.to_dict()
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

    output, docs = streaming(req['question'], [req['uid'], page_id, myiid, now])
    db.close()
    return {'status': 200, 'data': output, 'docs': docs}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3456)
