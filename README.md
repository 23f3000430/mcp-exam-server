# Exam MCP Challenge Server

Minimal stateless MCP-compatible Streamable HTTP endpoint for the exam challenge.

- Public endpoint: `POST /`
- Tool: `solve_challenge` (no required input properties)
- Reads `X-Exam-Challenge` from the current HTTP request headers for every `tools/call`.
- Computes `SHA-256(challenge + ":" + normalized exam email)`, returning the first 16 lowercase hex characters as one MCP text content block.

## Deploy on Render

Create a **new** Render Blueprint or Web Service from this repository. For a Web Service, use:

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Use the root HTTPS URL as the MCP endpoint. Do not use the Acme ledger service URL.

## Protocol flow supported

- `initialize`
- `notifications/initialized`
- `tools/list`
- `tools/call`
- `ping`

The only exposed tool is `solve_challenge`.
