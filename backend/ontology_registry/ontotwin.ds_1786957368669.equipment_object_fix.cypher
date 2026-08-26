// SCC W18 semantic correction: Equipment is a business ObjectType, not an interface.
// CAD types remain concrete ObjectTypes and use MAPS_TO for the reviewed cross-granularity mapping.

MERGE (e:ObjectType:OntologyEntity {rid: "ri.obj.413a3b7d-7f54-5a38-8d0c-8538c8314c41"})
SET e.api_name = "equipment",
    e.display_name = "设备",
    e.description = "生产设备；承接业务关系，CAD类型通过独立映射关联。",
    e.lifecycle_status = "ACTIVE",
    e.x_source = "business_ontology:scc_w18_pcb";

MATCH (e:ObjectType {rid: "ri.obj.413a3b7d-7f54-5a38-8d0c-8538c8314c41"})
MATCH (i:InterfaceType)
WHERE i.rid IN [
  "ri.iface.6df2b90b-4fce-59e1-85cf-1ae618adc04a",
  "ri.iface.b6853938-5de6-5b2d-a761-4f495d61ddda",
  "ri.iface.4c79e494-eae7-5fd5-8049-fe8ab1a5e6b4"
]
MERGE (e)-[:IMPLEMENTS]->(i);

MATCH (legacy:InterfaceType {rid: "ri.iface.02baa12b-3ae6-5b13-9fdf-a1b49fbc2ee5"})
MATCH (cad:ObjectType)-[old:IMPLEMENTS]->(legacy)
MATCH (equipment:ObjectType {rid: "ri.obj.413a3b7d-7f54-5a38-8d0c-8538c8314c41"})
MERGE (cad)-[mapping:MAPS_TO]->(equipment)
SET mapping.dataset_id = "ds_1786957368669",
    mapping.building = "W18",
    mapping.floor = "3F",
    mapping.status = "CONFIRMED",
    mapping.confidence = "HIGH"
DELETE old;

MATCH (link:LinkType)-[old:CONNECTS]->(legacy:InterfaceType {rid: "ri.iface.02baa12b-3ae6-5b13-9fdf-a1b49fbc2ee5"})
WHERE link.rid IN [
  "ri.link.80efe74e-67e5-58b7-812f-a445fa34b19b",
  "ri.link.ca7de2f9-93c9-503f-a352-c18575dc7758",
  "ri.link.b5986874-6794-57fc-afee-3776c64170e7",
  "ri.link.96a58a27-a578-5823-bc8f-3eadc2e516c5"
]
MATCH (equipment:ObjectType {rid: "ri.obj.413a3b7d-7f54-5a38-8d0c-8538c8314c41"})
MERGE (link)-[:CONNECTS]->(equipment)
DELETE old;

MATCH (legacy:InterfaceType {rid: "ri.iface.02baa12b-3ae6-5b13-9fdf-a1b49fbc2ee5"})-[old:CONNECTS]->(link:LinkType)
WHERE link.rid IN [
  "ri.link.b0ec91ab-2a84-5bec-ae40-a371fe43c412",
  "ri.link.0ecf7674-bc8a-536d-87a6-ec699763fdda",
  "ri.link.28366607-9b64-5d9f-a516-909f68ebd5f3"
]
MATCH (equipment:ObjectType {rid: "ri.obj.413a3b7d-7f54-5a38-8d0c-8538c8314c41"})
MERGE (equipment)-[:CONNECTS]->(link)
DELETE old;

MATCH (legacy:InterfaceType {rid: "ri.iface.02baa12b-3ae6-5b13-9fdf-a1b49fbc2ee5"})
DETACH DELETE legacy;
