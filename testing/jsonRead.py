import zipfile
import io
import json
import json
from datetime import datetime
import re

def getconservationsjson(content, TARGET_FILENAME = "conversations.json"):
    try:
        with zipfile.ZipFile(io.BytesIO(content), "r") as z:
        # 4. 遍历压缩包里的每一个文件
            found_filename = next((name for name in z.namelist() if name.endswith(TARGET_FILENAME)), None)
            if found_filename:
                file_bytes = z.read(found_filename)
                file_text = file_bytes.decode('utf-8')
                return {
                    "status": "success", 
                    "file": file_text
                    }
            else:
                return {
                    "status": "error", 
                    "error": f"压缩包里没找到 {TARGET_FILENAME}，请确认这是正确的导出包。"
                }
    except zipfile.BadZipFile:
        return {"error": "这不是一个有效的zip文件"}
                        
def parse_GG_conversations(input_payload):
    """
    解析从前端/Zip工具传来的 JSON 数据。
    """


    data = input_payload
    # -------------------------------------------------------
    # 2. 提取并解析 content
    # -------------------------------------------------------
    file = data.get("file", [])

    try:
        conversations_list = json.loads(file)
    except json.JSONDecodeError:
        return {"status": "error", "error": "conversations.json content is not valid JSON"}

    # =======================================================
    # 【修复核心】：智能处理数据结构异常
    # =======================================================
    
    # 情况A: 如果解析出来还是字符串（双重序列化问题），再解一次
    print(isinstance(conversations_list, str))

    if isinstance(conversations_list, str):
        try:
            conversations_list = json.loads(conversations_list)
        except:
            pass # 如果解不开，可能就是普通字符串，交给下面处理
            

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

def getGeminiConversationsjson(content):
    """
    专门为 Gemini 准备的提取函数。
    Gemini 导出文件名通常类似于: conversations-805fc99937f48299.json
    使用正则匹配: conversations-[乱码].json
    """
    # 匹配模式：conversations- 后面跟任意字母数字，以 .json 结尾
    pattern = re.compile(r'conversations-[a-zA-Z0-9]+\.json$')
    
    try:
        with zipfile.ZipFile(io.BytesIO(content), "r") as z:
            # 遍历压缩包里的每一个文件，寻找匹配正则的文件
            found_filename = next((name for name in z.namelist() if pattern.search(name)), None)
            
            if found_filename:
                file_bytes = z.read(found_filename)
                file_text = file_bytes.decode('utf-8')
                return {
                    "status": "success", 
                    "file": file_text
                }
            else:
                return {
                    "status": "error", 
                    "error": "压缩包里没找到符合 Gemini 格式 (conversations-*.json) 的文件。"
                }
    except zipfile.BadZipFile:
        return {"error": "这不是一个有效的zip文件"}

def SortingAI(content):
    Userjson = getconservationsjson(content, TARGET_FILENAME= "user.json")
    if Userjson.get("status", 0) == "success":
        isUserjson = True
        file = Userjson.get("file", [])
        readUserjson = json.loads(file)
        if readUserjson.get('chatgpt_plus_user', 2) == 2:
            return 'deepseek'
        else:
            return 'ChatGPT'

    else:
        isUserjson = False
        return 'may_Gemini'

def main():
    file_path = "testing/testpack.zip"
    with open(file_path, "rb") as file:
        content = file.read()
        gain = getGeminiConversationsjson(content)
        result = parse_GG_conversations(gain)
    print(result)

if __name__=='__main__':
    main()