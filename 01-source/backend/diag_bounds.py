"""检查设备 INSERT 的块定义几何范围 + 变换后的实际范围"""
import ezdxf

doc = ezdxf.readfile(r"C:\Users\ADMIN\Desktop\废弃塔.dxf")
msp = doc.modelspace()

# 先看块定义的几何范围
block_bounds = {}
for block in doc.blocks:
    name = block.name
    if name.startswith('*'):  # 跳过匿名块
        continue
    xs, ys = [], []
    for e in block:
        etype = e.dxftype()
        if etype == 'LWPOLYLINE':
            for p in e.get_points(format='xy'):
                xs.append(p[0]); ys.append(p[1])
        elif etype == 'LINE':
            xs.extend([e.dxf.start.x, e.dxf.end.x])
            ys.extend([e.dxf.start.y, e.dxf.end.y])
        elif etype == 'CIRCLE':
            xs.extend([e.dxf.center.x - e.dxf.radius, e.dxf.center.x + e.dxf.radius])
            ys.extend([e.dxf.center.y - e.dxf.radius, e.dxf.center.y + e.dxf.radius])
        elif etype == 'ARC':
            xs.append(e.dxf.center.x); ys.append(e.dxf.center.y)
    if xs:
        block_bounds[name] = (min(xs), max(xs), min(ys), max(ys))

# 找设备图层的 INSERT, 计算变换后的实际边界
print("=== 设备 INSERT 详情（含块几何变换后的实际范围）===\n")
for e in msp:
    layer = e.dxf.get('layer', '0')
    if e.dxftype() != 'INSERT':
        continue
    if '设备' not in layer and '预留' not in layer:
        continue
    
    bname = e.dxf.name
    ix, iy = e.dxf.insert.x, e.dxf.insert.y
    sx = e.dxf.get('xscale', 1.0)
    sy = e.dxf.get('yscale', 1.0)
    rot = e.dxf.get('rotation', 0.0)
    
    line = f"[{layer}] block={bname} insert=({ix:.0f}, {iy:.0f}) scale=({sx}, {sy}) rot={rot}"
    
    if bname in block_bounds:
        bx0, bx1, by0, by1 = block_bounds[bname]
        # 简化变换: 不考虑旋转, 只考虑缩放+平移
        real_x0 = ix + bx0 * sx
        real_x1 = ix + bx1 * sx
        real_y0 = iy + by0 * sy
        real_y1 = iy + by1 * sy
        # 确保 min < max
        rx_min, rx_max = min(real_x0, real_x1), max(real_x0, real_x1)
        ry_min, ry_max = min(real_y0, real_y1), max(real_y0, real_y1)
        line += f"\n    块几何: ({bx0:.0f}~{bx1:.0f}, {by0:.0f}~{by1:.0f})"
        line += f"\n    变换后实际范围: X({rx_min:.0f}~{rx_max:.0f}) Y({ry_min:.0f}~{ry_max:.0f})"
    
    print(line + "\n")
