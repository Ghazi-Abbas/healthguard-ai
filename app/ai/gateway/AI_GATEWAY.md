# HealthGuard AI — AI Gateway

## 1. Purpose

The AI Gateway provides a centralized way to configure, create, and manage language models across HealthGuard AI.

Instead of initializing provider models separately inside agents, the application uses a shared gateway.

The gateway is responsible for:

- Model selection through a central registry.
- Model initialization.
- Provider API-key validation.
- Centralized timeout and retry configuration.
- Fallback model execution.
- Structured-output consistency.
- Logging fallback activation.

## 2. Architecture

The AI Gateway contains three main components:

| Component | File | Responsibility |
|---|---|---|
| Model Registry | `model_registry.py` | Defines primary models and fallback configurations for each AI task. |
| Model Factory | `model_factory.py` | Creates validated Groq and Gemini model instances. |
| Fallback Manager | `fallback_manager.py` | Attaches fallback models to LangChain runnables. |
| Retry Policy | `retry_policy.py` | Identifies errors that should trigger fallback execution. |

### Model execution flow

1. An agent requests a model using `get_chat_model(task_name)`.
2. The factory reads the task configuration from the registry.
3. The factory initializes the configured provider model.
4. The agent builds its prompt or structured-output chain.
5. `add_model_fallbacks()` attaches configured fallback models.
6. If the primary model raises a configured retryable error, LangChain attempts the fallback.
7. Fallback activation is logged.

## 3. Model Registry

File: `app/ai/gateway/model_registry.py`

The registry defines the model configuration for each AI task.

| AI task | Primary provider | Primary setting | Fallback |
|---|---|---|---|
| Supervisor | Groq | `GROQ_MODEL` | `groq_fast` |
| Clinical evidence | Groq | `GROQ_MODEL` | `groq_fast` |
| Criteria/risk | Groq | `GROQ_MODEL` | `groq_fast` |
| Policy criteria extraction | Groq | `GROQ_MODEL` | `groq_fast` |
| Policy answer generation | Groq | `GROQ_MODEL` | `groq_fast` |
| Policy query rewriting | Groq | `GROQ_FAST_MODEL` | Gemini |
| Policy retrieval grading | Groq | `GROQ_FAST_MODEL` | Gemini |
| Policy answer evaluation | Gemini | `GEMINI_EVAL_MODEL` | None |

All registered tasks currently use temperature `0`.

## 4. Model Factory

File: `app/ai/gateway/model_factory.py`

The factory provides two main functions.

### `get_chat_model(task_name)`

Creates the primary model configured for a task.

Example:

```python
model = get_chat_model("clinical_evidence")
```

### `create_model(provider, model_name, temperature)`

Initializes the provider-specific model.

Supported providers:

- Groq — `ChatGroq`
- Gemini — `ChatGoogleGenerativeAI`

The factory validates:

- Model name.
- Provider support.
- Provider API-key configuration.

It also applies centralized timeout and retry settings.

## 5. Configuration

Timeout and retry settings are defined centrally in `app/core/config.py`.

```python
AI_MODEL_TIMEOUT: int = 30
AI_MODEL_MAX_RETRIES: int = 2
```

Provider configuration uses these settings:

| Setting | Purpose |
|---|---|
| `GROQ_API_KEY` | Groq API authentication |
| `GOOGLE_API_KEY` | Gemini API authentication |
| `GROQ_MODEL` | Primary Groq model |
| `GROQ_FAST_MODEL` | Faster Groq model |
| `GEMINI_EVAL_MODEL` | Gemini model used for evaluation and configured Gemini fallbacks |
| `AI_MODEL_TIMEOUT` | Model request timeout |
| `AI_MODEL_MAX_RETRIES` | Provider-level retry limit |

Actual model identifiers are controlled by the application's configuration and environment.

Never commit API keys to source control.

## 6. Retry Policy

File: `app/ai/gateway/retry_policy.py`

The retry policy identifies transient provider errors.

Configured retryable errors include:

- Groq API connection errors.
- Groq API timeout errors.
- Groq rate-limit errors.
- Groq internal server errors.
- Gemini server errors.

Gemini server errors such as HTTP 503 and 504 are retryable.

General Gemini API errors are not automatically retryable.

The purpose is to avoid repeatedly attempting fallback for errors that are unlikely to succeed through another model, such as invalid requests.

## 7. Fallback Management

File: `app/ai/gateway/fallback_manager.py`

The fallback manager provides:

### `get_fallback_models()`

Creates the fallback models configured for a task.

### `add_model_fallbacks()`

Attaches fallback models to the primary runnable.

Example:

```python
chain = add_model_fallbacks(
    primary_chain,
    task_name="clinical_evidence",
)
```

When a configured retryable error occurs, LangChain attempts the fallback model.

Fallback activation is logged with:

- AI task.
- Provider.
- Fallback identifier.

A fallback is not automatically triggered for every exception. Only errors included in `RETRYABLE_ERRORS` are handled by the fallback chain.

## 8. Structured Output

Some agents require structured responses using Pydantic schemas.

The fallback manager supports structured-output configuration so that fallback models use the same schema and options as the primary model.

Example:

```python
chain = add_model_fallbacks(
    structured_chain,
    task_name="criteria_risk",
    schema=CriteriaResult,
    structured_output_kwargs={
        "method": "json_schema",
        "strict": True,
    },
)
```

This helps maintain consistent response structure across configured model fallbacks.

## 9. Agent Integration

The gateway is integrated into these application components:

- `clinical_evidence_agent.py`
- `critaria_risk_agent.py`
- `supervisor_agent.py`
- `policy_rag_agent.py`
- `policy_rag_graph.py`
- `policy_crag_graph.py`

Agents obtain their primary model through `get_chat_model()`.

Tasks configured with fallbacks attach them through `add_model_fallbacks()`.

The policy answer evaluator currently uses Gemini directly and has no fallback configured.

## 10. Logging and Troubleshooting

The gateway logs:

- Configured fallback chains.
- Fallback activation.
- Task and provider information.

Useful troubleshooting checks:

| Problem | Check |
|---|---|
| Missing model name | Verify the model setting in application configuration. |
| Missing API key | Verify provider API-key configuration. |
| Provider timeout | Check provider availability and timeout settings. |
| Fallback not activated | Check whether the exception is included in `RETRYABLE_ERRORS`. |
| Structured-output failure | Verify that primary and fallback schemas and options match. |
| Gemini 503/504 | Check provider availability and inspect fallback logs. |

Do not log API keys, authorization headers, or sensitive healthcare information.

## 11. Adding a New AI Task

To add a new AI task:

1. Add its provider, model setting, temperature, and fallback identifiers to `MODEL_REGISTRY`.
2. Ensure the fallback manager supports each configured fallback identifier.
3. Create the primary model using `get_chat_model("your_task")`.
4. Attach fallback models using `add_model_fallbacks()` where required.
5. Add tests for model selection, fallback behavior, and structured output if applicable.
6. Run the complete regression suite.

## 12. Verification

The gateway's automated regression suite currently reports:

- 28 tests passed.
- 0 tests failed.
- 27 warnings.
- Execution time: 23.07 seconds.

Tests cover model factory validation, retry classification, fallback execution, fallback logging, authorization workflows, checkpointing, and related application behavior.

The passing suite confirms the tested behavior; it does not by itself establish production readiness or guarantee live provider availability.

---

**Status:** AI Gateway implementation and automated regression verification completed. Final production readiness remains dependent on security, reliability, integration, and deployment validation.
