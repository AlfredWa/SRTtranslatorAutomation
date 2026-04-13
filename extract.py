import re
import os

# ================= 配置区 =================
INPUT_SRT_PATH = "侯门主母不好惹_全集中文.srt"  # 你原始的大文件路径
OUTPUT_SAMPLE_PATH = "sample_100.srt"         # 提取出来的样本保存路径
SAMPLE_LIMIT = 1                            # 你想要提取的条数
# =========================================

def parse_raw_srt(file_content):
    """
    解析基础的 SRT 文件，清洗标签，返回字典列表
    """
    # 1. 清洗掉大模型附带的 等多余系统标签
    cleaned_content = re.sub(r'\\s*', '', file_content)
    
    # 2. SRT 格式通常由双换行符分割每个字幕块
    blocks = cleaned_content.strip().split('\n\n')
    
    parsed_data = []
    for block in blocks:
        lines = block.strip().split('\n')
        # 一个正常的字幕块至少包含3行：序号、时间轴、文本
        if len(lines) >= 3:
            parsed_data.append({
                "index": lines[0].strip(),
                "timecode": lines[1].strip(),
                "text": "\n".join(lines[2:]).strip() # 将所有文本行合并（防止多行字幕）
            })
    return parsed_data

def build_srt_text(blocks):
    """
    将解析后的字典列表重新组装成标准的 SRT 文本格式
    """
    srt_text = ""
    for block in blocks:
        srt_text += f"{block['index']}\n{block['timecode']}\n{block['text']}\n\n"
    return srt_text.strip()

if __name__ == "__main__":
    print(f"▶ 开始从 {INPUT_SRT_PATH} 提取前 {SAMPLE_LIMIT} 条字幕...")
    
    # 检查文件是否存在
    if not os.path.exists(INPUT_SRT_PATH):
        print(f"❌ 找不到文件: {INPUT_SRT_PATH}，请确保文件名正确且在同一目录下。")
        exit(1)
        
    # 读取原始文件
    with open(INPUT_SRT_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 解析并提取
    all_blocks = parse_raw_srt(content)
    print(f"📄 原始文件共解析出 {len(all_blocks)} 条字幕。")
    
    # 截取前 100 条
    samples = all_blocks[:SAMPLE_LIMIT]
    
    # 组装为新的 SRT 文本并保存
    sample_text = build_srt_text(samples)
    
    with open(OUTPUT_SAMPLE_PATH, 'w', encoding='utf-8') as f:
        f.write(sample_text)
        
    print(f"✅ 成功提取 {len(samples)} 条样本，已保存至文件: {OUTPUT_SAMPLE_PATH}")