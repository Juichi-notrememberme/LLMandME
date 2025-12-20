from fastapi import FastAPI, UploadFile, File
from keybert import KeyBERT
from fastapi.middleware.cors import CORSMiddleware
from zipfiletool import getconservationsjson
from jsonTool import parse_GG_conversations
from jsonTool import parse_DeepSeek_conversations
from jsonTool import analyze_time_distribution
from jsonTool import analyze_code_stats
from jsonTool import analyze_word_count
from jsonTool import analyze_email_stats
from jsonTool import analyze_bubble_counts
from aiTool import extract_keywords_from_chat
from aiTool import analyze_emotion_trend

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("正在初始化 关键词 AI 模型...")
GLOBAL_KW_MODEL = KeyBERT(model='paraphrase-multilingual-MiniLM-L12-v2')
print("模型加载完毕！")

@app.post("/upload_zip/")
async def process_zip(file: UploadFile = File(...)):
    # 1. 读取上传的文件内容到内存
    content = await file.read()
    # 2. 准备返回的数据列表
    process1 = getconservationsjson(content)
    # process2 = parse_GG_conversations(process1)
    process2 = parse_DeepSeek_conversations(process1)
    time = analyze_time_distribution(process2)
    words = analyze_word_count(process2)
    bubbles = analyze_bubble_counts(process2)
    code = analyze_code_stats(process2)
    emotions = analyze_emotion_trend(process2)
    keywords = extract_keywords_from_chat(
        chat_data_list=process2, 
        kw_model=GLOBAL_KW_MODEL,  # <--- 传参
        top_n=7,
        target_role="all"
    )

    return {
                    "status": "success", 
                    "files": [time, words, bubbles, code, emotions, keywords]
    }
# 做了词云，做了小时统计，做了代码统计, 字数统计