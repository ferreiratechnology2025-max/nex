"""
WebSocket Handler - Nex.spec.md Seção 4
Real-time chat via WebSocket
"""

import asyncio
import json
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse

from src.metrics import metrics


router = APIRouter()


WS_TIMEOUT = 30  # seconds of inactivity before disconnect


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        metrics.increment_connections()
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        metrics.decrement_connections()
    
    async def send_message(self, websocket: WebSocket, message: str):
        try:
            await websocket.send_text(message)
        except:
            pass
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await self.send_message(connection, message)


manager = ConnectionManager()


async def generate_response(
    llm_manager, 
    prompt: str, 
    max_tokens: int = 256, 
    temperature: float = 0.7
) -> AsyncGenerator[str, None]:
    """Generate response from LLM as async generator"""
    if llm_manager is None:
        yield "Error: LLM manager not initialized"
        return
    
    try:
        from src.core.llm_manager import Request as LLMRequest
        
        request = LLMRequest(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True
        )
        
        # Use streaming generator
        async for token in llm_manager._generate_stream(request):
            yield token
            
    except Exception as e:
        yield f"Error: {str(e)}"


@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket)
    
    llm_manager = None
    memory_system = None
    
    # Get managers from app state via websocket scope
    app = websocket.scope.get("app")
    if app and hasattr(app.state, 'llm_manager'):
        llm_manager = app.state.llm_manager
    if app and hasattr(app.state, 'memory_system'):
        memory_system = app.state.memory_system
    
    try:
        while True:
            try:
                # Wait for message with timeout
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=WS_TIMEOUT
                )
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Timeout: no activity"}))
                break
            
            text = data.get("text", "")
            max_tokens = data.get("max_tokens", 256)
            temperature = data.get("temperature", 0.7)
            use_memory = data.get("use_memory", True)
            use_web_search = data.get("use_web_search", False)
            
            if not text:
                continue
            
            # Get context from memory if enabled
            context = ""
            if use_memory and memory_system:
                try:
                    memories = await memory_system.buscar_contexto(text, k=3)
                    if memories:
                        context = "\n\n".join([m['texto'] for m in memories])
                except:
                    pass
            
            # Build prompt
            if context:
                prompt = f"""<|im_start|>system
You are a helpful assistant with access to the memories below.
Use them to answer, but only if relevant.

Memories:
{context}
<|im_end|>
<|im_start|>user
{text}<|im_end|>
<|im_start|>assistant
"""
            else:
                prompt = f"<|im_start|>user\n{text}\n<|im_end|>\n<|im_start|>assistant\n"
            
            # Send initial response
            await websocket.send_text(json.dumps({"type": "start"}))
            
            # Stream tokens
            async for token in generate_response(llm_manager, prompt, max_tokens, temperature):
                await websocket.send_text(json.dumps({
                    "type": "token",
                    "content": token
                }))
            
            await websocket.send_text(json.dumps({"type": "end"}))
            
    except WebSocketDisconnect:
        pass
    except json.JSONDecodeError:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))
        except:
            pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except:
            pass
    finally:
        manager.disconnect(websocket)


@router.get("/ws")
async def ws_index():
    """Simple WebSocket status page"""
    return HTMLResponse("""
    <html>
        <head><title>Nex WebSocket</title></head>
        <body>
            <h1>Nex WebSocket Chat</h1>
            <p>Connect to <code>/ws/chat</code> for real-time chat</p>
        </body>
    </html>
    """)