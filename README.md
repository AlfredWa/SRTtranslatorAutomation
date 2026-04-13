# 🎬 自动化字幕翻译与大模型横向评测工作流 (Auto-SRT-Eval)

本项目是一个全自动化的字幕（SRT）翻译与质量评测流水线。它能够调用多个顶尖大语言模型（如 DeepSeek, Qwen, Kimi, GPT-4o 等）对同一份字幕进行并发翻译，并最终由一个“AI 裁判”模型根据严苛的自定义规则对所有翻译结果进行打分和排名。

## 📁 核心文件说明

本项目由 4 个核心 Python 脚本组成，它们各司其职：

1. **`extract.py` (数据准备)**：从原始的大字幕文件中提取出前 100 条（或指定数量）的样本，生成 `sample_100.srt` 供后续测试使用。
2. **`run.py` (并发翻译与归档)**：自动修改 `LinguaGacha` 的配置，依次调起预设的多个大模型进行翻译。翻译完成后，会自动将生成的“双语对照版”和“纯译文版”分别归档到 `Outputs_Bilingual` 和 `Outputs_Translated` 文件夹，并清理临时文件。
3. **`eval.py` (多线程并发评测)**：读取 `Outputs_Bilingual` 文件夹中的所有双语字幕，呼叫 AI 裁判（如 Kimi-K2.5）进行多线程并发打分，并生成包含排行榜的终极 Markdown 报告。
4. **`main.py` (一键主控)**：中枢脚本。按顺序自动执行上述三个脚本，实现真正的“一键端到端”工作流。

---

## 🚀 如何使用 (快速上手)

**前置准备：**
1. 确保您的电脑已安装 Python。
2. 安装必要的第三方库（用于裁判打分）：
   ```bash
   pip install openai
   ```
3. 确保当前目录下有一个完整的 `LinguaGacha` 文件夹，且包含 `LinguaGacha.exe` (或 `app.exe`) 及 `userdata/config.json`。

**一键运行：**
把你要切分的原始字幕准备好，然后在终端运行：
```bash
python main.py
```
喝杯咖啡，等待终端提示完成。所有翻译结果将在 `Outputs_Bilingual` 文件夹中，评测报告为根目录下的 `多模型横向评测报告.md`。

---

## 🛠️ 高级自定义指南

### 1. 如何在 `run.py` 中添加或修改“参赛翻译模型”

打开 `run.py`，找到顶部的 `MODELS_TO_RUN` 列表。您可以按照以下格式随意增删模型：

```python
MODELS_TO_RUN = [
    {
        "name": "deepseek_v3",  # ⚠️ 极其重要：只能用字母、数字和下划线，绝对不能包含斜杠(/)或点号(.)
        "id": "deepseek-ai/DeepSeek-V3", # 平台真实的 Model ID
        "api_key": "sk-xxxxxx", # 你的真实 API Key
        "api_url": "https://api.siliconflow.cn/v1" # 接口地址（支持硅基流动、Vercel Gateway 等）
    }
]
```
* **注意**：如果您使用的是 Vercel AI Gateway 代理 OpenAI 或 Claude，请确保 `api_url` 填写完整的端点路径，并且在 LinguaGacha 软件界面中，您当前激活的预设模型格式（Format）与网关路由相匹配（例如 OpenAI 格式）。

### 2. 如何在 `eval.py` 中修改“AI 裁判模型”

打开 `eval.py`，找到顶部的 **1. 裁判配置区**。修改以下三个变量：

```python
API_KEY = "sk-xxxxxx" # 裁判模型的 API Key
BASE_URL = "https://api.siliconflow.cn/v1" # 裁判模型的接口地址
JUDGE_MODEL = "Pro/moonshotai/Kimi-K2.5" # 裁判模型的真实 ID
```
* **建议**：裁判模型务必选择逻辑推理能力强、指令遵循度高的大模型（如 Kimi-K2.5, DeepSeek-V3, Qwen2.5-72B 或 GPT-4o），否则可能导致 JSON 输出格式损坏或乱打分。

### 3. 如何修改翻译 Prompt (提示词) 与打分规则

#### A. 修改“翻译”阶段的 Prompt 和术语表
本项目的翻译动作是由底层的 `LinguaGacha` 软件执行的。`run.py` 只是负责自动点击“开始翻译”。
* **如何修改**：请直接打开 `LinguaGacha` 软件界面，在您激活的模型预设中，修改“系统提示词（System Prompt）”、添加自定义 prompt 或配置“专属术语表”。`run.py` 运行时会自动继承这些设置。

#### B. 修改“评测”阶段的打分标准与规则
打开 `eval.py`，搜索 `def llm_judge` 函数，找到里面名为 `prompt` 的长字符串：

```python
    prompt = f"""
    你是一个极其冷酷的字幕翻译评测专家。请根据以下【7大硬规则】对翻译结果进行深度审计并打分（满分 10 分）。
    
    【7大评分规则】
    1. 问号硬对齐：只有原文含“？”或以“吗/么”结尾时，英文必须以“?”结尾；否则不得添加“?”。
    2. 逐行翻译：行号顺序必须一致...
    （在此处自由修改、增加或删除你的评分规则）
    ...
    """
```
* **修改技巧**：
    * 如果你发现某个模型总是犯同一种错误，可以直接在这里加一条规则（例如：“8. 严禁将中文的‘少爷’翻译为‘Master’，必须翻译为‘Young Lord’”）。
    * 保持输出要求（`【输出要求】` 及其 JSON 格式指示）不变，否则 Python 会因为无法解析 JSON 而报错。