#!/usr/bin/env python3
"""
Test WebSocket streaming connection
"""

import asyncio
import json
import websockets
from websockets.exceptions import ConnectionClosed

async def test_websocket_connection():
    uri = "ws://localhost:9000/api/v1/agents/ws/streaming/test_user/ali-chief-of-staff"
    
    try:
        print("🌊 Connecting to WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send a test message
            test_message = {
                "message": "Hello, test streaming!",
                "context": {"test": True}
            }
            
            await websocket.send(json.dumps(test_message))
            print(f"📤 Sent test message: {test_message}")
            
            # Wait for response(s)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                print(f"📥 Received response: {response}")
                return True
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for response")
                return False
                
    except ConnectionClosed as e:
        print(f"🔌 Connection closed: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket_connection())
    print(f"🎯 Test result: {'PASS' if result else 'FAIL'}")