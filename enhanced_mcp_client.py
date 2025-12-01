#!/usr/bin/env python3
"""
Enhanced MCP Direct Client - Supports asynchronous MCP services on the Motar platform
Handles HTTP 202 asynchronous responses and obtains results via SSE
"""

import requests
import json
import time
import threading
import queue
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

@dataclass
class AsyncMCPResult:
    """Asynchronous MCP call result"""
    success: bool
    data: str
    service_name: str
    execution_time: float
    session_id: Optional[str] = None
    error_message: Optional[str] = None

class AsyncMCPClient:
    """Asynchronous MCP client - optimized for Motar platform"""
    
    def __init__(self):
        self.timeout = 60
        self.result_timeout = 30  # Timeout for waiting for asynchronous results
        
        # Motar MCP service configuration
        self.mcp_services = {
            "fetch": {
                "url": "https://mcp.api-inference.modelscope.net/6ec508e067dc41/sse",
                "name": "Fetch MCP",
                "enabled": True,
                "tools": {
                    "fetch": {
                        "url": "string",
                        "max_length": "integer", 
                        "start_index": "integer",
                        "raw": "boolean"
                    }
                }
            },
            "deepwiki": {
                "url": "https://mcp.api-inference.modelscope.net/d4ed08072d2846/sse",
                "name": "DeepWiki MCP", 
                "enabled": True,
                "tools": {
                    "deepwiki_fetch": {
                        "url": "string",
                        "mode": "string",
                        "maxDepth": "integer"
                    }
                }
            }
        }
    
    def _get_sse_endpoint(self, service_url: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Get SSE endpoint and session_id"""
        try:
            headers = {
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            }
            
            logger.info(f"🔗 Connecting to SSE: {service_url}")
            response = requests.get(service_url, headers=headers, timeout=15, stream=True)
            
            if response.status_code != 200:
                logger.error(f"❌ SSE connection failed: HTTP {response.status_code}")
                return False, None, None
            
            # Parse SSE events
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    if '/messages/' in data and 'session_id=' in data:
                        session_id = data.split('session_id=')[1]
                        logger.info(f"✅ Obtained session_id: {session_id}")
                        response.close()
                        return True, data, session_id
                elif line == "":
                    break
            
            response.close()
            logger.error("❌ Failed to obtain a valid endpoint")
            return False, None, None
            
        except Exception as e:
            logger.error(f"💥 SSE connection exception: {str(e)}")
            return False, None, None
    
    def _listen_for_result(self, service_url: str, session_id: str, result_queue: queue.Queue):
        """Listen to SSE stream to get asynchronous results"""
        try:
            headers = {
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            }
            
            logger.info(f"👂 Starting to listen for results...")
            response = requests.get(service_url, headers=headers, timeout=self.result_timeout, stream=True)
            
            if response.status_code != 200:
                result_queue.put(("error", f"Listening connection failed: HTTP {response.status_code}"))
                return
            
            # Listen for SSE events
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    data_str = line[6:]
                    try:
                        # Try to parse JSON data
                        data = json.loads(data_str)
                        if isinstance(data, dict):
                            # Check if it is an MCP response
                            if "result" in data or "error" in data:
                                logger.info("✅ Received MCP response")
                                result_queue.put(("success", data))
                                break
                            elif "id" in data:  # Possibly an MCP response
                                result_queue.put(("success", data))
                                break
                    except json.JSONDecodeError:
                        # Non-JSON data, possibly plain text result
                        if len(data_str.strip()) > 10:
                            logger.info("✅ Received text response")
                            result_queue.put(("success", {"result": {"text": data_str}}))
                            break
                elif line.startswith('event: '):
                    event_type = line[7:]
                    logger.debug(f"📨 SSE event: {event_type}")
            
            response.close()
            
        except requests.exceptions.Timeout:
            logger.warning("⏰ Result listening timed out")
            result_queue.put(("timeout", "Waiting for result timed out"))
        except Exception as e:
            logger.error(f"💥 Listening exception: {str(e)}")
            result_queue.put(("error", f"Listening exception: {str(e)}"))
    
    def call_mcp_service_async(
        self,
        service_key: str,
        tool_name: str,
        tool_args: Dict[str, Any]
    ) -> AsyncMCPResult:
        """Asynchronously call MCP service"""
        
        if service_key not in self.mcp_services:
            return AsyncMCPResult(
                success=False,
                data="",
                service_name=service_key,
                execution_time=0.0,
                error_message=f"Unknown service: {service_key}"
            )
        
        service_config = self.mcp_services[service_key]
        service_url = service_config["url"]
        service_name = service_config["name"]
        
        start_time = time.time()
        
        logger.info(f"🚀 Starting call to {service_name}")
        logger.info(f"📊 Tool: {tool_name}")
        logger.info(f"📋 Parameters: {json.dumps(tool_args, ensure_ascii=False)}")
        
        # Step 1: Get SSE endpoint
        success, endpoint_path, session_id = self._get_sse_endpoint(service_url)
        if not success:
            return AsyncMCPResult(
                success=False,
                data="",
                service_name=service_name,
                execution_time=time.time() - start_time,
                error_message="Failed to get endpoint"
            )
        
        # Step 2: Start result listener
        result_queue = queue.Queue()
        listener_thread = threading.Thread(
            target=self._listen_for_result,
            args=(service_url, session_id, result_queue)
        )
        listener_thread.daemon = True
        listener_thread.start()
        
        # Wait a short time to ensure listener is ready
        time.sleep(0.5)
        
        # Step 3: Send MCP request
        try:
            base_url = service_url.replace('/sse', '')
            full_endpoint = urljoin(base_url, endpoint_path)
            
            mcp_request = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": tool_args
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            logger.info(f"📤 Sending request to: {full_endpoint}")
            response = requests.post(full_endpoint, json=mcp_request, headers=headers, timeout=10)
            
            logger.info(f"📊 Request response: HTTP {response.status_code}")
            
            if response.status_code == 202:  # Accepted - asynchronous processing
                logger.info("✅ Request accepted, waiting for asynchronous result...")
                
                # Step 4: Wait for asynchronous result
                try:
                    result_type, result_data = result_queue.get(timeout=self.result_timeout)
                    
                    execution_time = time.time() - start_time
                    
                    if result_type == "success":
                        # Parse result data
                        content = self._extract_content_from_response(result_data)
                        if content and len(content.strip()) > 10:
                            logger.info(f"✅ {service_name} asynchronous call succeeded!")
                            return AsyncMCPResult(
                                success=True,
                                data=content,
                                service_name=service_name,
                                execution_time=execution_time,
                                session_id=session_id
                            )
                        else:
                            return AsyncMCPResult(
                                success=False,
                                data="",
                                service_name=service_name,
                                execution_time=execution_time,
                                session_id=session_id,
                                error_message="Response content is empty"
                            )
                    else:
                        return AsyncMCPResult(
                            success=False,
                            data="",
                            service_name=service_name,
                            execution_time=execution_time,
                            session_id=session_id,
                            error_message=str(result_data)
                        )
                        
                except queue.Empty:
                    return AsyncMCPResult(
                        success=False,
                        data="",
                        service_name=service_name,
                        execution_time=time.time() - start_time,
                        session_id=session_id,
                        error_message="Timeout waiting for asynchronous result"
                    )
            
            elif response.status_code == 200:
                # Synchronous response
                try:
                    data = response.json()
                    content = self._extract_content_from_response(data)
                    execution_time = time.time() - start_time
                    
                    return AsyncMCPResult(
                        success=bool(content and len(content.strip()) > 10),
                        data=content or "",
                        service_name=service_name,
                        execution_time=execution_time,
                        session_id=session_id,
                        error_message=None if content else "Response content is empty"
                    )
                except json.JSONDecodeError:
                    content = response.text
                    return AsyncMCPResult(
                        success=len(content.strip()) > 10,
                        data=content,
                        service_name=service_name,
                        execution_time=time.time() - start_time,
                        session_id=session_id
                    )
            else:
                return AsyncMCPResult(
                    success=False,
                    data="",
                    service_name=service_name,
                    execution_time=time.time() - start_time,
                    session_id=session_id,
                    error_message=f"HTTP {response.status_code}: {response.text[:200]}"
                )
                
        except Exception as e:
            return AsyncMCPResult(
                success=False,
                data="",
                service_name=service_name,
                execution_time=time.time() - start_time,
                session_id=session_id,
                error_message=f"Request exception: {str(e)}"
            )
    
    def _extract_content_from_response(self, response_data: Any) -> Optional[str]:
        """Extract content from response"""
        try:
            if isinstance(response_data, str):
                return response_data
            
            if isinstance(response_data, dict):
                # Check standard MCP response format
                if "result" in response_data:
                    result = response_data["result"]
                    
                    # Check content array
                    if "content" in result and isinstance(result["content"], list):
                        contents = []
                        for item in result["content"]:
                            if isinstance(item, dict) and "text" in item:
                                contents.append(item["text"])
                            elif isinstance(item, str):
                                contents.append(item)
                        if contents:
                            return "\n".join(contents)
                    
                    # Check other fields
                    for field in ["text", "data", "message"]:
                        if field in result and result[field]:
                            return str(result[field])
                    
                    # If result itself is a string
                    if isinstance(result, str):
                        return result
                
                # Check errors
                if "error" in response_data:
                    error = response_data["error"]
                    if isinstance(error, dict) and "message" in error:
                        return f"Error: {error['message']}"
                    else:
                        return f"Error: {str(error)}"
                
                # Check direct fields
                for field in ["content", "data", "text", "message", "response"]:
                    if field in response_data and response_data[field]:
                        content = response_data[field]
                        if isinstance(content, list):
                            return "\n".join(str(item) for item in content if item)
                        else:
                            return str(content)
            
            # If no match, return JSON string
            return json.dumps(response_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.warning(f"⚠️ Content extraction failed: {e}")
            return str(response_data) if response_data else None

# Global instance
async_mcp_client = AsyncMCPClient()

# Convenience functions
def call_fetch_mcp_async(url: str, max_length: int = 5000) -> AsyncMCPResult:
    """Asynchronously call Fetch MCP service"""
    return async_mcp_client.call_mcp_service_async(
        "fetch",
        "fetch",
        {"url": url, "max_length": max_length}
    )

def call_deepwiki_mcp_async(url: str, mode: str = "aggregate") -> AsyncMCPResult:
    """Asynchronously call DeepWiki MCP service"""
    return async_mcp_client.call_mcp_service_async(
        "deepwiki",
        "deepwiki_fetch", 
        {"url": url, "mode": mode}
    )

if __name__ == "__main__":
    # Test asynchronous MCP client
    print("🧪 Testing asynchronous MCP client")
    print("=" * 50)
    
    # Test Fetch MCP
    print("Testing Fetch MCP...")
    result = call_fetch_mcp_async("https://example.com")
    print(f"Success: {result.success}")
    print(f"Content length: {len(result.data) if result.data else 0}")
    print(f"Execution time: {result.execution_time:.2f}s")
    if result.error_message:
        print(f"Error: {result.error_message}")
    
    print("\n" + "-" * 30)
    
    # Test DeepWiki MCP
    print("Testing DeepWiki MCP...")
    result = call_deepwiki_mcp_async("https://deepwiki.org/openai/openai-python")
    print(f"Success: {result.success}")
    print(f"Content length: {len(result.data) if result.data else 0}")
    print(f"Execution time: {result.execution_time:.2f}s")
    if result.error_message:
        print(f"Error: {result.error_message}")
    
    print("\n✅ Asynchronous MCP client test completed")