#!/usr/bin/env python3
"""
Extended WebSocket streaming test - full conversation flow
"""

import asyncio
import json
import websockets
from websockets.exceptions import ConnectionClosed

async def test_full_streaming_conversation():
    uri = "ws://localhost:9000/api/v1/agents/ws/streaming/test_user/ali-chief-of-staff"
    
    try:
        print("🌊 Connecting to WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send a real conversation message
            conversation_message = {
                "message": "Come posso migliorare la produttività del team?",
                "context": {"department": "engineering", "team_size": 12}
            }
            
            await websocket.send(json.dumps(conversation_message))
            print(f"📤 Sent conversation message: {conversation_message['message']}")
            
            # Collect all streaming responses
            responses = []
            chunk_count = 0
            
            try:
                # Listen for multiple streaming chunks
                while chunk_count < 10:  # Limit to avoid infinite loop
                    response = await asyncio.wait_for(websocket.recv(), timeout=15)
                    response_data = json.loads(response)
                    responses.append(response_data)
                    chunk_count += 1
                    
                    chunk_type = response_data.get('data', {}).get('chunk_type', 'unknown')
                    content = response_data.get('data', {}).get('content', '')
                    
                    print(f"📥 Chunk {chunk_count} [{chunk_type}]: {content[:100]}...")
                    
                    # Stop if we get a completion status
                    if chunk_type in ['complete', 'error']:
                        break
                        
            except asyncio.TimeoutError:
                print("⏰ Timeout - stopping collection")
            
            print(f"🎯 Collected {len(responses)} streaming responses")
            return len(responses) > 1  # Success if we got multiple chunks
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_full_streaming_conversation())
    print(f"🎯 Extended test result: {'PASS' if result else 'FAIL'}")