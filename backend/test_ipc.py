"""
Test untuk IPC Server - WebSocket communication
"""

import pytest
import asyncio
import json
import websockets
from backend.ipc_server import IPCServer


@pytest.mark.asyncio
async def test_ipc_server_start():
    """Test IPC server can start"""
    server = IPCServer(port=8766)  # Use different port untuk testing
    
    await server.start()
    assert server.running is True
    
    await server.stop()


@pytest.mark.asyncio
async def test_ipc_client_connection():
    """Test client dapat connect ke server"""
    server = IPCServer(port=8767)
    await server.start()
    
    # Connect as client
    async with websockets.connect("ws://localhost:8767") as ws:
        assert ws.open
        
        # Send ping
        await ws.send(json.dumps({"type": "ping", "data": {}}))
        
        # Expect pong
        response = await ws.recv()
        msg = json.loads(response)
        
        assert msg["type"] == "pong"
    
    await server.stop()


@pytest.mark.asyncio
async def test_ipc_broadcast():
    """Test broadcast ke multiple clients"""
    server = IPCServer(port=8768)
    await server.start()
    
    # Connect 2 clients
    async with websockets.connect("ws://localhost:8768") as ws1:
        async with websockets.connect("ws://localhost:8768") as ws2:
            # Broadcast message
            await server.broadcast("test_event", {"message": "Hello clients"})
            
            # Both clients should receive
            msg1 = json.loads(await ws1.recv())
            msg2 = json.loads(await ws2.recv())
            
            assert msg1["type"] == "test_event"
            assert msg2["type"] == "test_event"
            assert msg1["data"]["message"] == "Hello clients"
    
    await server.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
