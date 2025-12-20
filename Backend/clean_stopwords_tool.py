import os
import re

def clean_stop_words_file(input_path="stopwords.txt", output_path="stopwords_clean.txt"):
    """
    读取停用词文件，执行以下操作：
    1. 去重
    2. 排序
    3. 【新增】智能处理英文缩写 (don't -> don, t, dont) 消除 sklearn 警告
    """
    
    if not os.path.exists(input_path):
        print(f"错误：找不到文件 {input_path}")
        return

    print(f"正在读取 {input_path} ...")
    
    unique_words = set()
    
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip()
                if not word:
                    continue
                
                # 1. 加入原词
                unique_words.add(word)
                
                # 2. 【核心修复】处理英文缩写/撇号
                # 如果词中包含单引号 (例如 "don't", "we'll", "c'mon")
                if "'" in word:
                    # 变体A: 去掉引号 (don't -> dont)
                    no_quote = word.replace("'", "")
                    unique_words.add(no_quote)
                    
                    # 变体B: 按引号切分 (don't -> don, t)
                    # 这是 sklearn 默认分词器的行为
                    parts = word.split("'")
                    for part in parts:
                        if part: # 防止空字符串
                            unique_words.add(part)
                            
    except UnicodeDecodeError:
        print("编码错误：请确保 txt 文件是 UTF-8 格式。")
        return

    # 3. 排序
    sorted_words = sorted(list(unique_words))
    
    # 4. 写入新文件
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for word in sorted_words:
                f.write(word + "\n")
        
        print(f"✅ 处理完成！")
        print(f"最终词数: {len(sorted_words)}")
        print(f"文件已保存为: {output_path}")
        print("-" * 30)
        print("提示：请将新生成的 stopwords_clean.txt 重命名为 stopwords.txt 并替换原文件。")
        
    except Exception as e:
        print(f"写入文件失败: {e}")

if __name__ == "__main__":
    clean_stop_words_file()