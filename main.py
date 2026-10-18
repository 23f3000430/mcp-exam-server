import hashlib
import re
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI(title="Exam MCP Challenge Server", version="1.0.0")
NORMALIZED_EMAIL = "23f3000430@ds.study.iitm.ac.in"
SUPPORTED_PROTOCOL_VERSIONS = {"2025-11-25", "2025-06-18", "2025-03-26"}

TOOL = {
    "name": "solve_challenge",
    "description": "Solve the current exam challenge using the X-Exam-Challenge HTTP request header.",
    "inputSchema": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}


def rpc_result(request_id: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def rpc_error(request_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


@app.get("/")
def health() -> dict:
    return {"service": "exam-mcp-challenge-server", "status": "ok"}


@app.post("/")
async def mcp_endpoint(request: Request):
    # The grader uses Streamable HTTP-style JSON-RPC POSTs to this URL.
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(rpc_error(None, -32700, "Parse error"), status_code=400)

    if not isinstance(payload, dict):
        return JSONResponse(rpc_error(None, -32600, "Invalid Request"), status_code=400)

    method = payload.get("method")
    request_id = payload.get("id")
    params = payload.get("params") or {}

    # Notifications do not have an id and must not receive a JSON-RPC result.
    if method == "notifications/initialized":
        return Response(status_code=202)

    if method == "initialize":
        requested = params.get("protocolVersion", "2025-03-26")
        negotiated = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else "2025-03-26"
        result = {
            "protocolVersion": negotiated,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "exam-mcp-challenge-server", "version": "1.0.0"},
            "instructions": "Call solve_challenge; the challenge is supplied in the X-Exam-Challenge HTTP header.",
        }
        return JSONResponse(rpc_result(request_id, result), headers={"MCP-Protocol-Version": negotiated})

    if method == "ping":
        return JSONResponse(rpc_result(request_id, {}))

    if method == "tools/list":
        return JSONResponse(rpc_result(request_id, {"tools": [TOOL]}))

    if method == "tools/call":
        tool_name = params.get("name")
        if tool_name != "solve_challenge":
            return JSONResponse(rpc_error(request_id, -32602, "Unknown tool"))

        # Intentionally read the challenge from the HTTP header, never the JSON body.
        challenge = request.headers.get("X-Exam-Challenge")
        if challenge is None:
            return JSONResponse(rpc_error(request_id, -32602, "Missing X-Exam-Challenge header"))
        if re.fullmatch(r"[0-9a-f]{32}", challenge) is None:
            return JSONResponse(rpc_error(request_id, -32602, "Invalid X-Exam-Challenge header"))

        digest = hashlib.sha256(f"{challenge}:{NORMALIZED_EMAIL}".encode("utf-8")).hexdigest()[:16]
        return JSONResponse(rpc_result(request_id, {"content": [{"type": "text", "text": digest}]}))

    if method and str(method).startswith("notifications/"):
        return Response(status_code=202)

    return JSONResponse(rpc_error(request_id, -32601, "Method not found"))
