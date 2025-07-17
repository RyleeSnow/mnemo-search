from mcp.server.fastmcp import FastMCP
from sympy import im

mcp = FastMCP("index_files")


@mcp.tool()
async def index_files(file_folder: str, data_folder: str, ollama_url: str, ollama_model_name: str) -> str:
    return None


if __name__ == "__main__":
    mcp.run(transport='stdio')
