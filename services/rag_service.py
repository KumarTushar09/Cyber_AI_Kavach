from rag.context_builder import build_context
from rag.retriever import retrieve
from services.llm_service import generate_completion


def _extract_answer(llm_response: dict) -> str:
    data = llm_response.get("data", {}) if isinstance(llm_response, dict) else {}
    if isinstance(data, dict):
        candidates = [
            data.get("answer"),
            data.get("response"),
            (data.get("data") or {}).get("answer") if isinstance(data.get("data"), dict) else None,
            data.get("message"),
        ]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return ""


async def query_rag(question: str) -> dict:
    chunks = await retrieve(question)
    context = build_context(chunks)

    prompt = (
        "You are a cyber security knowledge assistant. "
        "Use only the retrieved context to answer. "
        "If context is insufficient, say what is missing.\n\n"
        f"Question: {question}\n\n"
        f"Retrieved context:\n{context}\n\n"
        "Return a concise answer with practical guidance."
    )

    llm = await generate_completion(prompt, prompt_type="knowledge_query")

    answer = "Knowledge base is currently limited; showing retrieved context."
    if llm.get("status") == "ok":
        extracted = _extract_answer(llm)
        if extracted:
            answer = extracted

    return {
        "question": question,
        "context_chunks": chunks,
        "context": context,
        "answer": answer,
        "llm": llm,
    }
