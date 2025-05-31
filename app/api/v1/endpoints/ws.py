from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from typing import List, Optional
import logging # Loglama için eklendi

from app.core.connection_manager import manager
# from app.schemas.schemas import Cagri # Kullanılmadığı için kaldırıldı
import json
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

async def validate_classroom_token(websocket: WebSocket, token: Optional[str] = Query(None)) -> str:
    if not token or token != settings.CLASSROOM_PC_TOKEN:
        logger.warning(f"WebSocket connection denied for {websocket.client} in validate_classroom_token: Invalid or missing token. Provided: '{token}'") # print yerine logger.warning
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        # raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token") # Bu satır burada olmamalı, close yeterli.
        return None # Bağlantı kapatıldığı için None dönmek daha uygun.
    return token # Token geçerliyse döndür, ama bu fonksiyon token'ı değil sınıf adını doğrulamalı idealde.
                 # Şimdilik token doğrulaması olarak kalabilir, sınıf adı bilgisi WS URL'sinden gelmeli.

@router.websocket("/ws/{sinif_adi}")
async def websocket_endpoint(websocket: WebSocket, sinif_adi: str, token: str = Depends(validate_classroom_token)):
    if not token: # validate_classroom_token None dönerse bağlantı zaten kapatılmış olur.
        return # Fonksiyondan çık

    await manager.connect(sinif_adi, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Message received from {sinif_adi} - {websocket.client}: {data}") # print yerine logger.debug
            # Gelen mesajı işle veya diğer istemcilere yayınla (örnek)
            # await manager.broadcast_to_class(sinif_adi, f"Mesaj ({sinif_adi}): {data}", exclude_self=websocket)
    except WebSocketDisconnect:
        manager.disconnect(sinif_adi, websocket)
        logger.info(f"Client {websocket.client} disconnected from class {sinif_adi}") # print yerine logger.info
    except Exception as e:
        logger.error(f"Error in WebSocket for class {sinif_adi}, client {websocket.client}: {e}", exc_info=True) # print yerine logger.error
        manager.disconnect(sinif_adi, websocket) # Hata durumunda da disconnect çağır
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except RuntimeError: # Already closed
            pass # Girinti hatasını düzeltmek için pass eklendi 