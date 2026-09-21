import os
from openai import OpenAI

SYSTEM = """
你是AI知识复用助手。

你的任务不是回答用户问题，而是解释：
1. 检索片段中哪些信息与用户记忆/问题产生关联；
2. 这种关联是直接匹配、主题相近，还是仅提供背景参考；
3. 如果证据不足，明确告诉用户“目前无法判断”。

要求：
- 只能基于提供的检索片段分析；
- 不要编造原文不存在的观点；
- 不要为了证明相关而强行建立联系；
- 输出简洁、帮助用户判断是否继续使用该片段。
"""

def explain(query, context):
    key=os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("未检测到 DEEPSEEK_API_KEY")
    client=OpenAI(api_key=key, base_url="https://api.deepseek.com")
    r=client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role":"system","content":SYSTEM},
            {"role":"user","content":f"""
用户想找回的记忆：
{query}

检索到的原文片段：
{context}

请判断二者关系。
"""}
        ],
        temperature=0.2
    )
    return r.choices[0].message.content
