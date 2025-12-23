import zipfile
import io
import json
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

        
                        