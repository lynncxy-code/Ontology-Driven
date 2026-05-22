"""诊断脚本：分析设备图层的实体"""
import ezdxf

dxf_path = r"C:\Users\ADMIN\Desktop\废弃塔.dxf"
print(f"分析文件: {dxf_path}\n")

doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

KEYWORDS = ['设备', '预留', '生产']

# 统计
layer_type_stats = {}
for entity in msp:
    layer = entity.dxf.get('layer', '0')
    etype = entity.dxftype()
    key = (layer, etype)
    layer_type_stats[key] = layer_type_stats.get(key, 0) + 1

print("=" * 70)
print("设备相关图层 — 实体类型统计")
print("=" * 70)
for (layer, etype), count in sorted(layer_type_stats.items()):
    if any(kw in layer for kw in KEYWORDS):
        print(f"  [{layer}]  {etype:20s} x {count}")

print("\n" + "=" * 70)
print("设备相关图层 — 前 5 个实体的详细坐标")
print("=" * 70)

shown = {}
for entity in msp:
    layer = entity.dxf.get('layer', '0')
    if not any(kw in layer for kw in KEYWORDS):
        continue
    shown[layer] = shown.get(layer, 0) + 1
    if shown[layer] > 5:
        continue

    etype = entity.dxftype()
    print(f"\n--- [{layer}] #{shown[layer]} 类型={etype} ---")
    
    if etype == 'DIMENSION':
        for attr in ['defpoint', 'defpoint2', 'defpoint3', 'insert', 'text_midpoint', 'text']:
            try:
                val = entity.dxf.get(attr)
                if val is not None:
                    print(f"  {attr}: {val}")
            except:
                pass
        try:
            print(f"  dimtype: {entity.dxf.dimtype}")
        except:
            pass
    elif etype == 'INSERT':
        print(f"  position: {entity.dxf.insert}")
        print(f"  block_name: {entity.dxf.name}")
    else:
        for key in ['insert', 'start', 'end', 'center', 'radius']:
            try:
                val = getattr(entity.dxf, key, None)
                if val is not None:
                    print(f"  {key}: {val}")
            except:
                pass

# 同时打印图纸 bounds 供参考
print("\n" + "=" * 70)
print("图纸范围参考（从所有 LWPOLYLINE/LINE 的坐标推算）")
print("=" * 70)
all_x, all_y = [], []
for entity in msp:
    etype = entity.dxftype()
    if etype == 'LWPOLYLINE':
        for p in entity.get_points(format='xy'):
            all_x.append(p[0]); all_y.append(p[1])
    elif etype == 'LINE':
        all_x.extend([entity.dxf.start.x, entity.dxf.end.x])
        all_y.extend([entity.dxf.start.y, entity.dxf.end.y])
    elif etype == 'INSERT':
        all_x.append(entity.dxf.insert.x)
        all_y.append(entity.dxf.insert.y)

if all_x:
    print(f"  X: {min(all_x):.0f} ~ {max(all_x):.0f}")
    print(f"  Y: {min(all_y):.0f} ~ {max(all_y):.0f}")
