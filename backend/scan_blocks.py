import ezdxf, os, sys, io

# 强制 stdout 用 UTF-8 输出，绕过 Windows 控制台的 GBK
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

doc = ezdxf.readfile('新块.dxf')
print('DXF code page:', doc.encoding)
print('DXF version:', doc.dxfversion)
print()

msp = doc.modelspace()

# 看图层
layers = sorted({e.dxf.layer for e in msp if hasattr(e.dxf, 'layer')})
print(f'=== 图层 ({len(layers)} 个) ===')
for l in layers:
    print(repr(l), '→', l)
print()

# 看 block_name 头10条
inserts = list(msp.query('INSERT'))
block_names = {}
for e in inserts:
    name = e.dxf.name
    layer = e.dxf.layer
    if name not in block_names:
        block_names[name] = {'count': 0, 'layers': set()}
    block_names[name]['count'] += 1
    block_names[name]['layers'].add(layer)

# 只看含中文的 block_name
print('=== 含中文的 block_name ===')
for name, info in sorted(block_names.items()):
    if any('一' <= c <= '鿿' for c in name):
        print(f'{name}  x{info["count"]}  layers: {list(info["layers"])}')
