MODEL_REGISTRY = {
    "supervisor": {
        "provider": "groq",
        "model_setting": "GROQ_MODEL",
        "temperature": 0,
        "fallbacks": ["groq_fast", ],
    },
    "clinical_evidence": {
        "provider": "groq",
        "model_setting": "GROQ_MODEL",
        "temperature": 0,
        "fallbacks": [ ],
    },
    "criteria_risk": {
        "provider": "groq",
        "model_setting": "GROQ_MODEL",
        "temperature": 0,
        "fallbacks": [ ],
    },
    "policy_criteria_extraction": {
        "provider": "groq",
        "model_setting": "GROQ_MODEL",
        "temperature": 0,
        "fallbacks": ["groq_fast", ],
    },
    "policy_answer_generation": {
        "provider": "groq",
        "model_setting": "GROQ_MODEL",
        "temperature": 0,
        "fallbacks": ["groq_fast", ],
    },
    "policy_query_rewriting": {
        "provider": "groq",
        "model_setting": "GROQ_FAST_MODEL",
        "temperature": 0,
        "fallbacks": ["gemini"],
    },
    "policy_retrieval_grading": {
        "provider": "groq",
        "model_setting": "GROQ_FAST_MODEL",
        "temperature": 0,
        "fallbacks": ["gemini"],
    },
    "policy_answer_evaluation": {
        "provider": "gemini",
        "model_setting": "GEMINI_EVAL_MODEL",
        "temperature": 0,
        "fallbacks": [],
    },
}
