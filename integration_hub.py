from fastapi import FastAPI, Request, HTTPException, Form
from pydantic import BaseModel
from supabase import create_client
import os

# Inizializza Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="CashFlowBoost Integration Hub")

class InvoiceEvent(BaseModel):
    invoice_id: str
    status: str
    amount: float
    client_id: str

@app.post("/webhook/invoice")
async def invoice_webhook(event: InvoiceEvent, request: Request):
    try:
        # Sincronizza su Supabase
        data = {
            "id": event.invoice_id,
            "client_id": event.client_id,
            "amount": event.amount,
            "status": event.status,
            "paid_date": None if event.status == "Unpaid" else event.paid_date
        }
        resp = supabase.table("invoices").upsert(data).execute()
        # Notifica Zapier
        await call_zapier(event)
        return {"status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/subscribe")
async def subscribe(email: str = Form(...)):
    try:
        # Inserisci in Supabase
        supabase.table("subscribers").insert({"email": email}).execute()
        # Notifica Zapier
        await call_zapier({"email": email})
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def call_zapier(payload: dict):
    import httpx
    webhook = os.getenv("ZAPIER_WEBHOOK_URL")
    async with httpx.AsyncClient() as client:
        r = await client.post(webhook, json=payload)
        r.raise_for_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 