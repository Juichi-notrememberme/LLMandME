from fastapi import FastAPI, UploadFile, File
from keybert import KeyBERT
from fastapi.middleware.cors import CORSMiddleware
from zipfiletool import getconservationsjson
from zipfiletool import getGeminiConversationsjson
from zipfiletool import SortingAI
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
    # 2. 判断类型
    sort = SortingAI(content)
    if sort == "ChatGPT":
        text = getconservationsjson(content)
        chatlist = parse_GG_conversations(text)
    elif sort == "deepseek":
        text = getconservationsjson(content)
        chatlist = parse_DeepSeek_conversations(text)
    else:
        text = getGeminiConversationsjson(content)
        chatlist = parse_GG_conversations(text)
    # 3. 处理数据
    time = analyze_time_distribution(chatlist)
    words = analyze_word_count(chatlist)
    bubbles = analyze_bubble_counts(chatlist)
    code = analyze_code_stats(chatlist)
    emotions = analyze_emotion_trend(chatlist)
    keywords = extract_keywords_from_chat(
        chat_data_list=chatlist, 
        kw_model=GLOBAL_KW_MODEL,  # <--- 传参
        top_n=7,
        target_role="all"
    )

    return {
                    "status": "success", 
                    "files": [time, words, bubbles, code, emotions, keywords]
                    # "files": [chatlist]
    }
# 做了词云，做了小时统计，做了代码统计, 字数统计