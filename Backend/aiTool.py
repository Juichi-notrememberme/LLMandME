import re
import jieba
import os
import random
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax

def load_stop_words(filepath="stopwords.txt"):
    """
    加载外部停用词文件。
    """
    stopwords = set()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, filepath)
    
    if os.path.exists(full_path):
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word:
                        stopwords.add(word)
            print(f"成功加载停用词表，共 {len(stopwords)} 个词。")
        except Exception as e:
            print(f"读取停用词文件失败: {e}，将使用默认列表。")
    else:
        print(f"停用词文件 {filepath} 不存在，将使用默认列表。")

    if not stopwords:
        default_words = ["the", "of", "is", "的", "了", "在", "是", "我", "你"]
        stopwords.update(default_words)
        
    return list(stopwords)

# 全局加载
STOP_WORDS_LIST = load_stop_words("stopwords.txt")

def clean_markdown(text):
    """
    清洗 Markdown 及特定噪音 (如 turn0, turn1)
    """
    if not text:
        return ""

    # 1. 【新增】定点清除 "turn0", "turn1", "Turn 10" 这种模式
    # re.IGNORECASE 让它同时匹配 Turn0 和 turn0
    text = re.sub(r'\bturn\s*\d+\b', '', text, flags=re.IGNORECASE)

    # 2. 去除代码块
    text = re.sub(r'```[a-zA-Z0-9]*', '', text) 
    text = re.sub(r'```', '', text)
    text = re.sub(r'`', '', text)

    # 3. 去除链接和图片
    text = re.sub(r'!\[(.*?)\]\(.*?\)', r'\1', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

    # 4. 去除 Markdown 符号
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*|__|\*', '', text)
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\-\+\*]\s+', '', text, flags=re.MULTILINE)

    # 5. 【新增】去除看起来像乱码的长字符串 (连续超过20个字母数字且没有空格)
    # 这能过滤掉一些 base64 图片编码残留或奇怪的日志
    text = re.sub(r'\b[a-zA-Z0-9]{20,}\b', '', text)

    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()


def extract_keywords_from_chat(chat_data_list, kw_model, top_n=10, target_role='all'):
    """
    按【对话(Chat)】维度提取关键词。
    """
    results = []
    
    for chat in chat_data_list:
        title = chat.get("title", "Untitled")
        messages = chat.get("message", [])
        
        if not messages:
            continue
            
        full_text_buffer = []
        
        for msg in messages:
            msg_id = msg.get('id', 0)
            msg_role = msg.get("role", "system")
            
            # 角色筛选
            if target_role == 'user' and msg_role != "user":
                continue
            elif target_role == 'ai' and msg_role != "assistant":
                continue
            
            raw_text = msg['chat']
            clean_text = clean_markdown(raw_text)
            
            if clean_text:
                # 分词
                seg_list = jieba.cut(clean_text)
                # 过滤掉长度小于 2 的单字 (比如 "我", "做", "弄")，这能极大提升长对话的质量
                seg_text = " ".join([word for word in seg_list if word.strip() and len(word) > 1])
                full_text_buffer.append(seg_text)
        
        chat_content = "\n".join(full_text_buffer)
        
        # 过滤太短的对话
        if len(chat_content) < 20: 
            continue

        # 内存保护：保留开头 20万字
        if len(chat_content) > 200000:
            chat_content = chat_content[:200000]

        try:
            keywords = kw_model.extract_keywords(
                chat_content, 
                keyphrase_ngram_range=(1, 1), 
                stop_words=STOP_WORDS_LIST, 
                top_n=top_n, 
                use_mmr=True,
                diversity=0.42 # 如果长对话还是很乱，可以尝试把这个调低到 0.3
            )
            
            keymap = [{"name": kw[0].replace(" ", ""), "value": round(kw[1] * 100, 2)} for kw in keywords]
            
            results.append({
                "name": title,
                "children": keymap
            })
            
        except Exception as e:
            print(f"Error processing chat '{title}': {e}")
            results.append({"title": title, "keymap": []})

    # return results

    return {
        "name": "聊天关键词",
        "children": results
    }


# 1. 设置模型路径 (使用国内镜像，防止下载超时)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
MODEL_NAME = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

print(f"正在加载情绪分析模型: {MODEL_NAME} ...")
# 缓存到本地，下次启动秒开
# 【核心修复】：强制 use_fast=False
# 这会避开 transformers 库中关于 FastTokenizer 转换的那个 Bug
# XLM-RoBERTa 必须依赖 sentencepiece 库 (请确保 pip install sentencepiece)
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False)
except Exception as e:
    print(f"加载分词器失败，尝试备用方案: {e}")
    # 如果失败，尝试不带参数（虽然可能会再次触发 Bug，但值得一试）
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

print("情绪模型加载完毕！")

def get_sentiment_detail(text):
    """
    计算单段文本的情绪分。
    返回: float, 范围 [-1, 1]
    -1: 非常消极
    0:  完全中性
    +1: 非常积极
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    # 截断策略：BERT 最大支持 512 token。
    # 对于情绪分析，通常开头和结尾的情绪最强烈。
    # 这里简单截取前 512 个 token (足以覆盖绝大多数聊天气泡)
    encoded_input = tokenizer(
        text, 
        return_tensors='pt', 
        truncation=True, 
        max_length=512, 
        padding=True
    )
    
    with torch.no_grad(): # 禁用梯度计算，节省内存并加速
        output = model(**encoded_input)
    
    scores = output.logits[0].numpy()
    probs = softmax(scores) # 归一化为概率 [Neg, Neu, Pos]
    
    # scores[0] = Negative
    # scores[1] = Neutral
    # scores[2] = Positive
    
    neg = float(probs[0])
    neu = float(probs[1])
    pos = float(probs[2])

    # 计算加权分：
    # 积极概率 减去 消极概率
    # 例子：如果 积极0.8, 消极0.1 -> 得分 0.7
    # 例子：如果 积极0.1, 消极0.8 -> 得分 -0.7
    # 例子：如果 中性0.9 -> 得分 接近 0
    def fade(score : float):
        return score*score*(3 - 2 * score)

    final_score = 1 - neu
    
    return {
        "score": float(final_score),
        "probs": {
                "negative": round(neg, 4),
                "neutral": round(neu, 4),
                "positive": round(pos, 4)
            }
            }

def analyze_emotion_trend(chat_data_list):
    """
    分析所有对话的情绪波动。
    只分析【用户】 的发言。
    
    输出格式:
    {
      "total_avg": 0.2, // 用户全年的平均情绪基调
      "mapping": [
        {
          "title": "对话标题",
          "avg_score": 0.5, // 该对话平均情绪
          "timeline": [     // 情绪随时间变化曲线 (用于画折线图)
             {"id": 0, "score": 0.1}, 
             {"id": 2, "score": -0.5},
             ...
          ]
        },
        ...
      ]
    }
    """
    results = []
    global_scores = []

    # 简单的进度提示
    total_chats = len(chat_data_list)
    print(f"开始分析 {total_chats} 个对话的情绪...")

    for idx, chat in enumerate(chat_data_list):
        if not isinstance(chat, dict): continue
        
        title = chat.get("title", "Untitled")
        messages = chat.get("message", [])
        
        chat_scores = []
        timeline = []
        
        for msg in messages:
            # 只分析用户的发言 (id 为偶数: 0, 2, 4...)
            # AI 的情绪通常是莫得感情的助手，分析它没意义且浪费算力
            msg_role = msg.get("role", "assistant")
            if msg_role != "user":
                continue

            msg_id = msg.get("id", 0)
                
            content = msg.get("chat", "")
            if not content: continue
            
            # 计算分数
            detail = get_sentiment_detail(content)
            score = detail["score"]
            
            # 保留两位小数
            # score = round(score, 4)
            
            chat_scores.append(score)
            # timeline.append({
            #     "id": msg_id,
            #     "score": score, 
            #     "chat": content,
            #     "list": detail["probs"]
            #     })
            
        # 如果这个对话用户没说话，跳过
        if not chat_scores:
            continue
            
        # 计算该对话的平均情绪
        avg_chat_score = sum(chat_scores) / len(chat_scores)
        global_scores.extend(chat_scores)
        
        results.append({
            "title": title,
            "avg_score": round(avg_chat_score, 4),
            # "timeline": timeline
        })
        
    # 计算全年平均情绪
    total_avg = 0.0
    if global_scores:
        total_avg = sum(global_scores) / len(global_scores)

    return {
        "total_avg": round(total_avg, 4),
        "mapping": results
    }

# 测试代码
# if __name__ == "__main__":
#     # 模拟数据
#     mock_data = [
#         {
#             "title": "Bug调试", 
#             "message": [
#                 {"id": 0, "chat": "这代码怎么又报错了，烦死了！"}, # 用户
#                 {"id": 1, "chat": "请提供报错信息。"},           # AI
#                 {"id": 2, "chat": "I am so happy that it works now! Thanks!"} # 用户
#             ]
#         }
#     ]
#     res = analyze_emotion_trend(mock_data)
#     print(res)