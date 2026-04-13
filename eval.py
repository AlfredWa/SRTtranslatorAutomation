import os
import re
import json
import glob
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    from openai import OpenAI
except ImportError:
    print("缺少 openai 库，请运行: pip install openai")
    exit(1)

# ================= 1. 裁判配置区 =================
# 唯一的铁面裁判：Kimi-K2.5
API_KEY = "sk-oaudxmuupeqnaevevnghuqllbsudfxvxetzzolukbjrzqtgu" 
BASE_URL = "https://api.siliconflow.cn/v1" 
JUDGE_MODEL = "Pro/moonshotai/Kimi-K2.5"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BILINGUAL_FOLDER = os.path.join(CURRENT_DIR, "Outputs_Bilingual")
REPORT_FILE = os.path.join(CURRENT_DIR, "多模型横向评测报告.md")
# ===================================================

def parse_bilingual_srt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    blocks = content.strip().split('\n\n')
    parsed_data = []
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 4:
            parsed_data.append({
                "index": lines[0].strip(),
                "timecode": lines[1].strip(),
                "zh": lines[2].strip(),
                "en": " ".join(lines[3:]).strip() 
            })
    return parsed_data

def llm_judge(parsed_data, filename):
    """大模型打分核心逻辑 (线程内运行)"""
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    eval_text = ""
    for item in parsed_data[:100]: 
        eval_text += f"[{item['index']}] {item['timecode']}\n原文: {item['zh']}\n译文: {item['en']}\n\n"

    prompt = f"""
    你是一个极其冷酷的字幕翻译评测专家。请根据以下【7大硬规则】对翻译结果进行深度审计并打分（满分 10 分）。
    
    【7大评分规则】
    1. 问号硬对齐：只有原文含“？”或以“吗/么”结尾时，英文必须以“?”结尾；否则不得添加“?”。
    2. 逐行翻译：行号顺序必须一致，禁止增删合并行，禁止输出解释。
    3. 格式原样保留：时间轴、序号、英文代码等必须字符级原样保留。
    4. 完整且不加戏：全部翻译（含拟声词、语气词、官职等）；不得遗漏或新增信息。
    5. 准确性第一：不得改变主谓宾、否定/肯定等；严禁过度意译。
    6. 全片一致：同一专名/官职/术语同译；禁止同物多译。
    7. 语气与语域一致：保持古装年代与身份体系，不用现代梗。

    【待测数据】
    {eval_text}

    【输出要求】
    必须直接输出 JSON 格式（包含 score, overall_comment, deductions: [{{index, rule, reason}}]）。不要包含 Markdown 标记。
    """
    
    try:
        response = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1 
        )
        raw_res = response.choices[0].message.content.strip().strip('`').removeprefix('json').strip()
        result = json.loads(raw_res)
        return {"filename": filename, "result": result, "status": "success"}
    except Exception as e:
        return {"filename": filename, "result": {"score": 0, "overall_comment": f"打分失败: {e}", "deductions": []}, "status": "error"}

def process_single_file(file_path):
    """给单线程包装一层，方便传参"""
    filename = os.path.basename(file_path)
    print(f"▶ 裁判已接过卷子，正在批改: {filename} ...")
    parsed_data = parse_bilingual_srt(file_path)
    if parsed_data:
        return llm_judge(parsed_data, filename)
    return None

def generate_master_report(all_results):
    print(f"\n▶ 正在生成终极对比报告: {REPORT_FILE}")
    all_results.sort(key=lambda x: x['result'].get('score', 0), reverse=True)
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("# 🏆 多模型翻译质量横向评测报告\n\n")
        f.write(f"- **测评时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **裁判模型**: `{JUDGE_MODEL}`\n\n")
        
        f.write("## 🥇 综合得分排行榜\n\n")
        f.write("| 排名 | 模型 / 文件名 | 综合得分 | 裁判核心评价 |\n")
        f.write("| :---: | :--- | :---: | :--- |\n")
        
        for idx, item in enumerate(all_results):
            score = item['result'].get('score', 0)
            medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else str(idx+1)
            f.write(f"| {medal} | `{item['filename']}` | **{score}/10** | {item['result'].get('overall_comment', '')} |\n")
        
        f.write("\n---\n\n## 📉 详细扣分审计明细\n\n")
        
        for item in all_results:
            f.write(f"### 📄 选手: `{item['filename']}` (得分: {item['result'].get('score', 0)})\n")
            deductions = item['result'].get('deductions', [])
            
            if not deductions:
                f.write("> ✅ **表现完美！** 裁判未发现任何违反 7 大准则的情况。\n\n")
            else:
                f.write("| 违规句序号 | 违反规则 | 裁判抓取证据与扣分原因 |\n")
                f.write("| :---: | :--- | :--- |\n")
                for ded in deductions:
                    f.write(f"| {ded.get('index')} | {ded.get('rule')} | {ded.get('reason')} |\n")
            f.write("\n")
    print(f"✅ 报告已就绪！")

if __name__ == "__main__":
    srt_files = glob.glob(os.path.join(BILINGUAL_FOLDER, "*.srt"))
    if not srt_files:
        print(f"❌ {BILINGUAL_FOLDER} 中没有找到任何文件！")
        exit(1)
        
    print(f"🔍 扫描到 {len(srt_files)} 份考生卷子，裁判“影分身”并发阅卷中...\n" + "="*50)
    
    all_evaluation_results = []
    
    # 💥 核心：启动多线程并发打分 (max_workers=5 表示最多同时批改 5 份卷子)
    with ThreadPoolExecutor(max_workers=5) as executor:
        # 将所有文件扔进线程池
        futures = {executor.submit(process_single_file, fp): fp for fp in srt_files}
        
        # 只要有一份卷子改完，就立刻收集成绩
        for future in as_completed(futures):
            res = future.result()
            if res:
                all_evaluation_results.append(res)
                score = res['result'].get('score')
                print(f"  └─ 批改完成！[{res['filename']}] 得分: {score}/10")
            
    print("="*50)
    if all_evaluation_results:
        generate_master_report(all_evaluation_results)