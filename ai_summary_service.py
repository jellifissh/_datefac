import json

import requests


def _clean_and_parse_json(raw_response):
    clean_text = raw_response or ""
    if "</think>" in clean_text:
        clean_text = clean_text.split("</think>")[-1]
    start = clean_text.find("{")
    end = clean_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    try:
        return json.loads(clean_text[start : end + 1])
    except Exception:
        return {}


def _build_prompt(ai_context):
    return (
        "你是一位资深投研分析师。请基于研报片段提取定性结论与关键预测，"
        "并只输出 JSON。\n"
        "要求：\n"
        "1. 提取【投资评级】、【核心逻辑】（不少于50字）、【目标价】。\n"
        "2. 提取所有预测年份的核心财务指标（净利润、营收、ROE、PE）。\n"
        "3. 动态生成键名，例如“2027E_净利润”。\n"
        f"研报片段：\n{ai_context}"
    )


def generate_investment_summary(full_text, doc_name, config, logger):
    ai_context = (full_text or "")[:5000] + "\n\n[...]\n\n" + (full_text or "")[-5000:]
    prompt = _build_prompt(ai_context)
    try:
        res = requests.post(
            config["ollama"]["url"],
            json={
                "model": config["ollama"]["model"],
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=config["ollama"].get("timeout"),
        )
        if res.status_code != 200:
            logger.warning("AI 请求失败: doc=%s, status_code=%s", doc_name, res.status_code)
            return {"状态": f"AI请求失败: status_code={res.status_code}"}

        ai_data = _clean_and_parse_json(res.json().get("response", "{}"))
        if not ai_data:
            logger.warning("AI 请求成功但未解析出有效 JSON: doc=%s", doc_name)
            return {"状态": "AI返回为空或非JSON"}

        logger.info("AI 请求成功: doc=%s, parsed_keys=%s", doc_name, list(ai_data.keys()))
        return ai_data
    except Exception as exc:
        logger.exception("AI 请求异常: doc=%s", doc_name)
        return {"状态": f"API异常: {str(exc)}"}
