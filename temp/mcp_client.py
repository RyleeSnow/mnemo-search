import json
import sys
import threading


class MCPClient:
    def __init__(self):
        self._recv_lock = threading.Lock()
        self._pending = {}

    def call_tool(self, method: str, params:dict, id:int):
        req = {"jsonrpc": "2.0", "method": method, "params": params, "id": id}
        sys.stdout.write(json.dumps(req) + "\n")
        sys.stdout.flush()
        return self._wait_response(id)
    
    def _wait_response(self, id: int):
        while True:
            line = sys.stdin.readline()
            if not line:
                raise RuntimeError("MCP server stdin closed")
            resp = json.loads(line)
            if resp.get("id") == id:
                if "error" in resp:
                    raise RuntimeError(f"Error in MCP response: {resp['error']['message']}")
                return resp.get("result")