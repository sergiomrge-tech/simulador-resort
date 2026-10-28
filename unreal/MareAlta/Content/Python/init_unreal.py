# Project MCP toolsets are editor-only; never imported by packaged runtime.
import unreal
if hasattr(unreal,'ToolsetDefinition'):
    import mare_mcp
