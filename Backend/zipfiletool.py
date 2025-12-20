import zipfile
import io
import json

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
                    "files": [{
                        "filename": found_filename,
                        "content": json.dumps(file_text)
                    }]}
            else:
                return {
                    "status": "error", 
                    "error": f"压缩包里没找到 {TARGET_FILENAME}，请确认这是正确的导出包。"
                }
    except zipfile.BadZipFile:
        return {"error": "这不是一个有效的zip文件"}
                        