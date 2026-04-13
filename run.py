import os
import json
import subprocess
import shutil
import time

# ================= 1. 模型与中转接口配置区 =================
MODELS_TO_RUN = [
    # --- 硅基流动模型阵营 (直接能跑) ---
    {
        "name": "kimi2_5", 
        "id": "Pro/moonshotai/Kimi-K2.5", 
        "api_key": "#",
        "api_url": "https://api.siliconflow.cn/v1"
    },
    {
        "name": "deepseek_v3", 
        "id": "deepseek-ai/DeepSeek-V3", 
        "api_key": "#",
        "api_url": "https://api.siliconflow.cn/v1"
    },
    {
        "name": "qwen2_5_72b", 
        "id": "Qwen/Qwen2.5-72B-Instruct", 
        "api_key": "#",
        "api_url": "https://api.siliconflow.cn/v1"
    },
    
    # --- Vercel AI Gateway 阵营 (填写真实信息后能跑) ---
    {
        "name": "gpt4o_vercel", 
        "id": "gpt-4o", 
        "api_key": "#",
        "api_url": "https://ai-gateway.vercel.sh/v1"
    },
    {
        "name": "gemini_3_flash", 
        "id": "gemini-3-flash", 
        "api_key": "#",
        "api_url": "https://ai-gateway.vercel.sh/v1"
    }
]

SRT_FILENAME = "sample_100.srt"
# ==========================================================

# --- 全自动路径推导 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FILE = os.path.join(CURRENT_DIR, SRT_FILENAME)
LG_ROOT_DIR = os.path.join(CURRENT_DIR, "LinguaGacha")
LG_EXE_PATH = os.path.join(LG_ROOT_DIR, "LinguaGacha.exe")
LG_CONFIG_PATH = os.path.join(LG_ROOT_DIR, "userdata", "config.json")

FINAL_BILINGUAL_DIR = os.path.join(CURRENT_DIR, "Outputs_Bilingual")
FINAL_TRANSLATED_DIR = os.path.join(CURRENT_DIR, "Outputs_Translated")

def init_env():
    os.makedirs(FINAL_BILINGUAL_DIR, exist_ok=True)
    os.makedirs(FINAL_TRANSLATED_DIR, exist_ok=True)
    print("📂 双语版与纯译文归档目录已就绪。")

def update_config(model_id, api_key, api_url=None):
    if not os.path.exists(LG_CONFIG_PATH): 
        return False
        
    with open(LG_CONFIG_PATH, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    active_id = config_data.get("activate_model_id")
    for m in config_data.get("models", []):
        if m.get("id") == active_id:
            m["model_id"] = model_id
            m["api_key"] = api_key
            if api_url:
                m["api_url"] = api_url
            break
            
    with open(LG_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=4)
    return True

def archive_and_cleanup(model_name):
    project_name = f"Task_{model_name}"
    raw_bilingual_dir = os.path.join(LG_ROOT_DIR, f"{project_name}_译文_双语对照")
    raw_translated_dir = os.path.join(LG_ROOT_DIR, f"{project_name}_译文")
    
    # --- 1. 归档双语对照版 ---
    bi_patterns = [SRT_FILENAME.replace(".srt", ".zh.en.srt"), SRT_FILENAME]
    bi_moved = False
    for p in bi_patterns:
        old_path = os.path.join(raw_bilingual_dir, p)
        if os.path.exists(old_path):
            new_name = SRT_FILENAME.replace(".srt", f".{model_name}.zh.en.srt")
            shutil.move(old_path, os.path.join(FINAL_BILINGUAL_DIR, new_name))
            print(f"✅ 双语版归档完成: {new_name}")
            bi_moved = True
            break
    if not bi_moved: 
        print(f"⚠️ 警告: 未能找到双语结果文件。")

    # --- 2. 归档纯译文版 ---
    trans_patterns = [SRT_FILENAME, SRT_FILENAME.replace(".srt", ".en.srt")]
    trans_moved = False
    for p in trans_patterns:
        old_path = os.path.join(raw_translated_dir, p)
        if os.path.exists(old_path):
            new_name = SRT_FILENAME.replace(".srt", f".{model_name}.srt")
            shutil.move(old_path, os.path.join(FINAL_TRANSLATED_DIR, new_name))
            print(f"✅ 纯译文归档完成: {new_name}")
            trans_moved = True
            break
    if not trans_moved: 
        print(f"⚠️ 警告: 未能找到纯译文结果文件。")

    # --- 3. 彻底清理战场 ---
    shutil.rmtree(raw_bilingual_dir, ignore_errors=True)
    shutil.rmtree(raw_translated_dir, ignore_errors=True)
    
    for ext in ["", ".lg"]:
        proj_file = os.path.join(LG_ROOT_DIR, project_name + ext)
        if os.path.exists(proj_file):
            if os.path.isdir(proj_file): shutil.rmtree(proj_file)
            else: os.remove(proj_file)
    print(f"🧹 {model_name} 的临时现场已无痕清理。")

def run_one_model(model_info):
    name = model_info["name"]
    project_name = f"Task_{name}"
    print(f"\n{'-'*15} 🚀 正在调起模型: {name} {'-'*15}")
    
    target_api_url = model_info.get("api_url")
    
    if not update_config(model_info["id"], model_info["api_key"], target_api_url):
        print(f"❌ 无法更新 {name} 的配置。")
        return
        
    exe = LG_EXE_PATH if os.path.exists(LG_EXE_PATH) else os.path.join(LG_ROOT_DIR, "app.exe")
    cli_cmd = [
        exe, "--cli", "--task", "translation", 
        "--project", project_name, "--create", "--input", SOURCE_FILE
    ]
    
    try:
        subprocess.run(cli_cmd, cwd=LG_ROOT_DIR, check=True)
        archive_and_cleanup(name)
    except Exception as e:
        print(f"❌ {name} 任务执行中发生错误: {e}")

if __name__ == "__main__":
    if not MODELS_TO_RUN:
        print("⚠️ 模型列表为空！请先在脚本顶部的 MODELS_TO_RUN 列表中配置你的模型。")
        exit(1)
        
    init_env()
    for model in MODELS_TO_RUN:
        run_one_model(model)
        time.sleep(2)
        
    print("\n" + "="*50)
    print("✨ 所有任务处理完毕！")
    print(f"📂 双语对照版已存放于：{FINAL_BILINGUAL_DIR}")
    print(f"📂 纯英文版已存放于：{FINAL_TRANSLATED_DIR}")
    print("="*50)