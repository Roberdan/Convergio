#!/usr/bin/env python3
"""
FINAL WebSocket streaming test with correct agent name
"""

import asyncio
import json
import websockets
from websockets.exceptions import ConnectionClosed

async def test_final_streaming():
    uri = "ws://localhost:9000/api/v1/agents/ws/streaming/test_user/ali_chief_of_staff"
    
    try:
        print("🌊 Connecting to WebSocket with correct agent name...")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send a real business conversation
            conversation_message = {
                "message": "Come posso migliorare la produttività del mio team di sviluppo?",
                "context": {"department": "engineering", "team_size": 12, "current_challenges": "code reviews lenti"}
            }
            
            await websocket.send(json.dumps(conversation_message))
            print(f"📤 Sent: {conversation_message['message']}")
            
            # Collect streaming responses
            responses = []
            chunk_count = 0
            
            try:
                while chunk_count < 15:  # Allow more chunks
                    response = await asyncio.wait_for(websocket.recv(), timeout=20)
                    response_data = json.loads(response)
                    responses.append(response_data)
                    chunk_count += 1
                    
                    chunk_type = response_data.get('data', {}).get('chunk_type', 'unknown')
                    content = response_data.get('data', {}).get('content', '')
                    
                    print(f"📥 [{chunk_type}]: {content[:80]}...")
                    
                    if chunk_type in ['complete', 'error']:
                        break
                        
            except asyncio.TimeoutError:
                print("⏰ Timeout reached")
            
            success = any(r.get('data', {}).get('chunk_type') == 'text' for r in responses)
            print(f"🎯 SUCCESS: {success} - Got {len(responses)} responses")
            return success
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_final_streaming())
    print(f"🏆 FINAL RESULT: {'✅ PASS' if result else '❌ FAIL'}")