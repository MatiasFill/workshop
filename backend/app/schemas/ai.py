from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=8000)
    use_rag: bool = True
    memory_first: bool = True
    context: str = ""

class AskResponse(BaseModel):
    answer: str
    source: str
    provider: str
    chunks_used: int = 0

class MemoryCreate(BaseModel):
    question: str
    answer: str
    context: str = ""
