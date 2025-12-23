import json
from datetime import datetime
import re

def parse_GG_conversations(input_payload):
    """
    解析从前端/Zip工具传来的 JSON 数据。
    """
    
    data = input_payload
    file = data.get("file", [])
    
    try:
        conversations_list = json.loads(file)
    except json.JSONDecodeError:
        return {"status": "error", "error": "conversations.json content is not valid JSON"}

    # 情况C: 确保它现在真的是个列表
    if not isinstance(conversations_list, list):
        return {
            "status": "error", 
            "error": f"Expected conversations to be a list, but got {type(conversations_list).__name__}"
        }

    # -------------------------------------------------------
    # 3. 处理对话逻辑
    # -------------------------------------------------------
    final_output = []

    for idx, conv in enumerate(conversations_list):
        # 双重保险：如果列表里混入了字符串，跳过
        if not isinstance(conv, dict):
            print(f"Warning: Skipping item {idx} because it is not a dict: {type(conv)}")
            continue

        title = conv.get("title") or "Untitled Chat"
        create_ts = conv.get("create_time")
        
        mapping = conv.get("mapping", {})
        current_node_id = conv.get("current_node")
        
        temp_msg_list = []

        while current_node_id:
            if current_node_id == "client-created-root":
                break
            node = mapping.get(current_node_id)
            if not node: break

            parent_id = node.get("parent")

            message_obj = node.get("message")
            if not message_obj:
                current_node_id = node.get("parent")
                continue

            author = message_obj.get("author", {})
            role = author.get("role")

            if role == "system" or role == "tool":
                current_node_id = parent_id
                continue

            content_data = message_obj.get("content", {})
            parts = content_data.get("parts", [])
            
            text_content = ""
            if parts and isinstance(parts, list):
                valid_parts = [p for p in parts if isinstance(p, str)]
                if valid_parts:
                    text_content = "".join(valid_parts)

            msg_ts = message_obj.get("create_time")

            if text_content.strip():
                temp_msg_list.append({
                    "time": msg_ts,
                    "chat": text_content,
                    "role": role 
                })

            current_node_id = node.get("parent")

        temp_msg_list.reverse()

        processed_messages = []
        for index, item, in enumerate(temp_msg_list):
            processed_messages.append({
                "id": index,
                "time": item["time"],
                "chat": item["chat"],
                "role": item["role"]
            })

        if processed_messages:
            final_output.append({
                "title": title,
                "time": create_ts,
                "message": processed_messages
            })

    return final_output

def parse_DeepSeek_conversations(input_payload):
    """
    【新增】解析 DeepSeek 格式 JSON 数据
    DeepSeek 结构特点：
    1. 根节点从 'root' 开始，向下查找 'children'。
    2. message 内容在 'fragments' 中，通过 'type' 区分 REQUEST/RESPONSE。
    3. 时间格式为 ISO 8601 (2025-03-08T...)。
    """
    
    data = input_payload
    file = data.get("file", [])

    try:
        conversations_list = json.loads(file)
    except json.JSONDecodeError:
        return {"status": "error", "error": "conversations.json content is not valid JSON"}

    # 情况C: 确保它现在真的是个列表
    if not isinstance(conversations_list, list):
        return {
            "status": "error", 
            "error": f"Expected conversations to be a list, but got {type(conversations_list).__name__}"
        }

    final_output = []

    # 2. 遍历对话列表
    for conv in conversations_list:
        if not isinstance(conv, dict): continue

        title = conv.get("title") or "Untitled Chat"
        
        # 转换对话创建时间
        inserted_at_str = conv.get("inserted_at")
        create_ts = 0
        if inserted_at_str:
            try:
                # 替换 +08:00 为 +0800 以兼容旧版 python (如果需要)
                # python 3.7+ fromisoformat 支持 : 
                dt = datetime.fromisoformat(inserted_at_str)
                create_ts = dt.timestamp()
            except:
                pass
        
        mapping = conv.get("mapping", {})
        if not mapping: continue

        # DeepSeek 的遍历逻辑：从 root 开始顺着 children 走
        # 与 GPT 的反向链表不同，这是正向链表
        
        temp_msg_list = []
        current_node_id = "root" # DeepSeek 固定入口
        safety_counter = 0

        while current_node_id and safety_counter < 10000:
            safety_counter += 1
            node = mapping.get(current_node_id)
            
            if not node: break
            
            # 提取消息
            msg_obj = node.get("message")
            if msg_obj:
                # 转换消息时间
                msg_time_str = msg_obj.get("inserted_at")
                msg_ts = 0
                if msg_time_str:
                    try:
                        dt = datetime.fromisoformat(msg_time_str)
                        msg_ts = dt.timestamp()
                    except: pass
                
                # 提取内容 fragments
                fragments = msg_obj.get("fragments", [])
                full_content = ""
                role = "unknown"
                
                for frag in fragments:
                    frag_type = frag.get("type")
                    frag_content = frag.get("content", "")
                    
                    if frag_type == "REQUEST":
                        role = "user"
                    elif frag_type == "RESPONSE":
                        role = "assistant" # 或 AI
                    
                    full_content += frag_content
                
                if full_content.strip():
                    temp_msg_list.append({
                        "time": msg_ts,
                        "chat": full_content,
                        "role": role
                    })

            # 寻找下一个节点
            # 通常 DeepSeek 线性对话只有一个 child
            children = node.get("children", [])
            if children and len(children) > 0:
                # 默认取最后一个 child (通常代表最新的分支/regenerate的结果)
                # 或者取第一个，取决于 DeepSeek 导出逻辑。
                # 观察样本，通常是线性的，取 children[0] 即可。
                # 为了稳妥，如果存在多个分支，我们取最后一个 (假设是最新的)
                current_node_id = children[-1] 
            else:
                current_node_id = None # 结束

        # 格式化输出消息列表
        processed_messages = []
        for index, item in enumerate(temp_msg_list):
            processed_messages.append({
                "id": index, # 重新生成 0, 1, 2 顺序 ID
                "time": item["time"],
                "chat": item["chat"],
                "role": item["role"]
            })

        if processed_messages:
            final_output.append({
                "title": title,
                "time": create_ts,
                "message": processed_messages
            })

    return final_output


def analyze_time_distribution(parsed_result):
    """
    统计聊天时间分布（按小时 0-23）。
    接受 parse_GPT_conversations 的输出作为输入。
    """
    
    chat_data_list = parsed_result
    
    # 初始化全局统计 (0-23小时)
    # 使用字典 key=0~23, value=count
    total_hours_count = {h: 0 for h in range(24)}
    
    formatted_message_list = []

    # 2. 遍历每个对话
    for chat in chat_data_list:
        title = chat.get("title", "Untitled")
        messages = chat.get("message", [])
        
        # 初始化当前对话的统计
        current_chat_hours_count = {h: 0 for h in range(24)}
        
        has_valid_msg = False
        
        for msg in messages:
            timestamp = msg.get("time")
            
            # 确保时间戳有效
            if timestamp is not None:
                try:
                    # 将 Unix 时间戳转换为本地时间对象
                    dt = datetime.fromtimestamp(float(timestamp))
                    hour = dt.hour # 获取小时 (0-23)
                    
                    # 累加计数
                    current_chat_hours_count[hour] += 1
                    total_hours_count[hour] += 1
                    has_valid_msg = True
                except (ValueError, TypeError, OSError):
                    continue # 跳过无效时间
        
        if has_valid_msg:
            # 格式化当前对话的 map
            # 格式: [{"id": "0", "value": 12}, ...]
            chat_map = [
                {"id": str(h), "value": current_chat_hours_count[h]} 
                for h in range(24)
            ]
            
            formatted_message_list.append({
                "title": title,
                "map": chat_map
            })

    # 3. 格式化总表 (Total Map)
    total_map = [
        {"id": str(h), "value": total_hours_count[h]} 
        for h in range(24)
    ]

    # 4. 返回最终结果
    return {
        "total_map": total_map,
        "message": formatted_message_list
    }

def analyze_code_stats(chat_data_list):
    """
    统计代码行数。
    输入：parse_GPT_conversations 的输出列表。
    输出：{"codeMap": [{"codeType": "python", "value": 1200}, ...]}
    """
    code_stats = {}

    # 正则解释：
    # ```         匹配开始标记
    # ([^\n]*)    捕获组1：匹配第一行（语言类型），直到遇到换行符
    # \n          匹配第一个换行符
    # ([\s\S]*?)  捕获组2：非贪婪匹配代码主体内容
    # ```         匹配结束标记
    pattern = re.compile(r'```([^\n]*)\n([\s\S]*?)```')

    # 简单防崩检查，虽然假设输入是 list
    if not isinstance(chat_data_list, list):
        return {"codeMap": []}

    for chat in chat_data_list:
        if not isinstance(chat, dict): continue
            
        messages = chat.get("message", [])
        for msg in messages:
            content = msg.get("chat", "")
            if not isinstance(content, str) or not content:
                continue

            # 查找当前消息内的所有代码块
            matches = pattern.findall(content)
            
            for lang, code_body in matches:
                # 处理语言类型 (codeType)
                lang = lang.strip().lower() # 统一转小写 (Python -> python)
                if not lang:
                    lang = "*" # 如果没写语言，归为 *
                
                # 统计行数
                # split('\n') 会把字符串按换行符切分
                # 例如 "print('hi')\n" 切分后 len 为 2 (因为末尾有空串)，所以通常代码行数就是切分后的长度-1
                # 但为了统计直观，我们直接计算切分后的列表长度，或者使用 strip 后计算
                # 这里采用最直观逻辑：有多少个 \n 就有多少行（近似），或者 splitlines()
                
                lines_list = code_body.split('\n')
                # 如果最后一行是空的（因为 ``` 前通常有个换行），去掉它
                if lines_list and lines_list[-1] == '':
                    lines_list.pop()
                
                line_count = len(lines_list)
                
                if line_count > 0:
                    code_stats[lang] = code_stats.get(lang, 0) + line_count

    # 格式化输出
    code_map = []
    total = 0
    for lang, count in code_stats.items():
        total += count
        code_map.append({"codeType": lang, "value": count})

    # 按行数从多到少排序
    code_map.sort(key=lambda x: x["value"], reverse=True)

    return {
        "total": total,
        "codeMap": code_map}

# ... (保留之前的 analyze_code_stats 等函数) ...

def _clean_markdown_for_count(text):
    """
    辅助函数：为字数统计清洗 Markdown 符号。
    保留文本内容，只去除格式符号（如 ** [] () # 等）。
    """
    if not text:
        return ""
    
    # 1. 去除代码块标记 ```python 等，但保留代码内容以便计数
    # (如果不想统计代码字数，可以用 r'```[\s\S]*?```' 替换为空)
    text = re.sub(r'```[a-zA-Z0-9]*', '', text) 
    text = re.sub(r'```', '', text)

    # 2. 去除行内代码符号 `
    text = re.sub(r'`', '', text)

    # 3. 链接/图片：只保留描述文字 [描述](链接) -> 描述
    text = re.sub(r'!\[(.*?)\]\(.*?\)', r'\1', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)

    # 4. 去除 URL (通常不计入有效阅读字数)
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

    # 5. 去除标题 #, 粗体 **, 引用 > 等符号
    text = re.sub(r'[*#>\-\+]', '', text)
    
    return text

def _count_mixed_text(text):
    """
    辅助函数：核心计数逻辑
    规则：
    1. 中文：按字符数统计 (一个汉字算1)
    2. 英文/数字：按单词数统计 (空格分隔)
    """
    if not text:
        return 0
        
    # 清洗 Markdown
    cleaned_text = _clean_markdown_for_count(text)
    
    # 1. 统计中文字符 (以及日文/韩文等 CJK 字符)
    # 范围 \u4e00-\u9fa5 是常用汉字
    chinese_chars = re.findall(r'[\u4e00-\u9fa5]', cleaned_text)
    chinese_count = len(chinese_chars)
    
    # 2. 统计英文/数字单词
    # 先把刚才统计过的中文替换为空格，避免粘连影响英文分词
    text_without_chinese = re.sub(r'[\u4e00-\u9fa5]', ' ', cleaned_text)
    
    # 按空白字符切分 (包括空格、换行、Tab)
    # 过滤掉空的项
    english_words = [w for w in text_without_chinese.split() if w.strip()]
    english_count = len(english_words)
    
    return chinese_count + english_count

def analyze_word_count(chat_data_list):
    """
    统计字数（中英文混合）。
    输入：parse_GPT_conversations 的输出列表。
    输出：{"total_value": 12345, "mapping": [{"title": "Chat A", "value": 100}, ...]}
    """
    total_count = 0
    mapping_list = []

    # 简单的类型检查
    if not isinstance(chat_data_list, list):
        return {"total_value": 0, "mapping": []}

    for chat in chat_data_list:
        if not isinstance(chat, dict): continue
        
        title = chat.get("title", "Untitled")
        messages = chat.get("message", [])
        
        current_chat_count = 0
        
        for msg in messages:
            content = msg.get("chat", "")
            # 累加单条消息的字数
            if content and isinstance(content, str):
                current_chat_count += _count_mixed_text(content)
        
        # 累加到总数
        total_count += current_chat_count
        
        # 记录单个对话数据
        mapping_list.append({
            "title": title,
            "value": current_chat_count
        })

    # (可选) 按字数从多到少排序，方便前端展示“最长对话”
    mapping_list.sort(key=lambda x: x["value"], reverse=True)

    return {
        "total_value": total_count,
        "mapping": mapping_list
    }

def analyze_email_stats(chat_data_list):
    """
    【新增】统计邮件生成情况
    规则：检索 --- \n Subject: ... --- 的格式
    """
    total_email_words = 0
    mapping_list = []
    
    # 正则逻辑：
    # ---\s*\n      : 匹配起始的 --- 和换行
    # (             : 捕获组开始
    #   (?:[*#]+)?  : 允许 Subject 前面有 Markdown 强调符 (如 **, ##)
    #   \s*Subject: : 匹配 Subject: (忽略大小写，见 flag)
    #   [\s\S]*?    : 匹配邮件正文 (非贪婪)
    # )             : 捕获组结束
    # \s*---        : 匹配结尾的 ---
    email_pattern = re.compile(r'---\s*\n\s*((?:[*#]+)?\s*Subject:[\s\S]*?)\s*---', re.IGNORECASE)

    if not isinstance(chat_data_list, list):
        return {"total": 0, "mapping": []}

    for chat in chat_data_list:
        if not isinstance(chat, dict): continue
        
        messages = chat.get("message", [])
        
        for msg in messages:
            content = msg.get("chat", "")
            if not isinstance(content, str) or not content:
                continue
            
            # 在消息中搜索所有符合邮件格式的片段
            matches = email_pattern.findall(content)
            
            for raw_email_content in matches:
                # 1. 清洗 Markdown (得到纯文本邮件草稿)
                cleaned_email = _clean_markdown_for_count(raw_email_content).strip()
                
                # 2. 计算字数 (复用中英文混合计数)
                word_count = _count_mixed_text(cleaned_email)
                
                # 累加总数
                total_email_words += word_count
                
                # 添加到列表
                mapping_list.append({
                    "email": cleaned_email,  # 清洗后的邮件内容，方便阅读
                    "chat": content,         # 原始对话上下文
                    "words": word_count
                })
    
    
    return {
        "total": total_email_words,
        "mapping": mapping_list
    }

def analyze_bubble_counts(chat_data_list):

    Total = 0
    mapping_list = []

    for chat in chat_data_list:
        if not isinstance(chat, dict): continue
        
        title = chat.get("title", "Untitled")
        messages = chat.get("message", [])
        
        chatTotal = messages[-1].get("id", 0) + 1
        Total += chatTotal
        mapping_list.append({
            "title": title,
            "bubbles": chatTotal
        })

    mapping_list.sort(key=lambda x: x["bubbles"], reverse=True)

    return {
        "total": Total,
        "mapping": mapping_list
    }
