# Web-Based Full Stack Architecture for KONI Inference
한국과학기술정보연구원(KISTI)의 오픈 LLM 모델인 KONI의 인퍼런스를 위한 웹 기반 전사 시스템입니다. 과학기술 특화 LLM인 KONI에게 다양한 이야기를 건네보세요.

## 주요 의존성 패키지 버전
- Python 3.10
- Flask 3.0.3
- langchain-core 0.3.9

## private 파일 내용

**/{project}/static/private/server_info.json**
```json
{
    "STATUS": "{'test','inference'}", 
    "WAS_SERVER": "Local_WAS IP",
    "API_SERVER": "LLM model API Server",
    "ADMIN_SERVER":"AJAX ADMIN URL", // use http://~~
    "INFERENCE_TYPE": "normal"
}
```

**/{project}/static/private/database.json**
```json
{
    "host": "DB HOST Address",     
    "port": "DB PORT",     
    "user": "DB USER",      
    "passwd": "DB PW",    
    "db": "DB SCHEMA",   
    "charset": "DB CHARSET"
}
```

## API 콜 유의사항
LLM API 서버가 보안을 위해 WAS 서버 IP만 개방했을 경우, 일반적인 웹 서버로 구축하면 API 콜이 제한될 수 있습니다. **반드시 리버스 프록시**를 이용하여 WAS 서버의 IP로 우회 접근하세요.