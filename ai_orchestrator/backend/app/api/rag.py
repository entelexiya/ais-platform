from fastapi import APIRouter
from pydantic import BaseModel
from app.ai.rag_service import check_compliance, translate_to_checklist

router = APIRouter()

class ComplianceQuery(BaseModel):
    query: str

class OrderPayload(BaseModel):
    order_text: str

@router.post("/query")
async def rag_query(payload: ComplianceQuery):
    """ Эндпоинт для проверки ситуации на соответствие приказам """
    result = check_compliance(payload.query)
    return result

@router.post("/checklist")
async def rag_checklist(payload: OrderPayload):
    """ Эндпоинт для преобразования приказа в чек-лист """
    checklist = translate_to_checklist(payload.order_text)
    return {"checklist": checklist}
