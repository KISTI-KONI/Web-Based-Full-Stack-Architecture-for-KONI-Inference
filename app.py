import sys
sys.path.append('./static/utils/')
from utils import connect_db,connect_serverinfo,randomAscii

from flask import Flask,request,render_template,redirect,url_for,session
from flask_cors import CORS
import json,pymysql,datetime
from pytz import timezone
from langserve import RemoteRunnable
from langchain_core.documents import Document
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.secret_key = 'kisti-koni-largescaleairesearchgroup'
DB_INFO = connect_db()
SERVER_INFO = connect_serverinfo()


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

@app.route('/page/<pid>',methods=['GET','POST'])
def page(pid):  
    return render_template('index.html')
    
@app.route('/init',methods=['POST'])
def wru():
    db = pymysql.connect(
        host=DB_INFO['host'],     
        port=DB_INFO['port'],     
        user=DB_INFO['user'],      
        passwd=DB_INFO['passwd'],    
        db=DB_INFO['db'],   
        charset=DB_INFO['charset'],
    )

    cursor = db.cursor()
    ip=request.headers.get('X-forwarded-for')
    if not ip:
        ip = '127.0.0.1'
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

### API ###

API_SERVER = SERVER_INFO['API_SERVER']
WAS_SERVER = SERVER_INFO['WAS_SERVER']

def generateOutput(db,cursor,text,settings):
    headers = {'Content-Type': 'application/json; charset=utf-8'}                                                                                                                                                                        
    print(text)
    docscount = 0
    try:                                                                                                                                                                                            
        remote_runnable = RemoteRunnable(API_SERVER+'/singleturn')                                                                                                                                                     
        output = remote_runnable.invoke({"question":text,"session_id":settings[1]})                                                                                                                                          
        docs=[]
        print(output)
        sql='insert into outputs set output=%s,uid = %s,pid=%s,iid=%s,created = %s'
        cursor.execute(sql,(output,settings[0],settings[1],settings[2],settings[3]))
        oid = cursor.lastrowid
        sql='update pages set title=%s,updated = %s where id = %s'
        cursor.execute(sql,(output[0:31],settings[3],settings[1]))
        db.commit()
    except:
        output="예기치 못한 오류가 발생하였습니다. 새로고침하여 재실행해주세요."
        docscount='error'
    return output,docscount

@app.route('/generate',methods=['POST'])
def generate():
    db = pymysql.connect(
        host=DB_INFO['host'],     
        port=DB_INFO['port'],     
        user=DB_INFO['user'],      
        passwd=DB_INFO['passwd'],    
        db=DB_INFO['db'],   
        charset=DB_INFO['charset'],
    )
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
    db = pymysql.connect(
        host=DB_INFO['host'],     
        port=DB_INFO['port'],     
        user=DB_INFO['user'],      
        passwd=DB_INFO['passwd'],    
        db=DB_INFO['db'],   
        charset=DB_INFO['charset'],
    )
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
        host=DB_INFO['host'],     
        port=DB_INFO['port'],     
        user=DB_INFO['user'],      
        passwd=DB_INFO['passwd'],    
        db=DB_INFO['db'],   
        charset=DB_INFO['charset'],
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
        host=DB_INFO['host'],     
        port=DB_INFO['port'],     
        user=DB_INFO['user'],      
        passwd=DB_INFO['passwd'],    
        db=DB_INFO['db'],   
        charset=DB_INFO['charset'],
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
        host=DB_INFO['host'],     
        port=DB_INFO['port'],     
        user=DB_INFO['user'],      
        passwd=DB_INFO['passwd'],    
        db=DB_INFO['db'],   
        charset=DB_INFO['charset'],
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
    print(status)
    return status

@app.route('/alogout',methods=['POST'])
def alogout():
    session.pop('userid', None)
    return '200'

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=3457,debug=True)