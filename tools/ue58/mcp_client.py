import json
import os
import urllib.request
from pathlib import Path

class UnrealClient:
    def __init__(self):
        self.headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
        self.sequence = 0
        reply = self.rpc('initialize', {'protocolVersion': '2025-11-25', 'capabilities': {},
                                        'clientInfo': {'name': 'codex-topgpt-map', 'version': '1.0'}})
        self.headers['MCP-Protocol-Version'] = reply['protocolVersion']
        self.rpc('notifications/initialized', notification=True)

    def rpc(self, method, params=None, notification=False):
        self.sequence += 1
        message = {'jsonrpc': '2.0', 'method': method}
        if not notification:
            message['id'] = self.sequence
        if params is not None:
            message['params'] = params
        request = urllib.request.Request(os.environ.get('MARE_MCP_URL', 'http://127.0.0.1:8000/mcp'),
            data=json.dumps(message).encode(), headers=self.headers)
        with urllib.request.urlopen(request, timeout=float(os.environ.get('MARE_MCP_TIMEOUT','180'))) as response:
            session = response.headers.get('Mcp-Session-Id')
            if session:
                self.headers['Mcp-Session-Id'] = session
            raw = response.read().decode()
        if not raw.strip():
            return None
        if raw.lstrip().startswith('{'):
            result = json.loads(raw)
        else:
            result = json.loads(next(line[5:].strip() for line in raw.splitlines() if line.startswith('data:')))
        if 'error' in result:
            raise RuntimeError(result['error'])
        return result.get('result')

    def call(self, toolset, tool, **arguments):
        if '.' not in toolset:
            toolset = 'editor_toolset.toolsets.' + {'scene':'scene.SceneTools', 'asset':'asset.AssetTools',
                'actor':'actor.ActorTools','mesh':'static_mesh.StaticMeshTools',
                'material':'material.MaterialTools','object':'object.ObjectTools','texture':'texture.TextureTools'}[toolset]
        result = self.rpc('tools/call', {'name':'call_tool', 'arguments':
            {'toolset_name':toolset,'tool_name':tool,'arguments':arguments}})
        if result.get('isError'):
            raise RuntimeError(f'{tool}: {result.get("content")}')
        for entry in result.get('content', []):
            if entry.get('type') == 'text':
                try:
                    value = json.loads(entry['text'])
                    return value.get('returnValue', value) if isinstance(value,dict) else value
                except json.JSONDecodeError:
                    return entry['text']
        return result

    def props(self, instance, **values):
        return self.call('object','set_properties', instance=instance, values=json.dumps(values))

    def save(self):
        return self.call('asset','save_assets',asset_paths=[])

def ref(path):
    return {'refPath':path}

def transform(x=0,y=0,z=0,yaw=0,scale=1):
    return {'location':{'x':x,'y':y,'z':z},'rotation':{'pitch':0,'yaw':yaw,'roll':0},
            'scale':{'x':scale,'y':scale,'z':scale}}

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Native Unreal MCP client for Maré Alta')
    parser.add_argument('--method',default='tools/list')
    parser.add_argument('--params',default='{}')
    parser.add_argument('--output')
    args=parser.parse_args()
    client=UnrealClient()
    result=client.rpc(args.method,json.loads(args.params))
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:Path(args.output).write_text(text,encoding='utf-8')
    print(text)
