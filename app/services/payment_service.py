import httpx
import base64
from app.core.config import settings
from app.models.user import UserPublic

async def create_midtrans_snap_transaction(
    contribution_id: str, 
    amount: float, 
    user: UserPublic
) -> dict:
    if not settings.MIDTRANS_SERVER_KEY:
        raise Exception("Midtrans Server Key tidak dikonfigurasi.")

    api_url = "https://app.sandbox.midtrans.com/snap/v1/transactions"
    
    auth_string = base64.b64encode(f"{settings.MIDTRANS_SERVER_KEY}:".encode()).decode()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_string}",
    }
    
    payload = {
        "transaction_details": {
            "order_id": contribution_id,
            "gross_amount": round(amount),
        },
        "customer_details": {
            "first_name": user.name.split(" ")[0],
            "email": user.email,
            "phone": user.phone or "N/A",
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(api_url, json=payload, headers=headers)
        
        if response.status_code != 201:
            print(f"Midtrans Error: {response.text}")
            raise Exception(f"Gagal membuat transaksi Midtrans: {response.text}")
            
        response_data = response.json()
        if "token" not in response_data:
            raise Exception("Midtrans tidak mengembalikan token transaksi.")
            
        return {
            "token": response_data["token"],
            "redirect_url": response_data["redirect_url"]
        }