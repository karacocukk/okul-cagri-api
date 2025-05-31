import logging # Loglama için eklendi
from typing import Dict, List, Tuple
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Her sınıf adı için aktif bağlantıları (WebSocket objeleri) tutar
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, sinif_adi: str, websocket: WebSocket):
        await websocket.accept()
        if sinif_adi not in self.active_connections:
            self.active_connections[sinif_adi] = []
        self.active_connections[sinif_adi].append(websocket)
        logger.info(f"WebSocket connected for class: {sinif_adi}, client: {websocket.client}") # print yerine logger.info

    def disconnect(self, sinif_adi: str, websocket: WebSocket):
        if sinif_adi in self.active_connections:
            if websocket in self.active_connections[sinif_adi]:
                self.active_connections[sinif_adi].remove(websocket)
                logger.info(f"WebSocket disconnected for class: {sinif_adi}, client: {websocket.client}") # print yerine logger.info
                if not self.active_connections[sinif_adi]: # Sınıfta başka bağlantı kalmadıysa
                    del self.active_connections[sinif_adi]
                    logger.info(f"No active connections left for class: {sinif_adi}, removing from manager.") # print yerine logger.info
            else:
                logger.warning(f"WebSocket client {websocket.client} not found in class {sinif_adi} during disconnect.")
        else:
            logger.warning(f"Class {sinif_adi} not found in active connections during disconnect for client {websocket.client}.")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            # Bağlantı zaten kapalıysa veya başka bir hata oluşursa
            # Bu durumda disconnect çağrılmış olmalı, burada sadece loglayabiliriz.
            logger.error(f"Error sending personal message to {websocket.client}: {e}", exc_info=False) # Basit hata logu

    async def broadcast_to_class(self, sinif_adi: str, message: str, exclude_self: WebSocket = None):
        if sinif_adi in self.active_connections:
            active_sockets_in_class = list(self.active_connections[sinif_adi]) # Kopya üzerinde iterasyon
            if not active_sockets_in_class:
                logger.info(f"No active connections for class: {sinif_adi} to broadcast message.") # print yerine logger.info
                return
            for connection in active_sockets_in_class:
                if connection != exclude_self:
                    try:
                        await connection.send_text(message)
                    except Exception as e: # WebSocketException veya RuntimeError olabilir
                        logger.error(f"Error broadcasting message to {connection.client} for class {sinif_adi}: {e}. Removing problematic connection.", exc_info=False)
                        # Sorunlu bağlantıyı kaldır (disconnect içinde zaten loglama var)
                        # Bu, disconnect'in tekrar çağrılmasına neden olabilir, bu yüzden dikkatli olunmalı
                        # veya sadece loglayıp bırakılabilir.
                        # self.disconnect(sinif_adi, connection) # Bu döngüyü bozabilir, dikkat!
        else:
            logger.warning(f"Class {sinif_adi} not found for broadcasting message.")

# Global bir manager instance oluşturuyoruz, bu tüm uygulama tarafından kullanılacak.
manager = ConnectionManager() 