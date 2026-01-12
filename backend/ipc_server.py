"""
IPC Server untuk komunikasi WebSocket antara Python backend dan React frontend.
"""

import asyncio
import json
import logging
from typing import Optional, Set
import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)


class IPCServer:
    """
    WebSocket server untuk komunikasi real-time dengan UI.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8012):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server: Optional[websockets.WebSocketServer] = None
        self.running = False
        
    async def start(self):
        """Start WebSocket server"""
        try:
            self.server = await websockets.serve(
                self._handler,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10
            )
            self.running = True
            logger.info(f"🚀 IPC Server started on ws://{self.host}:{self.port}")
        except Exception as e:
            logger.error(f"❌ Failed to start IPC server: {e}")
            raise
        
    async def _handler(self, websocket: WebSocketServerProtocol):
        """Handle new WebSocket connection"""
        self.clients.add(websocket)
        remote = websocket.remote_address if hasattr(websocket, 'remote_address') else 'Unknown'
        logger.info(f"✅ New client connected: {remote}")
        
        try:
            async for message in websocket:
                try:
                    await self._handle_message(websocket, message)
                except Exception as e:
                    logger.error(f"❌ Error handling message: {e}")
        except websockets.ConnectionClosed as e:
            logger.info(f"🔌 Client disconnected: {remote} (code: {e.code})")
        except Exception as e:
            logger.error(f"❌ Unexpected error in handler: {e}")
        finally:
            if websocket in self.clients:
                self.clients.remove(websocket)
            
    async def _handle_message(self, websocket: WebSocketServerProtocol, raw_message: str):
        """Process incoming message from client"""
        try:
            message = json.loads(raw_message)
            msg_type = message.get("type")
            data = message.get("data", {})
            
            logger.debug(f"📥 Received: {msg_type} from {websocket.remote_address}")
            
            # Handle different message types
            if msg_type == "user_action":
                await self._handle_user_action(data)
            elif msg_type == "ping":
                await self.send_to_client(websocket, "pong", {})
            else:
                logger.warning(f"⚠️ Unknown message type: {msg_type}")
                
        except json.JSONDecodeError:
            logger.error(f"❌ Invalid JSON: {raw_message}")
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
            
    async def _handle_user_action(self, data: dict):
        """Handle user action from UI (Ya/Nanti/Dismiss)"""
        action = data.get("action")
        intent_id = data.get("intent_id")
        
        logger.info(f"👤 User action: {action} for intent {intent_id}")
        
        # TODO: Notify orchestrator about user action
        # For now, just log it
        
    async def send_to_client(self, websocket: WebSocketServerProtocol, msg_type: str, data: dict):
        """Send message to specific client"""
        try:
            message = json.dumps({
                "type": msg_type,
                "data": data
            })
            await websocket.send(message)
            logger.debug(f"📤 Sent: {msg_type} to {websocket.remote_address}")
        except Exception as e:
            logger.error(f"❌ Failed to send to client: {e}")
            
    async def broadcast(self, msg_type: str, data: dict):
        """Broadcast message to all connected clients"""
        if not self.clients:
            logger.warning("⚠️ No clients connected, cannot broadcast")
            return
            
        message = json.dumps({
            "type": msg_type,
            "data": data
        })
        
        # Send to all clients concurrently
        await asyncio.gather(
            *[client.send(message) for client in self.clients],
            return_exceptions=True
        )
        logger.debug(f"📡 Broadcasted: {msg_type} to {len(self.clients)} clients")
        
    async def send_ui_update(self, ui_output: dict):
        """
        Send UI update to frontend.
        
        Args:
            ui_output: Output dari BehaviorFSM.get_ui_output()
        """
        await self.broadcast("ui_update", ui_output)
        
    async def stop(self):
        """Stop WebSocket server"""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("🛑 IPC Server stopped")


# Singleton instance untuk digunakan oleh orchestrator
_ipc_server: Optional[IPCServer] = None


def get_ipc_server() -> IPCServer:
    """Get singleton IPC server instance"""
    global _ipc_server
    if _ipc_server is None:
        _ipc_server = IPCServer()
    return _ipc_server


async def main():
    """Test IPC server standalone"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = get_ipc_server()
    await server.start()
    
    # Keep server running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
