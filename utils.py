import json
import re
from typing import Dict, List, Any, Optional
import ollama

# ---- helpers ---------------------------------------------------------------

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)

def _extract_json(text: str) -> Optional[dict]:
    """
    Tries to parse JSON. If the model wrapped JSON with prose,
    extracts the first {...} block.
    """
    try:
        return json.loads(text)
    except Exception:
        m = _JSON_BLOCK_RE.search(text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


def _ollama_json_call(prompt, model="phi3:mini", temperature=0.1):
    try:
        resp = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": temperature},
            stream=False,
            timeout=30
        )
        raw_output = resp["message"]["content"]

        # Try parsing JSON
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            match = _JSON_BLOCK_RE.search(raw_output)
            if match:
                return json.loads(match.group(0))
            else:
                return {
                    "score": 0,
                    "matched_skills": [],
                    "missing_skills": [],
                    "error": "Invalid JSON"
                }
    except Exception as e:
        return {
            "score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "error": str(e)
        }


# ---- public API ------------------------------------------------------------

def match_skills(resume_text: str, job_desc: str, model: str = "phi3:mini") -> Dict[str, Any]:
    """
    Uses LLM (Ollama) to produce a 0-100 score + matched/missing skills.
    """
    prompt = f"""
You are an AI resume analyzer. Compare the RESUME with the JOB DESCRIPTION.

RESUME:
\"\"\"{resume_text}\"\"\"

JOB DESCRIPTION:
\"\"\"{job_desc}\"\"\"

Return ONLY valid JSON with this exact schema:
{{
  "score": <int 0-100>,
  "matched_skills": [<string>],
  "missing_skills": [<string>]
}}
- "score" must be an integer (0-100).
- "matched_skills" and "missing_skills" should be concise keywords/phrases (lowercase).
    """.strip()

    data = _ollama_json_call(prompt, model=model, temperature=0.1)

    # normalize & safeguards
    score = data.get("score")
    if not isinstance(score, int):
        try:
            score = int(float(score))
        except Exception:
            score = 0
    score = max(0, min(100, score))

    matched = data.get("matched_skills") or []
    missing = data.get("missing_skills") or []
    if not isinstance(matched, list): matched = [str(matched)]
    if not isinstance(missing, list): missing = [str(missing)]

    return {
        "score": score,
        "matched_skills": [str(s).strip().lower() for s in matched if str(s).strip()],
        "missing_skills": [str(s).strip().lower() for s in missing if str(s).strip()],
        "raw": data
    }


def generate_suggestions(resume_text: str, job_desc: str, purpose: str, model: str = "phi3:mini") -> List[str]:
    """
    Uses LLM (Ollama) to generate 5 actionable suggestions.
    Returns a list of bullet strings.
    """
    prompt = f"""
You are an expert resume coach. Based on the RESUME and JOB DESCRIPTION,
write 5 specific, actionable bullet-point suggestions to improve the resume
for a "{purpose}" application. Keep each suggestion under 20 words. Avoid fluff.

RESUME:
\"\"\"{resume_text}\"\"\"

JOB DESCRIPTION:
\"\"\"{job_desc}\"\"\"

Return ONLY a JSON array of strings, e.g.:
["rewrite summary to include role and years", "quantify outcomes in projects", ...]
    """.strip()

    data = _ollama_json_call(prompt, model=model, temperature=0.3)

    # data should be a list; if dict came back, try common keys
    suggestions = []
    if isinstance(data, list):
        suggestions = data
    elif isinstance(data, dict):
        for k in ("suggestions", "bullets", "items"):
            if isinstance(data.get(k), list):
                suggestions = data[k]
                break

    if not suggestions:
        suggestions = [
            "Tailor summary to target role with key skills.",
            "Add measurable outcomes in experience bullets.",
            "Mirror top JD keywords in skills section.",
            "Re-order sections to highlight relevant projects.",
            "Ensure ATS-friendly formatting and consistent tense."
        ]

    return [str(s).strip("-• ").strip() for s in suggestions if str(s).strip()]
