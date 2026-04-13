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
