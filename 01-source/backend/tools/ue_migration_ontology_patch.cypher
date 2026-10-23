// OntoTwin UE migration ontology patch
// Apply in Neo4j Browser or cypher-shell, then sync_types_from_graph --apply --add-missing.

MERGE (o:ObjectType {rid: "ri.obj.283fceb2-831b-58ed-8021-97660c3abd49"})
SET o.api_name = "a",
    o.display_name = "操控机械臂A",
    o.lifecycle_status = 'EXPERIMENTAL',
    o.x_block_name = "ri.obj.283fceb2-831b-58ed-8021-97660c3abd49",
    o.x_source = 'ue_migration',
    o.x_origin = 'ue_migration_csv',
    o.x_group_key = "blueprint_class_path:/Game/ManipulatorRobot/Blueprints/ManipulatorRobot/ManipulatorRobot_BP.ManipulatorRobot_BP",
    o.x_source_folder_path = "ToMigrate",
    o.x_source_asset_path = "/Game/ManipulatorRobot/Blueprints/ManipulatorRobot/ManipulatorRobot_BP.ManipulatorRobot_BP";
MATCH (o:ObjectType {rid: "ri.obj.283fceb2-831b-58ed-8021-97660c3abd49"})
MATCH (i:InterfaceType {api_name: "i3d_representable"})
MERGE (o)-[:IMPLEMENTS]->(i);
MATCH (o:ObjectType {rid: "ri.obj.283fceb2-831b-58ed-8021-97660c3abd49"})
MATCH (i:InterfaceType {api_name: "i3d_spatial"})
MERGE (o)-[:IMPLEMENTS]->(i);

MERGE (o:ObjectType {rid: "ri.obj.5a0312de-2cf7-561a-a0f5-f91e8662454c"})
SET o.api_name = "mig_6517ac6e46",
    o.display_name = "卡车1",
    o.lifecycle_status = 'EXPERIMENTAL',
    o.x_block_name = "ri.obj.5a0312de-2cf7-561a-a0f5-f91e8662454c",
    o.x_source = 'ue_migration',
    o.x_origin = 'ue_migration_csv',
    o.x_group_key = "skeletal_mesh_asset:/Game/WarehouseProps_Bundle/Models/Skeletal/SKM_Reach_Truck_01a.SKM_Reach_Truck_01a",
    o.x_source_folder_path = "ToMigrate/Equipment/Skeletal",
    o.x_source_asset_path = "/Game/WarehouseProps_Bundle/Models/Skeletal/SKM_Reach_Truck_01a.SKM_Reach_Truck_01a";
MATCH (o:ObjectType {rid: "ri.obj.5a0312de-2cf7-561a-a0f5-f91e8662454c"})
MATCH (i:InterfaceType {api_name: "i3d_representable"})
MERGE (o)-[:IMPLEMENTS]->(i);
MATCH (o:ObjectType {rid: "ri.obj.5a0312de-2cf7-561a-a0f5-f91e8662454c"})
MATCH (i:InterfaceType {api_name: "i3d_spatial"})
MERGE (o)-[:IMPLEMENTS]->(i);

MERGE (o:ObjectType {rid: "ri.obj.599472d7-9aa1-5a21-9a1b-4b10e758c694"})
SET o.api_name = "b",
    o.display_name = "操控机械臂B",
    o.lifecycle_status = 'EXPERIMENTAL',
    o.x_block_name = "ri.obj.599472d7-9aa1-5a21-9a1b-4b10e758c694",
    o.x_source = 'ue_migration',
    o.x_origin = 'ue_migration_csv',
    o.x_group_key = "static_mesh_asset:/Game/ManipulatorRobot/Meshes/Manipulator_Robot/SM_ManipulatorRobot_Static.SM_ManipulatorRobot_Static",
    o.x_source_folder_path = "ToMigrate",
    o.x_source_asset_path = "/Game/ManipulatorRobot/Meshes/Manipulator_Robot/SM_ManipulatorRobot_Static.SM_ManipulatorRobot_Static";
MATCH (o:ObjectType {rid: "ri.obj.599472d7-9aa1-5a21-9a1b-4b10e758c694"})
MATCH (i:InterfaceType {api_name: "i3d_representable"})
MERGE (o)-[:IMPLEMENTS]->(i);
MATCH (o:ObjectType {rid: "ri.obj.599472d7-9aa1-5a21-9a1b-4b10e758c694"})
MATCH (i:InterfaceType {api_name: "i3d_spatial"})
MERGE (o)-[:IMPLEMENTS]->(i);

MERGE (o:ObjectType {rid: "ri.obj.2e40ded3-e02d-5468-b573-90739421e63e"})
SET o.api_name = "mig_bde5a34789",
    o.display_name = "工业秤",
    o.lifecycle_status = 'EXPERIMENTAL',
    o.x_block_name = "ri.obj.2e40ded3-e02d-5468-b573-90739421e63e",
    o.x_source = 'ue_migration',
    o.x_origin = 'ue_migration_csv',
    o.x_group_key = "static_mesh_asset:/Game/WarehouseProps_Bundle/Models/SM_Industrial_Scale_01a.SM_Industrial_Scale_01a",
    o.x_source_folder_path = "ToMigrate/Equipment",
    o.x_source_asset_path = "/Game/WarehouseProps_Bundle/Models/SM_Industrial_Scale_01a.SM_Industrial_Scale_01a";
MATCH (o:ObjectType {rid: "ri.obj.2e40ded3-e02d-5468-b573-90739421e63e"})
MATCH (i:InterfaceType {api_name: "i3d_representable"})
MERGE (o)-[:IMPLEMENTS]->(i);
MATCH (o:ObjectType {rid: "ri.obj.2e40ded3-e02d-5468-b573-90739421e63e"})
MATCH (i:InterfaceType {api_name: "i3d_spatial"})
MERGE (o)-[:IMPLEMENTS]->(i);

MERGE (o:ObjectType {rid: "ri.obj.4ab7adad-b7bf-5b15-8eff-0f4bf8c53c87"})
SET o.api_name = "mig_05ea3f4c21",
    o.display_name = "卡车2",
    o.lifecycle_status = 'EXPERIMENTAL',
    o.x_block_name = "ri.obj.4ab7adad-b7bf-5b15-8eff-0f4bf8c53c87",
    o.x_source = 'ue_migration',
    o.x_origin = 'ue_migration_csv',
    o.x_group_key = "static_mesh_asset:/Game/WarehouseProps_Bundle/Models/SM_Pallet_Truck_01a.SM_Pallet_Truck_01a",
    o.x_source_folder_path = "ToMigrate/Equipment",
    o.x_source_asset_path = "/Game/WarehouseProps_Bundle/Models/SM_Pallet_Truck_01a.SM_Pallet_Truck_01a";
MATCH (o:ObjectType {rid: "ri.obj.4ab7adad-b7bf-5b15-8eff-0f4bf8c53c87"})
MATCH (i:InterfaceType {api_name: "i3d_representable"})
MERGE (o)-[:IMPLEMENTS]->(i);
MATCH (o:ObjectType {rid: "ri.obj.4ab7adad-b7bf-5b15-8eff-0f4bf8c53c87"})
MATCH (i:InterfaceType {api_name: "i3d_spatial"})
MERGE (o)-[:IMPLEMENTS]->(i);

MERGE (o:ObjectType {rid: "ri.obj.124168c3-8773-5f16-a951-ff7744ea671f"})
SET o.api_name = "mig_0be32903f1",
    o.display_name = "卡车3",
    o.lifecycle_status = 'EXPERIMENTAL',
    o.x_block_name = "ri.obj.124168c3-8773-5f16-a951-ff7744ea671f",
    o.x_source = 'ue_migration',
    o.x_origin = 'ue_migration_csv',
    o.x_group_key = "static_mesh_asset:/Game/WarehouseProps_Bundle/Models/SM_Reach_Truck_01a.SM_Reach_Truck_01a",
    o.x_source_folder_path = "ToMigrate/Equipment",
    o.x_source_asset_path = "/Game/WarehouseProps_Bundle/Models/SM_Reach_Truck_01a.SM_Reach_Truck_01a";
MATCH (o:ObjectType {rid: "ri.obj.124168c3-8773-5f16-a951-ff7744ea671f"})
MATCH (i:InterfaceType {api_name: "i3d_representable"})
MERGE (o)-[:IMPLEMENTS]->(i);
MATCH (o:ObjectType {rid: "ri.obj.124168c3-8773-5f16-a951-ff7744ea671f"})
MATCH (i:InterfaceType {api_name: "i3d_spatial"})
MERGE (o)-[:IMPLEMENTS]->(i);

MERGE (o:ObjectType {rid: "ri.obj.1bf989bd-ce22-5961-b225-6b2241f1d7ec"})
SET o.api_name = "mig_13c68acd86",
    o.display_name = "卡车4",
    o.lifecycle_status = 'EXPERIMENTAL',
    o.x_block_name = "ri.obj.1bf989bd-ce22-5961-b225-6b2241f1d7ec",
    o.x_source = 'ue_migration',
    o.x_origin = 'ue_migration_csv',
    o.x_group_key = "static_mesh_asset:/Game/WarehouseProps_Bundle/Models/SM_Reach_Truck_01a_Front_02.SM_Reach_Truck_01a_Front_02",
    o.x_source_folder_path = "ToMigrate",
    o.x_source_asset_path = "/Game/WarehouseProps_Bundle/Models/SM_Reach_Truck_01a_Front_02.SM_Reach_Truck_01a_Front_02";
MATCH (o:ObjectType {rid: "ri.obj.1bf989bd-ce22-5961-b225-6b2241f1d7ec"})
MATCH (i:InterfaceType {api_name: "i3d_representable"})
MERGE (o)-[:IMPLEMENTS]->(i);
MATCH (o:ObjectType {rid: "ri.obj.1bf989bd-ce22-5961-b225-6b2241f1d7ec"})
MATCH (i:InterfaceType {api_name: "i3d_spatial"})
MERGE (o)-[:IMPLEMENTS]->(i);

MERGE (o:ObjectType {rid: "ri.obj.d3a34c33-dbad-5696-b88d-0f4445c5158b"})
SET o.api_name = "mig_9d95f328a0",
    o.display_name = "打包机",
    o.lifecycle_status = 'EXPERIMENTAL',
    o.x_block_name = "ri.obj.d3a34c33-dbad-5696-b88d-0f4445c5158b",
    o.x_source = 'ue_migration',
    o.x_origin = 'ue_migration_csv',
    o.x_group_key = "static_mesh_asset:/Game/WarehouseProps_Bundle/Models/SM_Wrapping_Machine_01a.SM_Wrapping_Machine_01a",
    o.x_source_folder_path = "ToMigrate/Equipment",
    o.x_source_asset_path = "/Game/WarehouseProps_Bundle/Models/SM_Wrapping_Machine_01a.SM_Wrapping_Machine_01a";
MATCH (o:ObjectType {rid: "ri.obj.d3a34c33-dbad-5696-b88d-0f4445c5158b"})
MATCH (i:InterfaceType {api_name: "i3d_representable"})
MERGE (o)-[:IMPLEMENTS]->(i);
MATCH (o:ObjectType {rid: "ri.obj.d3a34c33-dbad-5696-b88d-0f4445c5158b"})
MATCH (i:InterfaceType {api_name: "i3d_spatial"})
MERGE (o)-[:IMPLEMENTS]->(i);
