var page = '';
var uid = '';
var order = 1;
var is_noob = false;
/* 전역 변수 */
var prevent = false;
$(document).ready(function(){
	const url =new URL( window.location.href);
	const path = url.pathname;
    const trigger = path.split('/');
    $.ajax({
        type:"post",
        url:"/init",
        success:function(res){
            uid = res['uid'];
            console.log(uid)
            setSidebar(res['side']);
        }
    });
    
	if(trigger[1] != 'home'){
        $('.popup').css('display','none');
        $('.initial-chat').css('display','none');

        page = trigger[2]
        $.ajax({
            type:"post",
            url:"/page_init",
            data:{
                'page':page
            },
            success:function(res){
                let index = 1;
                for(let val of res['data']){
                    $('.chat').append(setInstruction(val['instruction'],index));
                    $('.chat').append(setOutput(index));
                    $('.scroll-box').scrollTop($('.scroll-box')[0].scrollHeight);

                    if(val['output'] == 'newbie'){
                        setLoader(index);
                    }else {
                        let output = val['output'].replaceAll('\n','<br>');       
                        $('#kout'+index).find('p').append(output);
                        $('#kout'+index).find('.more-btns').css('visibility','visible');
                        setRetrieval(index,val['docs'])
                        $('.scroll-box').scrollTop($('.scroll-box')[0].scrollHeight);
                        if(val['feedback']['bias']==0){
                            let selector1 = $('#kout'+index).find('.fa-thumbs-up');
                            let selector2 = $('#kout'+index).find('.fa-thumbs-down');

                            selector1.removeClass('fa-solid');
                            selector1.addClass('fa-regular');
                            selector2.removeClass('fa-solid');
                            selector2.addClass('fa-regular');
                        } else if(val['feedback']['bias']==-1){
                            let selector2 = $('#kout'+index).find('.fa-thumbs-up');
                            let selector1 = $('#kout'+index).find('.fa-thumbs-down');

                            selector1.removeClass('fa-regular');
                            selector1.addClass('fa-solid');
                            selector2.removeClass('fa-solid');
                            selector2.addClass('fa-regular');
                        } else if(val['feedback']['bias']==1){
                            let selector1 = $('#kout'+index).find('.fa-thumbs-up');
                            let selector2 = $('#kout'+index).find('.fa-thumbs-down');

                            selector1.removeClass('fa-regular');
                            selector1.addClass('fa-solid');
                            selector2.removeClass('fa-solid');
                            selector2.addClass('fa-regular');
                        }
                        if(val['feedback']['comment']){
                            let selector = $('#kout'+index).find('.fa-comment');
                            selector.removeClass('fa-regular');
                            selector.addClass('fa-solid');
                            $('#kout'+index).find('.comment-container').css('display','flex')
                            $('#kout'+index).find('.comment-container').find('textarea').val(val['feedback']['comment']);

                        }
                    }
                    index++;
                }
                order = index-1;
                if(res['status'] == 'newbie'){
                    
                    $.ajax({
                        type:"post",
                        url:"/generate",
                        data:{
                            'page':page,
                            'index':order
                        },
                        success:function(res){
                            
                            $('.loader').css('display','none');
                            if(res[1] == 'error'){
                                prevent = true;
                                $('#kout'+order).find('p').append('<a href="javascript:location.reload()">'+res[0]+'</a>')
                            }
                            else if(res[1] !='error'){
                                textAnimation('#kout'+order,res[0]);
                                setRetrieval(order,res[1])
				            }
                        }
                    });
                }
            }
        });
	}else{
        
        setExample(1,'fa-solid fa-magic-wand-sparkles','rgb(255, 240, 23)','서울로 1박 2일 출장을 가면, 숙박비는 얼마까지 사용 가능하나요?')
        setExample(2,'fa-solid fa-question','rgb(143, 255, 255)','배우자가 출산할 경우 휴가는 최대 몇 일까지 사용 가능하나요?')
        setExample(3,'fa-solid fa-computer','#ab68ff','전문가 자문비의 원천징수 기준 금액을 알려줘.')
        setExample(4,'fa-brands fa-rebel','#ce3212','소액물품구매, 소액용역, 소액공사의 경우 계약부서를 거치지 않고 수요부서에서 직접 계약 처리할 수 있는 상한 금액은 각각 얼마인가요?')
	}
	$('.home').click(function(){
		location.href='/';
	})
    
    $('#instruction').keydown(function(e){
        if(e.which === 13 && !e.shiftKey) {
            e.preventDefault();
            if($('.btn-chat-info').attr('disabled') != 'disabled'){
                submit();
            }
        }
        chatboxControl($('#instruction'));
    })

    $('#instruction').keyup(function(){
        chatboxControl($('#instruction'));
    })

    $('.btn-chat-info').click(function(e){
        submit();
    })

    $('.closed').click(()=>{
        $('.popup').css('display','none');
    })

    $('.fa-bullhorn').click(()=>{
        $('.popup').css('display','flex');
    })

    $('.init-ex').click(function(e){
        let ex = $(this).attr('id');
        let text =$('#'+ex).children('.init-ex-text').text();
        let n_text = text;
        submit(n_text)
    });

    $('.new-btn').click(function(){
        location.href='/home';
    });

})
function setLoader(index){
    let html = `<div class="loader"></div>`;
    $('#kout'+index).find('p').append(html);
}

function setRetrieval(index,length){
    let html =`<div class="rag-text cursor-pointer" onclick="actDocs(`+index+`)">>관련 문서 (`+length+`)</div><div class="rag-result" style='display:none'></div>`;
    $('#kout'+index).find('.retrieval-box').append(html);
}
function actDocs(index){
    let selector = $('#kout'+index).find('.retrieval-box');
    if (selector.find('.rag-result').css('display') == 'none'){
        $.ajax({
            type:"post",
            url:"/get_docs",
            data:{
                'page':page,
                'order':index
            },
            success:function(res){
                
                let html = ``
                let count = 1;
                //let converter = new showdown.Converter()

                for(let doc of res){
                    let page = doc[3]==-1?'없음':doc[3]
                    let contents = doc[0].replaceAll('\n','<br>')
                    // contents = converter.makeHtml(contents);
                    let cont = '<div>'+count+': '+doc[1]+" | filename: "+doc[2]+ " | 페이지 : "+page+"</div><div>" + contents +"</div><div class='r-line'></div>"
                    html = html + cont;
                    count++;
                }
                selector.find('.rag-result').html(html);
                selector.find('.rag-result').css('display','block');
            }
        })
    } else {
        selector.find('.rag-result').css('display','none');
    }
}

function move(path){
    location.href = '/page/'+path;
}

function setSidebar(side){
    let navbar = {};
    for(let sid of side){
        if (sid['title'] == null)
            sid['title'] = '제목 없음'
        if(sid['date'] == 'today'){
            if(!('today' in navbar)){
                navbar['today']={'today':`<div class="nav-date">오늘</div>`}
            }
            if(!('titles' in navbar['today'])){
                navbar['today']['titles'] = [];
            } 
            navbar['today']['titles'].push(`<div onclick='move("`+sid['pid']+`")' class="title cursor-pointer">
            `+sid['title']+`
            </div>
            `)
        } else if(sid['date'] == 'week'){
            if(!('week' in navbar)){
                navbar['week']={'week':`<div class="nav-date">7일이내</div>`}
            }
            if(!('titles' in navbar['week'])){
                navbar['week']['titles'] = [];
            } 
            navbar['week']['titles'].push(`<div onclick='move("`+sid['pid']+`")' class="title cursor-pointer">
            `+sid['title']+`
            </div>
            `)
        } else if(sid['date'] == 'month'){
            if(!('month' in navbar)){
                navbar['month']={'month':`<div class="nav-date">30일이내</div>`}
            }
            if(!('titles' in navbar['month'])){
                navbar['month']['titles'] = [];
            } 
            navbar['month']['titles'].push(`<div onclick='move("`+sid['pid']+`")' class="title cursor-pointer">
            `+sid['title']+`
            </div>
            `)
        }        
    }
    if('today' in navbar){
        $('.nav-box').append(navbar['today']['today']);
        for(let tit of navbar['today']['titles'])
            $('.nav-box').append(tit);
    }   
    if('week' in navbar){
        $('.nav-box').append(navbar['week']['week']);
        for(let tit of navbar['week']['titles'])
            $('.nav-box').append(tit);
    }   
    if('month' in navbar){
        $('.nav-box').append(navbar['month']['month']);
        for(let tit of navbar['month']['titles'])
            $('.nav-box').append(tit);
    }   
}
function iconAct(feature,index){
    let koniID = 'kout'+index;
    if(feature == 'thumbup'){
        let selector = $('#'+koniID).find('.fa-thumbs-up');
        let selector_op = $('#'+koniID).find('.fa-thumbs-down');
        let clas = selector.attr('class');
        let clas_op = selector_op.attr('class');

        if(clas.indexOf('fa-regular')!=-1){
            selector.removeClass('fa-regular');
            selector.addClass('fa-solid');
            feedback(index,1);
            if(clas_op.indexOf('fa-solid')!=-1){
                selector_op.addClass('fa-regular');
                selector_op.removeClass('fa-solid');
            }
            
        } else if(clas.indexOf('fa-solid')!=-1){
            selector.addClass('fa-regular');
            selector.removeClass('fa-solid');
            feedback(index,0);
        }
    }else if(feature == 'thumbdown'){
        let selector = $('#'+koniID).find('.fa-thumbs-down');
        let selector_op = $('#'+koniID).find('.fa-thumbs-up');
        let clas = selector.attr('class');
        let clas_op = selector_op.attr('class');

        if(clas.indexOf('fa-regular')!=-1){
            selector.removeClass('fa-regular');
            selector.addClass('fa-solid');
            feedback(index,-1);
            if(clas_op.indexOf('fa-solid')!=-1){
                selector_op.addClass('fa-regular');
                selector_op.removeClass('fa-solid');
            }
        } else if(clas.indexOf('fa-solid')!=-1){
            selector.addClass('fa-regular');
            selector.removeClass('fa-solid');
            feedback(index,0);
        }    
    }else if(feature == 'comment'){
        let selector = $('#'+koniID).find('.fa-comment')
        let clas = selector.attr('class');
        if(clas.indexOf('fa-regular')!=-1){
            selector.removeClass('fa-regular');
            selector.addClass('fa-solid');
            $('#'+koniID).find('.comment-container').css('display','flex')
        } else if(clas.indexOf('fa-solid')!=-1){
            selector.addClass('fa-regular');
            selector.removeClass('fa-solid');
            $('#'+koniID).find('.comment-container').css('display','none')
        }    
    }
}

function feedback(id,bias,comment=''){
    if(bias==null){
        bias = -99
    }
    const url =new URL( window.location.href);
	const path = url.pathname;
    const trigger = path.split('/');
    const page = trigger[2]
    $.ajax({
        type:"post",
        url:"/feedback",
        data:{
            'page':page,
            'bias':bias,
            'oorder':id,
            'comment':comment
        },
        success:function(res){
            
        }
    });
}

function iconMover(index,clas){
    let koniID = 'kout'+index;
    $('#'+koniID).find('.'+clas).show();
    let px = '0';
    if(clas == 'thumb-up'){
        px = '-10px';
    }else if(clas == 'thumb-down'){
        px = '37px';
    }else if(clas == 'comment'){
        px = '57px';
    }
    $('.'+clas).css('left',px);
}
function iconMout(clas){
    $('.'+clas).hide();
}

function chatboxControl(sel){
    if(sel.val().length != 0 ){
        $('.btn-chat-info').removeClass('btn-chat');
        $('.btn-chat-info').addClass('btn-chat-value');
        $('.btn-chat-info').attr('disabled',false);
    } else{
        $('.btn-chat-info').addClass('btn-chat');
        $('.btn-chat-info').removeClass('btn-chat-value');
        $('.btn-chat-info').attr('disabled',true);
    }

    sel.css('height',0);
    $('.input-container').css('height',0);
    
    let scrollHeight = sel.prop('scrollHeight');
    if (scrollHeight > 340){
        sel.css('overflow-y','scroll');
        scrollHeight = 344;
    } else {
        sel.css('overflow-y','hidden');
    }
    $('.input-container').css('height',19+scrollHeight+"px");
    $('.input-container').css('margin-top',32-scrollHeight+"px");
    $('.footer-bottom').css('margin-bottom',-32+scrollHeight+"px");
    sel.css('height',scrollHeight+"px");

}
function comment(index){
    const comment = $('#kout'+index).find('.comment-container').find('textarea').val();
    feedback(index,-99,comment);
    toastr.success('코멘트가 정상적으로 작성되었습니다.')
}

function submit(msg=''){
    if(prevent)
        return;
    prevent = true;
    let text =msg; 

    if(msg =='')
        text = $('#instruction').val();
    $('#instruction').val('')

    $('.chat').append(setInstruction(text,order));
    $('.chat').append(setOutput(order));
    $('.scroll-box').scrollTop($('.scroll-box')[0].scrollHeight);
    // 아웃풋 연결 부분

    let pd = {
        'uid':uid,
        'order':order,
        'page':page,
        'question':text,
        'chat_history':[]
    }
    setLoader(order);
	$.ajax({
            type:"post",
             url:"/submit",
             data:pd,
	 	success:function(res){
            if(res['status']==300){
	 	        location.href = '/page/'+res['data'];
            } else {
                $('.loader').css('display','none');
		if(res['docs'] == 'error'){
			$('#kout'+order).find('p').append('<a href="javascript:location.reload()">'+res['data']+'</a>')
		}
		else if(res['docs'] !='error'){

			textAnimation('#kout'+order,res['data']);
            setRetrieval(order,res['docs'])
            order++;
		}
            }

        }
    
    })
}

function setInstruction(msg,index){
    msg = msg.replaceAll('<','&lt;');
    msg = msg.replaceAll('>','&gt;');
    msg = msg.replaceAll('\n','<br>');
    return "<div class='flex-right'><div class='instruction' id='kins"+index+"'><p>"+msg+"</p></div></div>";
}

function setOutput(index){
    let koni = `
    <div class="koni-output" id='kout`+index+`'> 
        <div class="icon-box">
            <div class="icon">
                <img src="/static/img/koni.jpg" alt="">
            </div>
        </div>
        <div class="chat-box">
            <div class="chat-output">
                <p>
                </p>
            </div>
            <div class="more-btns">
                <div>
                    <div class="icon-div icon-thumb-up" onmouseover='iconMover(`+index+`,"thumb-up")' onmouseout='iconMout("thumb-up")' onclick="iconAct('thumbup',`+index+`)">
                        <i class="fa-regular fa-thumbs-up"></i>            
                    </div>
                </div>
                <div>
                    <div class="icon-div icon-thumb-down" onmouseover='iconMover(`+index+`,"thumb-down")' onmouseout='iconMout("thumb-down")' onclick="iconAct('thumbdown',`+index+`)">
                        <i class="fa-regular fa-thumbs-down"></i>
                    </div>
                </div>
                <div>
                    <div class="icon-div icon-comment" onmouseover='iconMover(`+index+`,"comment")' onmouseout='iconMout("comment")' onclick="iconAct('comment',`+index+`)">
                        <i class="fa-regular fa-comment"></i>
                    </div>  
                </div>
            </div>
            <div style="width:500px;height:20px;position:relative;">
                <div class="mover-pop thumb-up">좋아요</div>
                <div class="mover-pop thumb-down">싫어요</div>
                <div class="mover-pop comment">추가 코멘트</div>
                <div class="mover-pop repeat">재실행</div>
            </div>
            <div class="comment-container">
                <div class="comment-box">
                    <textarea ></textarea>
                    <a class="cursor-pointer" onclick='comment(`+index+`)'>코멘트</a>
                </div>
            </div>
            <div class="retrieval-box">
            </div>
        </div>
        
    </div>
    `

    return koni
}

function setExample(id,icon,color,text){
    $('#ex'+id).children('.init-ex-text').text(text);
    $('#ex'+id).children('.init-ex-logo').children('i').addClass(icon);
    $('#ex'+id).children('.init-ex-logo').children('i').css('color',color);
}

function delay(ms){
    return new Promise(resolve=>setTimeout(resolve,ms));
}

var idx = 0
var intervId;
async function textAnimation(tag,text){
    text = text.replaceAll('\n','<br>');       
    intervId = setInterval(typing,10,tag,text);
}

function typing(tag,text){
    if(idx < text.length){
        if(text[idx]=='<'){
            if(text.slice(idx,idx+4) == '<br>'){
                idx = idx + 4;
                $(tag).find('p').append('<br>');
                $('.scroll-box').scrollTop($('.scroll-box')[0].scrollHeight);
                return;
            }
        }
        $(tag).find('p').append(text[idx]);
        idx++;
    } else {
        clearInterval(intervId)
        prevent =false;
        idx = 0;
        $(tag).find('.more-btns').css('visibility','visible');
    }
    $('.scroll-box').scrollTop($('.scroll-box')[0].scrollHeight);
}