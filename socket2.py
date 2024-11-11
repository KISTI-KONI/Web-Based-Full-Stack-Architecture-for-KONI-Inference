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

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=3456,debug=True) 
