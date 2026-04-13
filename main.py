import subprocess
import sys
import time
from datetime import timedelta

def run_script(script_name):
    """运行子脚本并监控其执行状态"""
    print(f"\n{'='*20} 正在执行: {script_name} {'='*20}")
    start_time = time.time()
    
    try:
        # 使用 sys.executable 确保使用当前环境的 Python 解释器
        result = subprocess.run([sys.executable, script_name], check=True)
        
        end_time = time.time()
        duration = str(timedelta(seconds=int(end_time - start_time)))
        print(f"✅ {script_name} 执行成功！耗时: {duration}")
        return True
        
    except subprocess.CalledProcessError:
        print(f"❌ {script_name} 执行失败，流程已终止。")
        return False
    except FileNotFoundError:
        print(f"❌ 找不到文件: {script_name}，请检查文件名是否正确。")
        return False

def main():
    total_start = time.time()
    
    # 定义执行顺序
    pipeline = ["extract.py", "run.py", "eval.py"]
    
    print("🚀 开始一键全自动翻译评测流程...")
    
    for script in pipeline:
        if not run_script(script):
            sys.exit(1) # 如果某个环节失败，退出整个主程序
            
    total_end = time.time()
    total_duration = str(timedelta(seconds=int(total_end - total_start)))
    
    print("\n" + "#"*50)
    print(f"🎉 所有任务已圆满完成！")
    print(f"⏰ 总运行耗时: {total_duration}")
    print(f"📄 最终报告请查看: evaluation_report.md")
    print("#"*50)

if __name__ == "__main__":
    main()