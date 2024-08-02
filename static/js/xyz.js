const site = "http://203.250.214.35/aapi";

const query = new URLSearchParams(location.search);
let destination = ''
$(document).ready(function(){
    if (query.get('type')){
        destination = query.get('type');
    }else{
        location.href = "?type=instruction"
    }
    if (query.get('retrieval')){
        $('.input').children('input').val(query.get('retrieval'))
    }
    let page = query.get('page')?query.get('page'):1;
    let retrieval = query.get('retrieval')?query.get('retrieval'):'';
    let pid = query.get('pid')?query.get('pid'):'';
    if (page){
        let pd = {
            'type': query.get('type'),
            'page': page,
            'retrieval':retrieval,
            'pid':pid

        }

        $.ajax({
            type:'post',
            url:site+'/apage',
            data:pd,
            success:function(res){
                let numofList = 10;
                let numofPage = 5;
                $('.content-title').html(res['title']+"("+res['inscount']+")");
                if(pd['type']=='user'){
                    setUser(res);
                    pagenation($('.pagebox'),res['totcount'],numofList,numofPage,page);
	            }else if(pd['type']=='instruction'){
                    numofList = 1;
                    setInstruction(res,page);
                    pagenation($('.pagebox'),res['totcount'],numofList,numofPage,page);
                }else if(pd['type']=='good' || pd['type']=='bad' || pd['type']=='comment'|| pd['type']=='rag'){
                    $('.retrieval-box').css('display','none');
                    setPage(res);
                    pagenation($('.pagebox'),res['totcount'],numofList,numofPage,page);
                }else if(pd['type']=='normal'){
                    setPage(res,'normal');
		            $('.pagebox').html('');
                    
                }
                
            }
        })
    } 

    $('.logout').click(()=>{
        $.ajax({
            type:'post',
            url:site+'/alogout',
            success:function(res){
                if(res == '200')
                    location.reload();
            }
        })
    })

    $('.input').children('input').keydown(function(e){
        if(e.which === 13 && !e.shiftKey) {
            setRetrieval(1)
        }
    })
});

function move(destination){
    location.href = '/xyz?type='+destination
}
function goPage(pid){
    location.href = '/xyz?type=instruction&page=1&pid='+pid
}
function goRetrieval(page){
    let retrieval = '';
    if(query.get('retrieval')){
        retrieval = '&retrieval='+query.get('retrieval')
    }    
    location.href = '/xyz?type='+destination+'&page='+page+retrieval
}

function setRetrieval(page){
    location.href = '/xyz?type='+destination+'&page='+page+"&retrieval="+$('.input').children('input').val()
}
function actDoc(id){
    let selector = $('#'+id).children('.results');
    if(selector.css('display')=='none'){
        selector.css('display','block');
    } else{
        selector.css('display','none')
    }
}

function setPage(res,type='abnormal'){
    const dialogue = res['dialogues'];
    instructionHtml = ''
    let icount = 1;
    for(let d of dialogue){
        let pid = d['pid']
        let bias = d['bias']?d['bias']==1?'good':'bad':''; 
        let biasIcon = d['bias']?d['bias']==1?'<i class="fa-solid fa-thumbs-up"></i>':'<i class="fa-solid fa-thumbs-down"></i>':''; 
        let instruction = d['instruction'];
        let output = d['output'];
        let comment = d['comment'];
        let displayComment = d['comment'] == '-'?'style="display:none;"':'';
        
        let dcreated = d['created'];
        let dupdated = d['updated'];

        if(type =='normal'){
            instructionHtml += `<div class="dialogue flex `+bias+`">`
        }else{
            instructionHtml += `<div class="dialogue flex `+bias+` cursor-pointer" onclick='goPage("`+pid+`")'>`
        }
        instructionHtml += 
        
        `
            <div class="iid">
                <div>`+icount+`</div>
                <div>`+biasIcon+`</div>
                
            </div>
            <div class="main-box">
                <div class="bordering instruction">`+instruction+`</div>
                <div class="bordering output">`+output+`</div>
                <div class="bordering comment" `+displayComment+`>comment : `+comment+`</div>
            </div>
            <div class="date-box">
                <div>`+dcreated+`</div>
                <div>(`+dupdated+`)</div>
            </div>
        </div>
        `
        icount++;
    }
    
    $('.table').html(instructionHtml);
}


function setInstruction(res,page){
    let ptitle = res['etc'][0]['title'];
    let ip = res['etc'][0]['ip'];
    let uname = res['etc'][0]['name'];
    let pcreated = res['etc'][0]['created'];
    let pupdated = res['etc'][0]['updated'];
    $('.retrieval-box').prepend(`
        <div class="flex">
            <div class="mr-3">`+page+`</div>
            <div class="mr-3">`+ptitle+`</div>
            <div class="mr-3" style="text-align: center;">
                <div>`+ip+`</div>
                <div>(`+uname+`)</div>
            </div>
            <div class="mr-3" style="text-align: center;">
                <div>`+pcreated+`</div>
                <div>(`+pupdated+`)</div>
            </div>
        </div>
    `)
    const dialogue = res['dialogues'];
    instructionHtml = ''
    let icount = 1;
    for(let d of dialogue){
        let bias = d['bias']?d['bias']==1?'good':'bad':''; 
        let biasIcon = d['bias']?d['bias']==1?'<i class="fa-solid fa-thumbs-up"></i>':'<i class="fa-solid fa-thumbs-down"></i>':''; 
        let instruction = d['instruction'];
        let output = d['output'];
        let comment = d['comment'];
        let displayComment = d['comment'] == '-'?'style="display:none;"':'';
        let docs = Object.values(d['docs']);
        let docCount = 0;
        let docResult ='';
        if (!docs[0]){
            docs = null;
            docResult = ''
        }
        else {
            docCount =docs.length;
            docResult = '<div class="results" style="display:none">'
            for(let doc of docs){
                doc = doc.replaceAll('\n','<br>')
                let cont = '<div class="bordering">' + doc +"</div>"
                docResult += cont;
            }
            docResult += '</div>'
        }
        let displayDoc = docCount== 0?'style="display:none;"':'';
        
        let dcreated = d['created'];
        let dupdated = d['updated'];

        instructionHtml += `
        <div class="dialogue flex `+bias+`">
            <div class="iid">
                <div>`+icount+`</div>
                <div>`+biasIcon+`</div>
                
            </div>
            <div class="main-box">
                <div class="bordering instruction">`+instruction+`</div>
                <div class="bordering output">`+output+`</div>
                <div class="bordering comment" `+displayComment+`>comment : `+comment+`</div>
                <div id=`+d['id']+` class="bordering docs" `+displayDoc+`>
                    <div class='cursor-pointer' onclick='actDoc(`+d['id']+`)'>>더보기(`+docCount+`)</div>
                    `+docResult+`
                </div>
            </div>
            <div class="date-box">
                <div>`+dcreated+`</div>
                <div>(`+dupdated+`)</div>
            </div>
        </div>
        `
        icount++;
    }
    
    $('.table').html(instructionHtml);
}

function setUser(res){
    let keys='';
    let values = '';
    for(let k of res['key']){
        keys += `<div class="hcol col">`+k+`</div>`
    }
    let index = 1
    for(let rows of res['value']){
        values += `
            <div class="row flex flex-jc-between" id="row`+index+`">
        `
        for(let row of rows){
            values+= `<div class="tcol col" >`+row+`</div>`
        }
        values+=`</div>`
        index++;
    }
    $('.table-header').html(keys);
    $('.table-row').html(values);
}

function pagenation(pageTarget,total,numofList,numofPage,now){
    let maxPage = Math.ceil(total/numofList);
    let block = Math.abs(Math.floor(1-(now/numofPage)));
    let start = numofPage*block+1
    let end = (numofPage*block + 5) > maxPage ? maxPage : (numofPage*block + 5)
    let pageHtml = ''
    if(now != 1){
        pageHtml+=`<div class="pagenum prev cursor-pointer" onclick='goRetrieval(1)'><i class="fa-solid fa-angles-left"></i></div>`
    }
    if(block != 0){
        let tmpnum = numofPage*(block-1)+5
        pageHtml+=`<div class="pagenum prev cursor-pointer" onclick='goRetrieval(`+tmpnum+`)'><i class="fa-solid fa-angle-left"></i></div>`
    }
    for(let i = start;i<=end;i++){
        if(i==now)
            pageHtml+=`<div class="pagenum cursor-pointer now" onclick='goRetrieval(`+i+`)'>`+i+`</div>`
        else
            pageHtml+=`<div class="pagenum cursor-pointer" onclick='goRetrieval(`+i+`)'>`+i+`</div>`
    }    
    if(block != Math.floor(1-(maxPage/numofPage))){
        let tmpnum = numofPage*(block+1)+1

        pageHtml+=`<div class="pagenum prev cursor-pointer" onclick='goRetrieval(`+tmpnum+`)'><i class="fa-solid fa-angle-right"></i></div>`
    }
    if(now != maxPage){
        pageHtml+=`<div class="pagenum prev cursor-pointer" onclick='goRetrieval(`+maxPage+`)'><i class="fa-solid fa-angles-right"></i></div>`
    }

    pageTarget.html(pageHtml);
}

