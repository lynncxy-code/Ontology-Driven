from parser_dxf import extract_preview_data
import json

data = extract_preview_data(r"C:\Users\ADMIN\Desktop\废弃塔.dxf")

equip_layers = [l for l in data["layers"] if "设备" in l["name"] or "预留" in l["name"]]
print("=== 设备相关图层 ===")
for l in equip_layers:
    print(f"  {l['name']}: {l['entity_count']} 个实体")

equip_inserts = [i for i in data["inserts"] if "设备" in i["layer"] or "预留" in i["layer"]]
print(f"\n=== 设备INSERT总数: {len(equip_inserts)} ===")
for i in equip_inserts[:5]:
    print(f"  [{i['layer']}] {i['block_name']} pos={i['position']}")

print(f"\n=== warnings ({len(data.get('warnings',[]))}) ===")
for w in data.get("warnings", []):
    print(f"  {w}")

print(f"\n总polylines={len(data['polylines'])}, 总inserts={len(data['inserts'])}, 总layers={len(data['layers'])}")
