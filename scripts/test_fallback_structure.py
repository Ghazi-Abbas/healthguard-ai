
import httpx

from groq import APITimeoutError
from langchain_core.runnables import RunnableLambda

from app.schemas.clinical_evidence import ClinicalEvidenceResult


# Create a simulated timeout error
def simulate_primary_failure(data):
    request = httpx.Request(
        "POST",
        "https://api.groq.com/test"
    )

    raise APITimeoutError(request=request)


# Primary model simulation
primary = RunnableLambda(simulate_primary_failure)


# Fallback model simulation
fallback = RunnableLambda(
    lambda data: ClinicalEvidenceResult(
        finding=[],
        overall_missing_information=[]
    )
)


# Attach fallback
chain = primary.with_fallbacks(
    [fallback],
    exceptions_to_handle=(APITimeoutError,),
)


# Execute
result = chain.invoke({"test": "clinical evidence"})


print("Result type:", type(result).__name__)
print("Is Pydantic:", isinstance(result, ClinicalEvidenceResult))
print("Result:", result)
