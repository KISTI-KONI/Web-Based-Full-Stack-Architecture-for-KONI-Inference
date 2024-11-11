import sys
sys.path.append('./static/utils/')
from utils import connect_db

from flask import Flask,request,session
from flask_cors import CORS, cross_origin
import random as rd
import os,json,pymysql,datetime,time,random,string,requests,copy
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.secret_key = 'kisti-koni-largescaleairesearchgroup'

@app.route('/aapi/apage',methods=['POST'])
def apage():
    dbinfo = connect_db()
    db = pymysql.connect(
        host=dbinfo['host'],     
        port=dbinfo['port'],     
        user=dbinfo['user'],      
        passwd=dbinfo['passwd'],    
        db=dbinfo['db'],   
        charset=dbinfo['charset'],
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
                sql=f'select c.id from instructions a left join outputs b on a.id = b.iid left join pages c on c.id = a.pid where (a.instruction like %s or b.output like %s) order by c.created asc'
                cursor.execute(sql,("%"+req['retrieval']+"%","%"+req['retrieval']+"%"))
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
    elif req['type'] == 'normal' :
        title = '대화검색 (페이지 미적용)'
        where = 'where instruction like %s'
        sql=f'select count(id) as count from instructions {where}'
        cursor.execute(sql,"%"+req['retrieval']+"%")
        fetone = cursor.fetchone()
        count = fetone['count']
        sql=f'select a.id,a.pid,a.instruction, b.output,c.bias,c.comment,a.created,b.created as updated from instructions a left join outputs b on a.id = b.iid left join feedbacks c on b.id = c.oid {where} order by a.created asc'
        cursor.execute(sql,"%"+req['retrieval']+"%")
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
            dialogues.append(one_dialogue)
            idx+=1  
        ins_counts = count
        results=[]
    keys = []
    values = []
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
    app.run(host='0.0.0.0',port=4567,debug=True) 
