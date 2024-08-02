from flask import Flask,request,render_template,redirect,url_for,session
from flask_cors import CORS, cross_origin
import random as rd
import glob,os,jsonlines,json,pymysql,datetime,time,random,string,requests,copy
from pytz import timezone
from langserve import RemoteRunnable
from langchain_core.documents import Document
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.secret_key = 'kisti-koni-largescaleairesearchgroup'

def randomAscii():
    rand_str = ''
    for i in range(64):
        rand_str += str(random.choice(string.ascii_uppercase + string.digits))
    return rand_str

@app.route('/',methods=['GET'])
def init():
    return redirect(url_for('home'))

@app.route('/xyz',methods=['GET','POST'])
def admin():
    if 'userid' in session:
        if session['userid'] == 'admin':
            return render_template('admin.html')
    return render_template('admin_login.html')

@app.route('/home',methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/init',methods=['POST'])
def wru():
    db = pymysql.connect(
        host='127.0.0.1',     
        port=3306,     
        user='mykoni',      
        passwd='kisti123',    
        db='konidb',   
        charset='utf8'
    )

    cursor = db.cursor()
    ip=request.headers.get('X-forwarded-for')
    print(ip)
    sql='select id from user where ip = %s'
    cursor.execute(sql,ip)
    uid = cursor.rowcount
    myid = cursor.fetchone()
    now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')
    # 유저 첫 접근시 아이디 생성
    if not uid :
        sql='insert into user set ip = %s,created=%s'
        cursor.execute(sql,(ip,now))
        myid = cursor.lastrowid
        myid = str(myid)
    else :
        myid = str(myid[0])
    db.commit()
    # 사이드 네비 생성
    sql='select id from pages where uid = %s and uid != 5'
    cursor.execute(sql,myid)
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
    return {'side':res,'uid':myid}

@app.route('/page/<pid>',methods=['GET','POST'])
def page(pid):  
    return render_template('index.html')

def generateOutput(db,cursor,text,settings):
    headers = {'Content-Type': 'application/json; charset=utf-8'}                                                                                                                                                                        
    print(text)
    docscount = 0
    try:
        texts = requests.post('http://127.0.0.1:4000/classify',headers=headers,data=text)    
        output = ""                                                                                                                                    
        if texts.status_code == 200 :
            cls_res = texts.json()                                                                                                                                                                                                           
            if cls_res['intent'] == 'general' :                                                                                                                                                                                              
                remote_runnable = RemoteRunnable('http://150.183.252.61:3000/multiturn')                                                                                                                                                     
                output = remote_runnable.invoke({"question":cls_res['text'],"session_id":settings[1]}) #cls_res['text']                                                                                                                                             
                docs=[]
    
            elif cls_res['intent'] == 'rag':                                                                                                                                                                          
                remote_runnable = RemoteRunnable('http://150.183.252.61:3000/retrieval')                                                                                                                                                     
                result = remote_runnable.invoke(cls_res['text'])                                                                                                                                                                             
                docs = result['result_context']
                output = result['result']
                
        
        print(output)
    # docs = [{
    #     'page_content':'## 제40조(휴가수속) 직원이 휴가를 얻고자 할 때에는 사전에 소속부서장의 허가를 얻어 주관 부서 에 신청서를 제출하여야 한다.\n\n\n#',
    #     'metadata':{'field':'지침 및 법령','filename':'test.pdf','page':-1}
    # },{
    #     'page_content':'## 1. 신청개요\n\n| 기 업 체 명    | 대           | 표   | 자   |',
    #     'metadata':{'field':'지침 및 법령','filename':'test.pdf','page':-1}
    # },{
    #     'page_content':'## 제40조(휴가수속) 직원이 휴가를 얻고자 할 때에는 사전에 소속부서장의 허가를 얻어 주관 부서 에 신청서를 제출하여야 한다.\n\n\n#',
    #     'metadata':{'field':'지침 및 법령','filename':'test.pdf','page':-1}
    # }]
    # output= 'test yes'
    # time.sleep(1)

        sql='insert into outputs set output=%s,uid = %s,pid=%s,iid=%s,created = %s'
        cursor.execute(sql,(output,settings[0],settings[1],settings[2],settings[3]))
        oid = cursor.lastrowid
        if cls_res['intent'] == 'rag':
            print(docs[0].dict())
            for doc in docs :
                docscount+=1
                new_doc = doc.dict()
                sql='insert into docs set oid=%s,contents=%s,field=%s,filename=%s,page=%s'
                cursor.execute(sql,(oid,new_doc['page_content'],new_doc['metadata']['field'],new_doc['metadata']['filename'],new_doc['metadata']['page']))
        sql='update pages set title=%s,updated = %s where id = %s'
        cursor.execute(sql,(output[0:31],settings[3],settings[1]))
        db.commit()
    except:
        output="예기치 못한 오류가 발생하였습니다. 새로고침하여 재실행해주세요."
        docscount='error'
    return output,docscount

@app.route('/generate',methods=['POST'])
def generate():
    db = pymysql.connect(host='127.0.0.1',port=3306,user='mykoni',passwd='kisti123',db='konidb',charset='utf8')
    req = request.form.to_dict()
    cursor = db.cursor()
    page_id = req['page']
    iorder = req['index']
    sql = 'select id,uid,instruction from instructions where pid = %s and iorder=%s'
    cursor.execute(sql,(page_id,iorder))
    fets = cursor.fetchone()
    now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')
    
    output,docs = generateOutput(db,cursor,str(fets[2]),[str(fets[1]),page_id,str(fets[0]),now])
    return [output,docs]

@app.route('/get_docs',methods=['POST'])
def getDocs():
    db = pymysql.connect(host='127.0.0.1',port=3306,user='mykoni',passwd='kisti123',db='konidb',charset='utf8')
    req = request.form.to_dict()
    cursor = db.cursor()
    page_id = req['page']
    iorder = req['order']
    sql='select b.id from instructions a left join outputs b on a.id = b.iid where a.pid = %s and a.iorder = %s'
    cursor.execute(sql,(page_id,iorder))
    fets = cursor.fetchone()
    oid = fets[0]
    sql = 'select contents,field,filename,page from docs where oid=%s'
    cursor.execute(sql,oid)
    fets = cursor.fetchall()
    docs = list(fets)
    return docs

@app.route('/page_init',methods=['POST'])
def pinit():
    db = pymysql.connect(
        host='127.0.0.1',     
        port=3306,     
        user='mykoni',      
        passwd='kisti123',    
        db='konidb',   
        charset='utf8'
    )
    req = request.form.to_dict()
    cursor = db.cursor()
    page_id = req['page']
    now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')
    history = []

    # page 모든 ins + output 꺼내옴
    sql='select id,uid,instruction from instructions where pid = %s order by iorder asc'
    cursor.execute(sql,page_id)
    fets = cursor.fetchall()
    status = 'history'
    for ins in fets :
        docs = []
        sql='select a.output,b.bias,b.comment,a.id as oid from outputs a left join feedbacks b on a.id = b.oid where a.iid = %s'
        cursor.execute(sql,str(ins[0]))
        exist = cursor.rowcount
        if exist != 0 :
            result = cursor.fetchone()
            output = str(result[0])
            bias = result[1]
            comment = result[2]
            sql='select contents,field,filename,page from docs where oid=%s'
            cursor.execute(sql,str(result[3]))
            fets = cursor.rowcount
            docs = fets
        else :
            status='newbie'
            # output = generateOutput(db,cursor,str(ins[2]),[str(ins[1]),page_id,str(ins[0]),now])
            bias = 0
            comment = ''
            output='newbie'

        interact = {'instruction':str(ins[2]),'output':str(output),'feedback':{'bias':bias,'comment':comment},'docs':docs}
        history.append(interact)
    db.close()
    return {'status':status,'data':history}


@app.route('/submit',methods=['POST'])
def submit():
    db = pymysql.connect(
        host='127.0.0.1',     
        port=3306,     
        user='mykoni',      
        passwd='kisti123',    
        db='konidb',   
        charset='utf8'
    )
    req = request.form.to_dict()
    cursor = db.cursor()
    page_id = req['page']
    now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')
    newbie = False
    if not page_id :
        newbie = True
        while 1 :
            page_id = randomAscii()        
            sql='select id from pages where id = %s'
            cursor.execute(sql,page_id)
            pid = cursor.rowcount
            if pid != 0 :
                continue
            else :
                break
        sql='insert into pages set id = %s,uid = %s,created = %s,updated = %s'
        cursor.execute(sql,(page_id,req['uid'],now,now))
        db.commit()

    text = req['question']
    sql='insert into instructions set instruction=%s,uid = %s,pid=%s,iorder=%s,created = %s'
    cursor.execute(sql,(text,req['uid'],page_id,req['order'],now))
    db.commit()

    myiid = cursor.lastrowid

    db.commit()
    
    if newbie :
        db.close()
        return {'status':300,'data':page_id}

    output,docs = generateOutput(db,cursor,req['question'],[req['uid'],page_id,myiid,now])
    db.close()
    return {'status':200,'data':output,'docs':docs}

@app.route('/feedback',methods=['POST'])
def feedback():
    db = pymysql.connect(
        host='127.0.0.1',     
        port=3306,     
        user='mykoni',      
        passwd='kisti123',    
        db='konidb',   
        charset='utf8'
    )
    req = request.form.to_dict()
    cursor = db.cursor()
    page_id = req['page']
    bias = req['bias']
    

    now = datetime.datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')

    sql='select b.id from instructions a left join outputs b on a.id = b.iid where a.pid = %s and a.iorder = %s'
    cursor.execute(sql,(page_id,req['oorder']))
    fets = cursor.fetchone()
    oid = fets[0]

    # 기존 피드백 찾기
    sql='select id,bias,comment from feedbacks where oid=%s'
    cursor.execute(sql,oid)
    exist = cursor.rowcount
    fets = cursor.fetchone()
    if exist == 0:
        fdbk = [0,0,'']
        if bias == '-99':
            bias = fdbk[1]
        sql='insert into feedbacks set oid=%s,bias=%s,comment=%s,created=%s,updated=%s'
        cursor.execute(sql,(oid,bias,req['comment'],now,now))
        fdbk[0] = cursor.lastrowid
    else : 
        fdbk = list(fets)
        if bias == '-99':
            bias = fdbk[1]
        sql='update feedbacks set bias=%s,comment=%s,updated=%s where oid =%s'
        cursor.execute(sql,(bias,req['comment'],now,oid))

    sql='insert into update_logs set fid=%s,comment_b=%s,comment_a=%s,bias_b=%s,bias_a=%s,created=%s'
    cursor.execute(sql,(fdbk[0],fdbk[2],req['comment'],fdbk[1],bias,now))
    sql='update pages set updated = %s where id = %s'
    cursor.execute(sql,(now,page_id))
    db.commit()

    return 'good'

### ADMIN 

@app.route('/alogin',methods=['POST'])
def alogin():
    req = request.form.to_dict()
    if req['id'] != 'admin':
        return '400'
    if req['password'] != 'k1234!':
        return '400'
    session['userid'] = 'admin'
    status = '200'
    return status

@app.route('/alogout',methods=['POST'])
def alogout():
    session.pop('userid', None)
    return '200'

@app.route('/apage',methods=['POST'])
def apage():
    if session['userid'] != 'admin':
        return {'status' : 400}
    db = pymysql.connect(
        host='127.0.0.1',     
        port=3306,     
        user='mykoni',      
        passwd='kisti123',    
        db='konidb',   
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor
    )

    cursor = db.cursor()
    req = request.form.to_dict()
    line = 10
    title=''
    etc=[]
    results = []
    dialogues=[]
    if req['type'] == 'user':
        title = '사용자 관리'
        sql=f'select count(id) as count from user'
        cursor.execute(sql)
        fetone = cursor.fetchone()
        count = fetone['count']
        sql=f'select * from user limit {(int(req["page"])-1)*line},{line}'
        cursor.execute(sql)
        results = cursor.fetchall()
        ins_counts = count

    elif req['type'] == 'instruction':
        if req['pid'] :
            pid = req['pid']
            count = 1
            sql=f'select a.id as pid,b.ip,b.name,a.title,a.created,a.updated from pages a left join user b on a.uid = b.id where a.id = "{pid}"'
            cursor.execute(sql)
            fets = cursor.fetchone()
            etc = []
            for key,value in fets.items():
                if key =='created' or key == 'updated':
                    if value :
                        value = strfDatetime(value)
                if not value :
                    value ='-'
                fets[key]=value
            etc.append(fets)
            ins_count_sql = f'select count(id) as count from instructions  where pid = "{pid}"'
        else:    
            title = '대화 통계'
            if req['retrieval'] == '':
                sql=f'select count(id) as count from pages'
                cursor.execute(sql)
                fetone = cursor.fetchone()
                count = fetone['count']
                sql=f'select a.id as pid,b.ip,b.name,a.title,a.created,a.updated from pages a left join user b on a.uid = b.id order by a.created asc limit {(int(req["page"])-1)},1'
                cursor.execute(sql)
                fets = cursor.fetchone()
                etc = []
                for key,value in fets.items():
                    if key =='created' or key == 'updated':
                        if value :
                            value = strfDatetime(value)
                    if not value :
                        value ='-'
                    fets[key]=value
                etc.append(fets)
                ins_count_sql = "select count(id) as count from instructions"

            else :
                sql=f'select c.id from instructions a left join outputs b on a.id = b.iid left join pages c on c.id = a.pid where a.instruction like %s  order by c.created asc'
                cursor.execute(sql,"%"+req['retrieval']+"%")
                fetone = cursor.fetchall()
                new_pids = []
                for f in fetone:
                    new_pids.append("'"+f['id']+"'")
                pids = list(set(new_pids))
                count = len(pids)
                str_pids = ','.join(pids) if count != 0 else '""'
                sql=f'select a.id as pid,b.ip,b.name,a.title,a.created,a.updated from pages a left join user b on a.uid = b.id where a.id in ({str_pids}) order by a.created  asc limit {(int(req["page"])-1)},1'
                cursor.execute(sql)
                fets = cursor.fetchone()
                etc = []
                if fets :
                    for key,value in fets.items():
                        if key =='created' or key == 'updated':
                            if value :
                                value = strfDatetime(value)
                        if not value :
                            value ='-'
                        fets[key]=value
                    etc.append(fets)
                    ins_count_sql = f"select count(id) as count from instructions  where pid in ({str_pids})"
                else :
                    ins_count_sql = f"select count(id) as count from instructions  where pid in ('')"
        cursor.execute(ins_count_sql)
        counts = cursor.fetchone()
        ins_counts = counts['count']
        if fets :
            sql=f'select a.id,a.instruction, b.output,c.bias,c.comment,d.contents,a.created,b.created as updated from instructions a left join outputs b on a.id = b.iid left join feedbacks c on b.id = c.oid left join docs d on b.id = d.oid where a.pid =%s order by a.iorder asc; '
            cursor.execute(sql,fets['pid'])
            page_dialogues = cursor.fetchall()          
        
            idx = 0
            clk_id = ''
            one_dialogue = {}
            for dialogue in page_dialogues:
                if clk_id != dialogue['id']:
                    if idx != 0 :
                        dialogues.append(one_dialogue)
                    clk_id = dialogue['id']
                    one_dialogue = {'id':clk_id}
                    one_dialogue['instruction'] = dialogue['instruction']
                    one_dialogue['output'] = dialogue['output'] if dialogue['output'] else '-'
                    one_dialogue['bias'] = dialogue['bias']
                    one_dialogue['comment'] = dialogue['comment'] if dialogue['comment'] else '-'
                    one_dialogue['created'] = strfDatetime(dialogue['created'])
                    one_dialogue['updated'] = strfDatetime(dialogue['updated'])
                    one_dialogue['docs'] = []
                one_dialogue['docs'].append(dialogue['contents'])
                
                idx+=1  
            dialogues.append(one_dialogue)
        else :
            pass
    elif req['type'] == 'good' or req['type'] == 'bad' or req['type'] == 'comment': 
        if req['type'] == 'good':
            title = '좋아요 대화'
            where = 'where bias = 1'
        elif req['type'] == 'bad':
            title = '싫어요 대화'
            where = 'where bias = -1'
        elif req['type'] == 'comment':
            title='피드백 코멘트'
            where = 'where comment != ""'

        sql=f'select count(a.id) as count from instructions a left join outputs b on a.id = b.iid left join feedbacks c on b.id = c.oid {where}'
        cursor.execute(sql)
        fetone = cursor.fetchone()
        count = fetone['count']
        sql=f'select a.id,a.pid,a.instruction, b.output,c.bias,c.comment,a.created,b.created as updated from instructions a left join outputs b on a.id = b.iid left join feedbacks c on b.id = c.oid {where} limit {(int(req["page"])-1)*line},{line}'
        cursor.execute(sql)
        page_dialogues = cursor.fetchall()
        idx = 0
        clk_id = ''
        one_dialogue = {}
        for dialogue in page_dialogues:
            clk_id = dialogue['id']
            one_dialogue = {'id':clk_id}
            one_dialogue['pid'] = dialogue['pid']
            one_dialogue['instruction'] = dialogue['instruction']
            one_dialogue['output'] = dialogue['output'] if dialogue['output'] else '-'
            one_dialogue['bias'] = dialogue['bias']
            one_dialogue['comment'] = dialogue['comment'] if dialogue['comment'] else '-'
            one_dialogue['created'] = strfDatetime(dialogue['created'])
            one_dialogue['updated'] = strfDatetime(dialogue['updated'])
            one_dialogue['docs'] = [None]
            dialogues.append(one_dialogue)
        ins_counts = count
    elif req['type'] == 'normal' or req['type'] == 'rag':
        if req['type'] == 'rag':
            title = 'RAG 적용'
            where = 'where contents is not null group by a.id'
        elif req['type'] == 'normal':
            title = 'RAG 미적용'
            where = 'where contents is null group by a.id'
        sql=f'select count(a.id) as count from instructions a left join outputs b on a.id = b.iid left join docs c on b.id = c.oid {where}'
        cursor.execute(sql)
        fetone = cursor.fetchone()
        count = fetone['count']
        sql=f'select a.id,a.pid,a.instruction, b.output,c.bias,c.comment,a.created,d.contents,b.created as updated from instructions a left join outputs b on a.id = b.iid left join feedbacks c on b.id = c.oid left join docs d on b.id = d.oid {where} limit {(int(req["page"])-1)*line},{line}'
        cursor.execute(sql)
        page_dialogues = cursor.fetchall()
        idx = 0
        clk_id = ''
        one_dialogue = {}
        for dialogue in page_dialogues:
            if clk_id != dialogue['id']:
                if idx != 0 :
                    dialogues.append(one_dialogue)
                clk_id = dialogue['id']
                one_dialogue = {'id':clk_id}
                one_dialogue['pid'] = dialogue['pid']
                one_dialogue['instruction'] = dialogue['instruction']
                one_dialogue['output'] = dialogue['output'] if dialogue['output'] else '-'
                one_dialogue['bias'] = dialogue['bias']
                one_dialogue['comment'] = dialogue['comment'] if dialogue['comment'] else '-'
                one_dialogue['created'] = strfDatetime(dialogue['created'])
                one_dialogue['updated'] = strfDatetime(dialogue['updated'])
                one_dialogue['docs'] = []
            one_dialogue['docs'].append(dialogue['contents'])
            
            idx+=1  
        dialogues.append(one_dialogue)
        ins_counts = count
    keys = []
    values = []
    print(results)
    for v in results :
        ktmp = []
        vtmp = []
        for key,value in v.items():
            if key =='created' or key == 'updated':
                if value :
                    value = strfDatetime(value)
            if not value :
                value ='-'
            ktmp.append(key)
            vtmp.append(value)

        keys = copy.deepcopy(ktmp)
        values.append(vtmp)
    return {'title':title,'key':keys,'value':values,'totcount':count,'inscount':ins_counts,'etc':etc,'dialogues':dialogues}

def strfDatetime(datetime):
    if not datetime:
        return '-'
    d = str(datetime)[5:16].split(' ')[0].split('-')
    t = str(datetime)[5:16].split(' ')[1].split(':')
    return f"{d[0]}월{d[1]}일 {str(int(t[0]))}시{t[1]}분"

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=3456,debug=True) 
