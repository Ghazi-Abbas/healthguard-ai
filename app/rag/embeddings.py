from functools import lru_cache

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings

from app.rag.constants import EMBEDDING_MODEL , EMBIDDING_DIMENSION

# Least Recently Used. decorator who rember the last result and store it
@lru_cache(maxsize=1)
def get_embidding_service()->GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=settings.GOOGLE_API_KEY,
        output_dimensionality=EMBIDDING_DIMENSION

    )
