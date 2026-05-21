import ezdxf
import uuid

def parse_dxf_to_json(file_path, wall_height=4500, wall_thickness=240):
    try:
        doc = ezdxf.readfile(file_path)
    except IOError:
        print(f"Not a DXF file or a generic I/O error.")
        return None
    except ezdxf.DXFStructureError:
        print(f"Invalid or corrupted DXF file.")
        return None

    msp = doc.modelspace()
    
    unique_layers = set()
    for entity in msp:
        if hasattr(entity.dxf, 'layer'):
            unique_layers.add(entity.dxf.layer)
    
    entities = []
    
    wall_layer = "1.21-墙体"
    # Parse Polylines for walls
    for entity in msp.query(f'LWPOLYLINE[layer=="{wall_layer}"]'):
        path = []
        for point in entity.get_points(format='xy'):
            path.append([point[0], point[1]])
        
        if len(path) > 1:
            entities.append({
                "id": f"wall_{uuid.uuid4().hex[:8]}",
                "layer": wall_layer,
                "generate_type": "PROCEDURAL_WALL",
                "data": {
                    "path": path,
                    "height": wall_height,
                    "thickness": wall_thickness,
                    "material_params": { "color": "#C0C0C0" }
                }
            })
            
    # Parse regular LINES for walls (in case CAD exploded polylines)
    for entity in msp.query(f'LINE[layer=="{wall_layer}"]'):
        start = entity.dxf.start
        end = entity.dxf.end
        entities.append({
            "id": f"wall_{uuid.uuid4().hex[:8]}",
            "layer": wall_layer,
            "generate_type": "PROCEDURAL_WALL",
            "data": {
                "path": [[start.x, start.y], [end.x, end.y]],
                "height": wall_height,
                "thickness": wall_thickness,
                "material_params": { "color": "#C0C0C0" }
            }
        })

    col_layer = "1.20-柱子"
    for entity in msp.query(f'INSERT[layer=="{col_layer}"]'):
        loc = entity.dxf.insert
        block_name = entity.dxf.name # Dynamically retrieve the block name from DXF
        rot = entity.dxf.get('rotation', 0.0)
        scale_x = entity.dxf.get('xscale', 1.0)
        scale_y = entity.dxf.get('yscale', 1.0)
        scale_z = entity.dxf.get('zscale', 1.0)

        entities.append({
            "id": f"column_{uuid.uuid4().hex[:8]}",
            "layer": col_layer,
            "generate_type": "INSTANCE",
            "data": {
                "mesh_id": block_name,
                "transform": { 
                    "loc": [loc.x, loc.y, loc.z], 
                    "rot": [0, 0, rot], 
                    "scale": [scale_x, scale_y, scale_z] 
                }
            }
        })
        
    result_json = {
        "header": { "version": "1.0", "project": "Factory_Demo", "origin": [0,0,0] },
        "entities": entities,
        "debug_info": {
            "found_layers": list(unique_layers)
        }
    }
    
    return result_json


# ═══════════════════════════════════════════════════════════════
# PRD 2.9: 坐标标定工作台 — 预览数据提取
# ═══════════════════════════════════════════════════════════════

# 强制过滤的实体类型（纯文字/填充/视口，确实无几何意义）
_FILTERED_TYPES = {'TEXT', 'MTEXT', 'HATCH', 'TOLERANCE', 'VIEWPORT'}

# 需要炸开（explode）提取内部几何的复合实体类型
_EXPLODE_TYPES = {'DIMENSION', 'LEADER', 'MULTILEADER', 'MLINE'}

# Douglas-Peucker 降采样最大点数
_MAX_POLYLINE_POINTS = 20000


def _douglas_peucker(points, epsilon):
    """Douglas-Peucker 线简化算法"""
    if len(points) <= 2:
        return points
    
    # 找到距离首尾连线最远的点
    start, end = points[0], points[-1]
    max_dist = 0
    max_idx = 0
    for i in range(1, len(points) - 1):
        # 点到线段距离
        dx, dy = end[0] - start[0], end[1] - start[1]
        if dx == 0 and dy == 0:
            dist = ((points[i][0] - start[0])**2 + (points[i][1] - start[1])**2)**0.5
        else:
            t = ((points[i][0] - start[0]) * dx + (points[i][1] - start[1]) * dy) / (dx*dx + dy*dy)
            t = max(0, min(1, t))
            proj_x = start[0] + t * dx
            proj_y = start[1] + t * dy
            dist = ((points[i][0] - proj_x)**2 + (points[i][1] - proj_y)**2)**0.5
        if dist > max_dist:
            max_dist = dist
            max_idx = i
    
    if max_dist > epsilon:
        left = _douglas_peucker(points[:max_idx+1], epsilon)
        right = _douglas_peucker(points[max_idx:], epsilon)
        return left[:-1] + right
    else:
        return [start, end]


def extract_preview_data(file_path):
    """
    提取 DXF 全图层图元，用于坐标标定工作台预览。
    过滤非几何实体（DIMENSION/TEXT/HATCH 等），对大型 Polyline 降采样。
    
    Returns:
        dict: { mode, bounds, polylines, inserts, layers, warnings }
    """
    try:
        doc = ezdxf.readfile(file_path)
    except IOError:
        return {"error": "无法读取文件", "detail": "非 DXF 文件或 I/O 错误"}
    except ezdxf.DXFStructureError:
        return {"error": "DXF 结构错误", "detail": "文件格式损坏"}

    msp = doc.modelspace()
    
    polylines = []
    inserts = []
    layer_stats = {}  # layer_name -> {color, entity_count}
    warnings = []
    all_x, all_y = [], []
    total_points = 0
    poly_counter = 0
    insert_counter = 0

    import math

    # 未处理实体类型计数器
    unhandled_types = {}

    for entity in msp:
        etype = entity.dxftype()
        layer = entity.dxf.get('layer', '0')
        
        # 强制过滤纯文字/填充类型
        if etype in _FILTERED_TYPES:
            continue
        
        # DIMENSION / LEADER → 提取定义点作为位置标记（不炸开，避免辅助线飞出图纸范围）
        if etype in _EXPLODE_TYPES:
            # 初始化图层统计（确保图层出现）
            if layer not in layer_stats:
                color = '#666666'
                try:
                    layer_obj = doc.layers.get(layer)
                    if layer_obj:
                        ci = layer_obj.color
                        color_map = {
                            1:'#ff0000', 2:'#ffff00', 3:'#00ff00', 4:'#00ffff',
                            5:'#0000ff', 6:'#ff00ff', 7:'#ffffff', 8:'#808080',
                            9:'#c0c0c0', 250:'#535353', 251:'#6b6b6b',
                            252:'#848484', 253:'#9c9c9c', 254:'#b4b4b4'
                        }
                        color = color_map.get(ci, f'#{(ci*37%256):02x}{(ci*73%256):02x}{(ci*113%256):02x}')
                except:
                    pass
                layer_stats[layer] = {'color': color, 'entity_count': 0}

            # 提取 DIMENSION 的定义点
            if etype == 'DIMENSION':
                try:
                    # defpoint 是标注测量的实际位置
                    dp = entity.dxf.defpoint
                    text_val = entity.dxf.get('text', '')
                    insert_counter += 1
                    inserts.append({
                        'id': f'insert_{insert_counter:03d}',
                        'block_name': f'DIM_{text_val}' if text_val else 'DIMENSION',
                        'layer': layer,
                        'position': [round(dp.x, 2), round(dp.y, 2)],
                        'rotation': 0.0,
                        'scale_uniform': True,
                        'attribs': {'EQUIP_ID': text_val} if text_val else {}
                    })
                    layer_stats[layer]['entity_count'] += 1
                    all_x.append(dp.x); all_y.append(dp.y)
                except Exception:
                    unhandled_types[etype] = unhandled_types.get(etype, 0) + 1
            else:
                # LEADER / MULTILEADER / MLINE — 提取插入点
                try:
                    if hasattr(entity.dxf, 'insert'):
                        loc = entity.dxf.insert
                    elif hasattr(entity, 'vertices') and len(list(entity.vertices)) > 0:
                        v = list(entity.vertices)[0]
                        loc = type('P', (), {'x': v[0], 'y': v[1]})()
                    else:
                        unhandled_types[etype] = unhandled_types.get(etype, 0) + 1
                        continue
                    insert_counter += 1
                    inserts.append({
                        'id': f'insert_{insert_counter:03d}',
                        'block_name': etype,
                        'layer': layer,
                        'position': [round(loc.x, 2), round(loc.y, 2)],
                        'rotation': 0.0,
                        'scale_uniform': True,
                        'attribs': {}
                    })
                    layer_stats[layer]['entity_count'] += 1
                    all_x.append(loc.x); all_y.append(loc.y)
                except Exception:
                    unhandled_types[etype] = unhandled_types.get(etype, 0) + 1
            continue
        
        # 初始化图层统计
        if layer not in layer_stats:
            color = '#666666'
            try:
                layer_obj = doc.layers.get(layer)
                if layer_obj:
                    ci = layer_obj.color
                    color_map = {
                        1:'#ff0000', 2:'#ffff00', 3:'#00ff00', 4:'#00ffff',
                        5:'#0000ff', 6:'#ff00ff', 7:'#ffffff', 8:'#808080',
                        9:'#c0c0c0', 250:'#535353', 251:'#6b6b6b',
                        252:'#848484', 253:'#9c9c9c', 254:'#b4b4b4'
                    }
                    color = color_map.get(ci, f'#{(ci*37%256):02x}{(ci*73%256):02x}{(ci*113%256):02x}')
            except:
                pass
            layer_stats[layer] = {'color': color, 'entity_count': 0}
        
        # ── LWPOLYLINE ──
        if etype == 'LWPOLYLINE':
            points = [[round(p[0], 2), round(p[1], 2)] for p in entity.get_points(format='xy')]
            if len(points) < 2:
                continue
            total_points += len(points)
            closed = entity.closed
            generate_type = 'PROCEDURAL_FLOOR' if closed else 'PROCEDURAL_WALL'
            poly_counter += 1
            polylines.append({
                'id': f'poly_{poly_counter:03d}',
                'layer': layer,
                'points': points,
                'closed': closed,
                'generate_type': generate_type
            })
            layer_stats[layer]['entity_count'] += 1
            for p in points:
                all_x.append(p[0]); all_y.append(p[1])
        
        # ── LINE ──
        elif etype == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            points = [[round(start.x, 2), round(start.y, 2)], [round(end.x, 2), round(end.y, 2)]]
            poly_counter += 1
            polylines.append({
                'id': f'poly_{poly_counter:03d}',
                'layer': layer,
                'points': points,
                'closed': False,
                'generate_type': 'PROCEDURAL_WALL'
            })
            layer_stats[layer]['entity_count'] += 1
            all_x.extend([points[0][0], points[1][0]])
            all_y.extend([points[0][1], points[1][1]])

        # ── CIRCLE ──（离散为 36 段多边形）
        elif etype == 'CIRCLE':
            cx = entity.dxf.center.x
            cy = entity.dxf.center.y
            r = entity.dxf.radius
            seg = 36
            points = []
            for i in range(seg):
                angle = 2 * math.pi * i / seg
                points.append([round(cx + r * math.cos(angle), 2), round(cy + r * math.sin(angle), 2)])
            total_points += len(points)
            poly_counter += 1
            polylines.append({
                'id': f'poly_{poly_counter:03d}',
                'layer': layer,
                'points': points,
                'closed': True,
                'generate_type': 'PROCEDURAL_FLOOR'
            })
            layer_stats[layer]['entity_count'] += 1
            all_x.extend([cx - r, cx + r])
            all_y.extend([cy - r, cy + r])

        # ── ARC ──（离散为线段）
        elif etype == 'ARC':
            cx = entity.dxf.center.x
            cy = entity.dxf.center.y
            r = entity.dxf.radius
            start_angle = math.radians(entity.dxf.start_angle)
            end_angle = math.radians(entity.dxf.end_angle)
            if end_angle <= start_angle:
                end_angle += 2 * math.pi
            sweep = end_angle - start_angle
            seg = max(8, int(sweep / (2 * math.pi) * 36))
            points = []
            for i in range(seg + 1):
                angle = start_angle + sweep * i / seg
                points.append([round(cx + r * math.cos(angle), 2), round(cy + r * math.sin(angle), 2)])
            total_points += len(points)
            poly_counter += 1
            polylines.append({
                'id': f'poly_{poly_counter:03d}',
                'layer': layer,
                'points': points,
                'closed': False,
                'generate_type': 'PROCEDURAL_WALL'
            })
            layer_stats[layer]['entity_count'] += 1
            for p in points:
                all_x.append(p[0]); all_y.append(p[1])

        # ── ELLIPSE ──（离散为多边形）
        elif etype == 'ELLIPSE':
            try:
                cx = entity.dxf.center.x
                cy = entity.dxf.center.y
                major_axis = entity.dxf.major_axis
                ratio = entity.dxf.ratio
                a = math.sqrt(major_axis.x ** 2 + major_axis.y ** 2)
                b = a * ratio
                rot = math.atan2(major_axis.y, major_axis.x)
                start_param = entity.dxf.get('start_param', 0.0)
                end_param = entity.dxf.get('end_param', 2 * math.pi)
                if end_param <= start_param:
                    end_param += 2 * math.pi
                seg = 36
                points = []
                for i in range(seg + 1):
                    t = start_param + (end_param - start_param) * i / seg
                    lx = a * math.cos(t)
                    ly = b * math.sin(t)
                    px = cx + lx * math.cos(rot) - ly * math.sin(rot)
                    py = cy + lx * math.sin(rot) + ly * math.cos(rot)
                    points.append([round(px, 2), round(py, 2)])
                is_full = abs(end_param - start_param - 2 * math.pi) < 0.01
                total_points += len(points)
                poly_counter += 1
                polylines.append({
                    'id': f'poly_{poly_counter:03d}',
                    'layer': layer,
                    'points': points,
                    'closed': is_full,
                    'generate_type': 'PROCEDURAL_FLOOR' if is_full else 'PROCEDURAL_WALL'
                })
                layer_stats[layer]['entity_count'] += 1
                for p in points:
                    all_x.append(p[0]); all_y.append(p[1])
            except Exception:
                unhandled_types[etype] = unhandled_types.get(etype, 0) + 1

        # ── SPLINE ──（通过 ezdxf flattening 离散）
        elif etype == 'SPLINE':
            try:
                points = [[round(p.x, 2), round(p.y, 2)] for p in entity.flattening(0.5)]
                if len(points) < 2:
                    continue
                closed = entity.closed
                total_points += len(points)
                poly_counter += 1
                polylines.append({
                    'id': f'poly_{poly_counter:03d}',
                    'layer': layer,
                    'points': points,
                    'closed': closed,
                    'generate_type': 'PROCEDURAL_FLOOR' if closed else 'PROCEDURAL_WALL'
                })
                layer_stats[layer]['entity_count'] += 1
                for p in points:
                    all_x.append(p[0]); all_y.append(p[1])
            except Exception:
                unhandled_types[etype] = unhandled_types.get(etype, 0) + 1

        # ── POLYLINE（重量级 2D/3D 多段线）──
        elif etype == 'POLYLINE':
            try:
                points = [[round(v.dxf.location.x, 2), round(v.dxf.location.y, 2)] for v in entity.vertices]
                if len(points) < 2:
                    continue
                closed = entity.is_closed
                total_points += len(points)
                poly_counter += 1
                polylines.append({
                    'id': f'poly_{poly_counter:03d}',
                    'layer': layer,
                    'points': points,
                    'closed': closed,
                    'generate_type': 'PROCEDURAL_FLOOR' if closed else 'PROCEDURAL_WALL'
                })
                layer_stats[layer]['entity_count'] += 1
                for p in points:
                    all_x.append(p[0]); all_y.append(p[1])
            except Exception:
                unhandled_types[etype] = unhandled_types.get(etype, 0) + 1

        # ── INSERT (Block Reference) ──
        elif etype == 'INSERT':
            loc = entity.dxf.insert
            block_name = entity.dxf.name
            rotation = entity.dxf.get('rotation', 0.0)
            xscale = entity.dxf.get('xscale', 1.0)
            yscale = entity.dxf.get('yscale', 1.0)
            max_s = max(abs(xscale), abs(yscale))
            scale_uniform = (abs(xscale - yscale) / max_s <= 0.05) if max_s > 0 else True
            attribs = {}
            try:
                for attrib in entity.attribs:
                    tag = attrib.dxf.tag
                    val = attrib.dxf.text
                    if tag and val:
                        attribs[tag] = val
            except:
                pass
            insert_counter += 1
            inserts.append({
                'id': f'insert_{insert_counter:03d}',
                'block_name': block_name,
                'layer': layer,
                'position': [round(loc.x, 2), round(loc.y, 2)],
                'rotation': round(rotation, 2),
                'scale_uniform': scale_uniform,
                'attribs': attribs
            })
            layer_stats[layer]['entity_count'] += 1
            all_x.append(loc.x); all_y.append(loc.y)

        # ── 未处理的实体类型 ──
        else:
            unhandled_types[etype] = unhandled_types.get(etype, 0) + 1
            layer_stats[layer]['entity_count'] += 1

    # 将未处理类型汇总为警告
    for utype, count in unhandled_types.items():
        warnings.append(f"未渲染的实体类型: {utype} x {count} 个")

    # Douglas-Peucker 降采样（如果总点数超限）
    if total_points > _MAX_POLYLINE_POINTS:
        # 计算整体 bounding box 的 1% 作为容差
        if all_x and all_y:
            bbox_diag = ((max(all_x)-min(all_x))**2 + (max(all_y)-min(all_y))**2)**0.5
            epsilon = bbox_diag * 0.01
            new_total = 0
            for p in polylines:
                p['points'] = _douglas_peucker(p['points'], epsilon)
                new_total += len(p['points'])
            warnings.append(f"Polyline 点数从 {total_points} 降采样至 {new_total}（Douglas-Peucker, ε={epsilon:.1f}）")

    # Bounds
    if all_x and all_y:
        bounds = {'min': [round(min(all_x), 2), round(min(all_y), 2)],
                  'max': [round(max(all_x), 2), round(max(all_y), 2)]}
    else:
        bounds = {'min': [0, 0], 'max': [0, 0]}

    # Layers 列表（去除内部标记）
    layers = []
    for name, info in layer_stats.items():
        if name.startswith('_warned_'):
            continue
        layers.append({
            'name': name,
            'color': info['color'],
            'entity_count': info['entity_count']
        })
    layers.sort(key=lambda l: l['name'])

    return {
        'mode': 'dxf',
        'bounds': bounds,
        'polylines': polylines,
        'inserts': inserts,
        'layers': layers,
        'warnings': warnings
    }
