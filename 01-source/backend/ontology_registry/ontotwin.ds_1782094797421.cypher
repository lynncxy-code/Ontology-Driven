// Generated from ontology JSON. Review before running in production.
// Nodes are matched by rid.

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", description: "OntoTwin 三维接口共享属性", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"};

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", description: "OntoTwin 三维接口共享属性", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"};

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", description: "OntoTwin 三维接口共享属性", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"};

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", description: "OntoTwin 三维接口共享属性", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"};

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", description: "OntoTwin 三维接口共享属性", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"};

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", description: "OntoTwin 三维接口共享属性", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"};

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", description: "OntoTwin 三维接口共享属性", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"};

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", description: "OntoTwin 三维接口共享属性", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"};

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", description: "OntoTwin 三维接口共享属性", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"};

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", description: "OntoTwin 三维接口共享属性", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"};

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", description: "OntoTwin 三维接口共享属性", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"};

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", description: "OntoTwin 三维接口共享属性", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"};

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.78e7e192-dcb1-4bd8-9f80-d5274e0d1b59"})
SET n += {api_name: "material_variant", data_type: "DT_STRING", description: "OntoTwin 三维接口共享属性", display_name: "材质变体", lifecycle_status: "ACTIVE", rid: "ri.shprop.78e7e192-dcb1-4bd8-9f80-d5274e0d1b59"};

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.85fc9d92-0476-452a-b1b9-752305265e05"})
SET n += {api_name: "animation_state", data_type: "DT_STRING", description: "OntoTwin 三维接口共享属性", display_name: "动画状态", lifecycle_status: "ACTIVE", rid: "ri.shprop.85fc9d92-0476-452a-b1b9-752305265e05"};

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.b64ab3e5-5605-4e05-ad15-3e48ebcec617"})
SET n += {api_name: "fx_trigger", data_type: "DT_STRING", description: "OntoTwin 三维接口共享属性", display_name: "特效触发", lifecycle_status: "ACTIVE", rid: "ri.shprop.b64ab3e5-5605-4e05-ad15-3e48ebcec617"};

MERGE (n:SharedPropertyType:OntologyEntity {rid: "ri.shprop.4ed3a458-a659-4bb5-b93e-55342ef61253"})
SET n += {api_name: "ui_label_content", data_type: "DT_STRING", description: "OntoTwin 三维接口共享属性", display_name: "标签内容", lifecycle_status: "ACTIVE", rid: "ri.shprop.4ed3a458-a659-4bb5-b93e-55342ef61253"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.deed57c9-d4e6-4396-be88-cb189bf1edbe"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.deed57c9-d4e6-4396-be88-cb189bf1edbe"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c9bc0aa4-545f-41bc-abd7-8259966abc35"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.c9bc0aa4-545f-41bc-abd7-8259966abc35"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.91be0407-31f1-47b8-b869-fb78ddb05472"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.91be0407-31f1-47b8-b869-fb78ddb05472"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.68a8d855-9aff-4475-b138-2a0ef8a93f4a"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.68a8d855-9aff-4475-b138-2a0ef8a93f4a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.dcf1beca-2b81-4a30-9f22-92a8c1e17617"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.dcf1beca-2b81-4a30-9f22-92a8c1e17617"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a9b0d52a-3e6a-41b1-8a22-60949a5cb20b"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.a9b0d52a-3e6a-41b1-8a22-60949a5cb20b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ce5eb5b4-055b-4b14-ade6-01c1b01b8371"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.ce5eb5b4-055b-4b14-ade6-01c1b01b8371"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0a6cacc3-7d3f-4446-8cab-40df582aa6a0"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.0a6cacc3-7d3f-4446-8cab-40df582aa6a0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a35d9477-0df7-43a9-8e30-219bbe91ef6d"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.a35d9477-0df7-43a9-8e30-219bbe91ef6d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.39fe01e0-c128-4b93-b11b-52e5539719bc"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.39fe01e0-c128-4b93-b11b-52e5539719bc"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c471ef32-18d0-4f1e-873b-873e6e65f9f1"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.c471ef32-18d0-4f1e-873b-873e6e65f9f1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3c168335-c1d6-4b50-80e2-78633657b36d"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.3c168335-c1d6-4b50-80e2-78633657b36d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f92cab76-e18f-47fd-8bc2-333dcb476205"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.f92cab76-e18f-47fd-8bc2-333dcb476205"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.935dfae1-739e-4b6c-b2c8-d13fe13f21fd"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.935dfae1-739e-4b6c-b2c8-d13fe13f21fd"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d7bb8989-8516-4fb4-afa2-4dca2acf6236"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.d7bb8989-8516-4fb4-afa2-4dca2acf6236"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f9ff6e3e-0b14-4076-8ae2-f061d4378d47"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.f9ff6e3e-0b14-4076-8ae2-f061d4378d47"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3b4a566c-528c-43d9-9b79-5c4c8e2d16ac"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.3b4a566c-528c-43d9-9b79-5c4c8e2d16ac"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.411b3e59-5e9f-4e7b-82d0-ee3eed8140d7"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.411b3e59-5e9f-4e7b-82d0-ee3eed8140d7"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e2f064a4-710c-4fa4-a1bc-bdca146dbd2f"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.e2f064a4-710c-4fa4-a1bc-bdca146dbd2f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.84674453-6d4e-42db-8bac-6958d31ff159"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.84674453-6d4e-42db-8bac-6958d31ff159"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.53f81a89-0c3b-4ab2-8237-7efdec10e37d"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.53f81a89-0c3b-4ab2-8237-7efdec10e37d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e040f715-a64d-410f-b95e-8670923831cd"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.e040f715-a64d-410f-b95e-8670923831cd"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9c60b219-9d4a-417a-9257-5b2d5fea456b"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.9c60b219-9d4a-417a-9257-5b2d5fea456b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6a16093b-a083-4d6f-af1f-b75470d5d987"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.6a16093b-a083-4d6f-af1f-b75470d5d987"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0ceb36a4-bc22-43d0-b3aa-d405160107b0"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.0ceb36a4-bc22-43d0-b3aa-d405160107b0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9fb2974f-dda7-4129-9aa9-5a98141f31c7"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.9fb2974f-dda7-4129-9aa9-5a98141f31c7"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.43b16a60-0068-422e-bdb3-f61dc4361030"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.43b16a60-0068-422e-bdb3-f61dc4361030"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.64e2bfc9-af76-4497-8e56-4e375657daad"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.64e2bfc9-af76-4497-8e56-4e375657daad"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f10a77c9-5130-4b6e-98fe-2967322e53af"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.f10a77c9-5130-4b6e-98fe-2967322e53af"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.25ef1142-902f-422b-9933-7fc639b21f19"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.25ef1142-902f-422b-9933-7fc639b21f19"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ed7e086a-6342-49cf-b06c-7d1dbe4f2b66"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.ed7e086a-6342-49cf-b06c-7d1dbe4f2b66"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.601a2794-f887-4e85-93ba-82a93e36dae3"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.601a2794-f887-4e85-93ba-82a93e36dae3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5856c1f5-c5eb-4efc-b772-73611fbf1e4d"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.5856c1f5-c5eb-4efc-b772-73611fbf1e4d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e5a285cc-dbf4-430a-a696-a507d8e7a865"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.e5a285cc-dbf4-430a-a696-a507d8e7a865"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a5554ba7-9874-4a03-bace-72e5d3aaa544"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.a5554ba7-9874-4a03-bace-72e5d3aaa544"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1a973526-9812-4e0b-b7dc-80707d86d13f"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.1a973526-9812-4e0b-b7dc-80707d86d13f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f1da4ebf-2a1e-4eb3-ae29-eb86bba63284"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.f1da4ebf-2a1e-4eb3-ae29-eb86bba63284"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a0b1d85f-a45f-4c81-8992-d1c6a4998111"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.a0b1d85f-a45f-4c81-8992-d1c6a4998111"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d172bc31-785c-4e57-b6da-f4253e372511"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.d172bc31-785c-4e57-b6da-f4253e372511"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f49d0716-2a20-45aa-a593-d01ced4f0e61"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.f49d0716-2a20-45aa-a593-d01ced4f0e61"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.bed1902a-b10f-462b-a070-c961e60e2ded"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.bed1902a-b10f-462b-a070-c961e60e2ded"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e2645f87-7b2e-408c-8790-c98ed3d24216"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.e2645f87-7b2e-408c-8790-c98ed3d24216"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.38f39f7c-9c32-457c-a156-1c8369bb5245"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.38f39f7c-9c32-457c-a156-1c8369bb5245"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8fae8474-493e-456e-91cd-94717bb8ece9"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.8fae8474-493e-456e-91cd-94717bb8ece9"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f7dedb41-1ab2-442d-9670-91da17c492b0"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.f7dedb41-1ab2-442d-9670-91da17c492b0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.05d35b07-622b-4437-aa56-ed118b04982c"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.05d35b07-622b-4437-aa56-ed118b04982c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ff9cfda0-f26a-4ffc-895b-45fb0c4b1497"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.ff9cfda0-f26a-4ffc-895b-45fb0c4b1497"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4a1976f3-1315-48a5-9c13-36404936ff6d"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.4a1976f3-1315-48a5-9c13-36404936ff6d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e503bcce-1da1-4778-bb10-0bf9ce07a499"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.e503bcce-1da1-4778-bb10-0bf9ce07a499"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.caa39e88-e849-40d3-866e-5799acd81908"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.caa39e88-e849-40d3-866e-5799acd81908"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3026e034-dea5-4915-9c0c-a86052669aee"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.3026e034-dea5-4915-9c0c-a86052669aee"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f929d92b-f0dd-4ae7-9823-40f3b760ce69"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.f929d92b-f0dd-4ae7-9823-40f3b760ce69"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d01ee882-5d14-44cb-a3a3-500e4e28a642"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.d01ee882-5d14-44cb-a3a3-500e4e28a642"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.245e573b-0908-4bec-9b4d-39df386040a4"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.245e573b-0908-4bec-9b4d-39df386040a4"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.22a2be3e-cc87-470c-8556-60710f985c8d"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.22a2be3e-cc87-470c-8556-60710f985c8d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9dc17eb7-27d4-48c5-9e2a-7e30c685f83a"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.9dc17eb7-27d4-48c5-9e2a-7e30c685f83a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.db3e2bbe-ea45-4e43-a148-7d978840ec53"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.db3e2bbe-ea45-4e43-a148-7d978840ec53"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f54ff19f-17b6-4ae0-8030-40ebc458f094"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.f54ff19f-17b6-4ae0-8030-40ebc458f094"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2f772e0e-d60a-4d56-af3a-933759c65a93"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.2f772e0e-d60a-4d56-af3a-933759c65a93"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c2890215-e2a6-40a7-ab87-5ea9e66ba6ff"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.c2890215-e2a6-40a7-ab87-5ea9e66ba6ff"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f26b1983-ccc4-41d3-9120-1427aa2ad207"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.f26b1983-ccc4-41d3-9120-1427aa2ad207"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1cbb8182-7ca8-4bd8-a6a2-c1d3096dd195"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.1cbb8182-7ca8-4bd8-a6a2-c1d3096dd195"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9fd69543-ea79-4bb3-80a9-4543e4da3af3"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.9fd69543-ea79-4bb3-80a9-4543e4da3af3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.adccc361-17e0-4ee1-8cb2-aea40bf6dd08"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.adccc361-17e0-4ee1-8cb2-aea40bf6dd08"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.dbb1d60c-b2db-474b-b44a-30798737dc33"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.dbb1d60c-b2db-474b-b44a-30798737dc33"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3aff4994-6f06-44ae-b2a7-985773e62a8e"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.3aff4994-6f06-44ae-b2a7-985773e62a8e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.50d66bcb-758f-4bf7-9cdf-e5a1e6b5092c"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.50d66bcb-758f-4bf7-9cdf-e5a1e6b5092c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.22ececb3-55da-4a74-9dad-003023086b86"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.22ececb3-55da-4a74-9dad-003023086b86"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.323c116a-62c3-4dca-ba0d-581ea8f3cc5b"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.323c116a-62c3-4dca-ba0d-581ea8f3cc5b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7eaacf18-016e-4d89-958b-2762099a0f7e"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.7eaacf18-016e-4d89-958b-2762099a0f7e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.09b8b174-e82b-48ba-b9ce-dbde46a6f510"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.09b8b174-e82b-48ba-b9ce-dbde46a6f510"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c1c7ed25-8659-4263-bab7-6bc594115dde"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.c1c7ed25-8659-4263-bab7-6bc594115dde"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6702c5b2-195b-407c-b471-82dbefdacbb5"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.6702c5b2-195b-407c-b471-82dbefdacbb5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.467231c7-6fa1-447d-bdb8-13eefb481f9d"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.467231c7-6fa1-447d-bdb8-13eefb481f9d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2528b454-3bfc-40f8-8e34-21b98cd311e3"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.2528b454-3bfc-40f8-8e34-21b98cd311e3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a307be12-8cec-4c69-8e38-83c3664beabf"})
SET n += {api_name: "material_variant", data_type: "DT_STRING", display_name: "材质变体", lifecycle_status: "ACTIVE", rid: "ri.prop.a307be12-8cec-4c69-8e38-83c3664beabf"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6cb214ed-e5de-4771-9a62-d7ba7aa3ce35"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.6cb214ed-e5de-4771-9a62-d7ba7aa3ce35"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6ff032b3-d6cd-4251-aba4-0e002e1b160d"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.6ff032b3-d6cd-4251-aba4-0e002e1b160d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3f6b8f03-f43b-4d1a-a02f-de78646dd921"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.3f6b8f03-f43b-4d1a-a02f-de78646dd921"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.fd67fd6e-f85b-45b4-9392-e2192d860340"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.fd67fd6e-f85b-45b4-9392-e2192d860340"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d177d39a-b40c-4d13-a850-b489429872a6"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.d177d39a-b40c-4d13-a850-b489429872a6"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9b38dd41-dba5-4275-a3c7-586f0896afb5"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.9b38dd41-dba5-4275-a3c7-586f0896afb5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.cb3116e1-a76f-4c99-a44a-b3ca40793f68"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.cb3116e1-a76f-4c99-a44a-b3ca40793f68"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.cd07bb0a-70a0-4aa0-92d0-1ea92d33b2b1"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.cd07bb0a-70a0-4aa0-92d0-1ea92d33b2b1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a72cabab-dd4d-4b20-b9d7-8cdf060e9540"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.a72cabab-dd4d-4b20-b9d7-8cdf060e9540"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a3231a9f-4ff7-4945-a6ef-f70c4a57d9d1"})
SET n += {api_name: "animation_state", data_type: "DT_STRING", display_name: "动画状态", lifecycle_status: "ACTIVE", rid: "ri.prop.a3231a9f-4ff7-4945-a6ef-f70c4a57d9d1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.cc4200f5-7491-4086-a572-56bf7c00fb55"})
SET n += {api_name: "fx_trigger", data_type: "DT_STRING", display_name: "特效触发", lifecycle_status: "ACTIVE", rid: "ri.prop.cc4200f5-7491-4086-a572-56bf7c00fb55"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8ed71c5f-d708-4e78-94e7-7ef668118646"})
SET n += {api_name: "ui_label_content", data_type: "DT_STRING", display_name: "标签内容", lifecycle_status: "ACTIVE", rid: "ri.prop.8ed71c5f-d708-4e78-94e7-7ef668118646"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.caffa8e7-bf48-4266-859a-873cd3ec0f15"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.caffa8e7-bf48-4266-859a-873cd3ec0f15"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.df596391-b3c4-46a9-8f72-91aaaaad63b2"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.df596391-b3c4-46a9-8f72-91aaaaad63b2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.151a4d1d-781f-4716-a1c9-5f8440ada99f"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.151a4d1d-781f-4716-a1c9-5f8440ada99f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.51ffab5a-7056-4cdf-a28a-326fa6bc01d0"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.51ffab5a-7056-4cdf-a28a-326fa6bc01d0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.07c1fa8b-e5d6-41dc-af6d-3f507a3fb387"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.07c1fa8b-e5d6-41dc-af6d-3f507a3fb387"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.673f64bf-7117-4190-8b5b-5075ba8d43bb"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.673f64bf-7117-4190-8b5b-5075ba8d43bb"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9fdf3d14-3931-41a4-b1b5-362e2782c1ff"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.9fdf3d14-3931-41a4-b1b5-362e2782c1ff"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.007dc89b-488c-4601-82fb-f9871ccc624d"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.007dc89b-488c-4601-82fb-f9871ccc624d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1db107c1-c3bf-44df-bb42-08bfe89a28ef"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.1db107c1-c3bf-44df-bb42-08bfe89a28ef"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a268efe4-c8d9-4600-a9f4-ab2c482b5ceb"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.a268efe4-c8d9-4600-a9f4-ab2c482b5ceb"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d239aced-17d2-4e2e-98dc-fc363a891c52"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.d239aced-17d2-4e2e-98dc-fc363a891c52"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.74d67d0e-13da-4c4d-9576-584300fad9ab"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.74d67d0e-13da-4c4d-9576-584300fad9ab"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.86aa5387-99aa-41fd-8995-029254829371"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.86aa5387-99aa-41fd-8995-029254829371"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f33be0e3-116c-4e01-8ddc-3bc00625bfba"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.f33be0e3-116c-4e01-8ddc-3bc00625bfba"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2af7184a-582d-435f-8ce9-8f9f1350ddbe"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.2af7184a-582d-435f-8ce9-8f9f1350ddbe"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.24e94381-a6eb-4303-82db-e920dbd1af84"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.24e94381-a6eb-4303-82db-e920dbd1af84"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e183731b-aaa5-40d9-a381-98bf5ec3f5f5"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.e183731b-aaa5-40d9-a381-98bf5ec3f5f5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8da2011f-7479-407e-bd76-ec8294a20721"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.8da2011f-7479-407e-bd76-ec8294a20721"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8bc5b954-ddfe-41cb-8c93-d22dccdd6b33"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.8bc5b954-ddfe-41cb-8c93-d22dccdd6b33"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5ddee043-fa7e-42e1-857b-c63cf12775ef"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.5ddee043-fa7e-42e1-857b-c63cf12775ef"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f19a3a29-207a-4162-bb63-5b0c8c896972"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.f19a3a29-207a-4162-bb63-5b0c8c896972"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.11a495cc-ec44-46dc-a6bb-29abf8d02cfd"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.11a495cc-ec44-46dc-a6bb-29abf8d02cfd"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.23eab455-1189-4116-9276-9ad042fcdcf3"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.23eab455-1189-4116-9276-9ad042fcdcf3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.50ad6ea9-a53c-45a4-abfe-7e2aa8374ea8"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.50ad6ea9-a53c-45a4-abfe-7e2aa8374ea8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5191154a-a0d2-490d-8ce0-1011d7163a56"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.5191154a-a0d2-490d-8ce0-1011d7163a56"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2622f719-70b8-4791-a5cd-80e8b1e5ab97"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.2622f719-70b8-4791-a5cd-80e8b1e5ab97"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a5f702ee-b5ea-4606-a9ab-051ed2d2df96"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.a5f702ee-b5ea-4606-a9ab-051ed2d2df96"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e286f528-3d59-4f06-bdfb-56cba646b3da"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.e286f528-3d59-4f06-bdfb-56cba646b3da"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.da78d997-50de-4f00-a6d7-732bb9c15255"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.da78d997-50de-4f00-a6d7-732bb9c15255"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8b92d492-bb35-44d3-b379-03bad0e71531"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.8b92d492-bb35-44d3-b379-03bad0e71531"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.49d4f0a2-e913-4e19-9eba-0e0ff6f0ab90"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.49d4f0a2-e913-4e19-9eba-0e0ff6f0ab90"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.626eeacf-ab39-4eec-935e-96e43d7fca56"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.626eeacf-ab39-4eec-935e-96e43d7fca56"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.755acf5c-e251-435d-9d25-0e26ed14451a"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.755acf5c-e251-435d-9d25-0e26ed14451a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1d2a45da-5fc5-49e8-87ae-c34bfe6bd127"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.1d2a45da-5fc5-49e8-87ae-c34bfe6bd127"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4f8ca48e-8f01-40e0-b2d1-ac1418cec28c"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.4f8ca48e-8f01-40e0-b2d1-ac1418cec28c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e411ce62-77a0-4b9d-8da8-78d81a299521"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.e411ce62-77a0-4b9d-8da8-78d81a299521"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.590ba183-9122-400d-964c-ee6881286989"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.590ba183-9122-400d-964c-ee6881286989"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0313a341-db15-4cc9-bde3-d930cc02ae31"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.0313a341-db15-4cc9-bde3-d930cc02ae31"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.77669b70-b57f-43e4-888b-dba8f753e3c8"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.77669b70-b57f-43e4-888b-dba8f753e3c8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.de4354f1-8731-4c1c-9e3e-53aca72a3634"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.de4354f1-8731-4c1c-9e3e-53aca72a3634"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.54f0029f-a59d-472f-ba79-669203655d9e"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.54f0029f-a59d-472f-ba79-669203655d9e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f70bdb3e-aea7-4dd7-ade6-08d6737ff59c"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.f70bdb3e-aea7-4dd7-ade6-08d6737ff59c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3dd88e4d-9cf0-4b32-a69a-1a30c2d22c47"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.3dd88e4d-9cf0-4b32-a69a-1a30c2d22c47"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5ed0bb8f-f175-4e3f-9aee-cc11a0728f0d"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.5ed0bb8f-f175-4e3f-9aee-cc11a0728f0d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.beb7032b-0bb4-4d33-93a3-36d64b6dd631"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.beb7032b-0bb4-4d33-93a3-36d64b6dd631"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.800cd3a4-bbf0-406d-b595-4bfc8c97f251"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.800cd3a4-bbf0-406d-b595-4bfc8c97f251"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c9c4e792-aebe-4f01-94be-9f59d88d88ea"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.c9c4e792-aebe-4f01-94be-9f59d88d88ea"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6be14a42-d178-4c24-b195-169a45576c33"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.6be14a42-d178-4c24-b195-169a45576c33"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b178b58b-e5cd-4567-b06a-46436d715224"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.b178b58b-e5cd-4567-b06a-46436d715224"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8ad72184-cd7c-4bee-b93a-a76bfbedee53"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.8ad72184-cd7c-4bee-b93a-a76bfbedee53"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3583621f-9781-4cb1-b7c3-b30978064849"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.3583621f-9781-4cb1-b7c3-b30978064849"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9e4ceec5-eb2b-4337-ab9d-5270aa6b8cfc"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.9e4ceec5-eb2b-4337-ab9d-5270aa6b8cfc"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4151ec16-36d5-4a92-8675-a1ce5629177c"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.4151ec16-36d5-4a92-8675-a1ce5629177c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3deb9135-58c1-48aa-9d77-7a11d7eb9a91"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.3deb9135-58c1-48aa-9d77-7a11d7eb9a91"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8cf0c835-a522-4968-94af-aa3920a72519"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.8cf0c835-a522-4968-94af-aa3920a72519"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5b851716-d36f-4c53-b116-666bfb31803b"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.5b851716-d36f-4c53-b116-666bfb31803b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a813085a-ea8e-43b7-9e82-37e311ec489e"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.a813085a-ea8e-43b7-9e82-37e311ec489e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e6b49d14-1d4c-4564-b967-b34767a4a593"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.e6b49d14-1d4c-4564-b967-b34767a4a593"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.beded43e-0e3d-4e5a-ab7f-fb7dd7089d80"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.beded43e-0e3d-4e5a-ab7f-fb7dd7089d80"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5c7493b7-7e06-4637-847b-7e2e82328cfe"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.5c7493b7-7e06-4637-847b-7e2e82328cfe"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3021943b-99d0-4043-a310-d23af5514adb"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.3021943b-99d0-4043-a310-d23af5514adb"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.270fec92-2445-468c-8004-0edf7d660eb9"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.270fec92-2445-468c-8004-0edf7d660eb9"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.838e38ae-ae4b-4972-b5b7-5788d9630b1d"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.838e38ae-ae4b-4972-b5b7-5788d9630b1d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d9564e67-81a1-4173-96ae-92e1ca93a290"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.d9564e67-81a1-4173-96ae-92e1ca93a290"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.06e2462f-d0b8-45ff-93e7-1314dfed15ea"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.06e2462f-d0b8-45ff-93e7-1314dfed15ea"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.743306e4-e1b2-4af5-866f-bf6f8b276cb0"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.743306e4-e1b2-4af5-866f-bf6f8b276cb0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.78434de5-7b88-42d3-8212-24dffdbf5c4f"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.78434de5-7b88-42d3-8212-24dffdbf5c4f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8177c5d3-87be-4d8b-85f8-a77d871baba8"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.8177c5d3-87be-4d8b-85f8-a77d871baba8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c336a3b2-dafa-43ff-a39b-8e524c686810"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.c336a3b2-dafa-43ff-a39b-8e524c686810"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.dd7e2799-9649-4ad0-ae7d-740f60266b59"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.dd7e2799-9649-4ad0-ae7d-740f60266b59"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.562a6170-6a1b-453e-b1da-91edc9185743"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.562a6170-6a1b-453e-b1da-91edc9185743"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.24df180d-6f1f-4787-8098-0b1514895bab"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.24df180d-6f1f-4787-8098-0b1514895bab"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d0e479c6-f907-407f-a090-7687cd983b9b"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.d0e479c6-f907-407f-a090-7687cd983b9b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6fe38279-61d3-40da-bd4b-e1eafae930b1"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.6fe38279-61d3-40da-bd4b-e1eafae930b1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0dadbcfa-148b-4051-b431-6ac7b6387de4"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.0dadbcfa-148b-4051-b431-6ac7b6387de4"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.75474bc3-d4bd-4736-a069-071c5697bbe8"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.75474bc3-d4bd-4736-a069-071c5697bbe8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.825cd8f0-5abc-4735-8aea-a762c2c1cec2"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.825cd8f0-5abc-4735-8aea-a762c2c1cec2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.56063b64-69ae-446c-91b6-0779abd7b90d"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.56063b64-69ae-446c-91b6-0779abd7b90d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c86c5409-df22-486f-9092-86ed1bc451d0"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.c86c5409-df22-486f-9092-86ed1bc451d0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3ba398d2-be63-4563-baa2-b45768b82804"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.3ba398d2-be63-4563-baa2-b45768b82804"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0ccaaf9a-33be-43a6-b93e-daef41221713"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.0ccaaf9a-33be-43a6-b93e-daef41221713"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e0490e5d-71cd-4378-88ba-cfd7782860c0"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.e0490e5d-71cd-4378-88ba-cfd7782860c0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b8c5f9c2-ce46-431e-aa2d-79d7c490e0a9"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.b8c5f9c2-ce46-431e-aa2d-79d7c490e0a9"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.52c5a021-12a9-43cd-afd8-12e4d1c7e5c5"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.52c5a021-12a9-43cd-afd8-12e4d1c7e5c5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.25db2e98-1e52-4b74-9e39-630201f526ad"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.25db2e98-1e52-4b74-9e39-630201f526ad"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9a0085c3-bdea-47e0-aa6c-6384a5fd84e7"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.9a0085c3-bdea-47e0-aa6c-6384a5fd84e7"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f1bec52a-9d24-4127-b35b-286a22f997ec"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.f1bec52a-9d24-4127-b35b-286a22f997ec"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.766034db-285c-47c2-8853-9ac88c7443e5"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.766034db-285c-47c2-8853-9ac88c7443e5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.dcf6740b-3b1c-4bfc-968e-6fcad703a6cf"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.dcf6740b-3b1c-4bfc-968e-6fcad703a6cf"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ece6772b-f5ae-4592-a13d-55690faab422"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.ece6772b-f5ae-4592-a13d-55690faab422"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f4c9703c-4478-47e0-9654-f3c23e184029"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.f4c9703c-4478-47e0-9654-f3c23e184029"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.dc4f3b9e-31d5-4896-b4b4-262aed78a778"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.dc4f3b9e-31d5-4896-b4b4-262aed78a778"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2d2b9440-8856-433a-99ed-57480da8ca63"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.2d2b9440-8856-433a-99ed-57480da8ca63"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9124a638-d5d7-4ccd-9075-65d6b5c79de0"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.9124a638-d5d7-4ccd-9075-65d6b5c79de0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.37766ce4-6e02-4a66-a091-4d970e6d39de"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.37766ce4-6e02-4a66-a091-4d970e6d39de"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0b79c893-2e36-4568-85dc-d68a5689b5ee"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.0b79c893-2e36-4568-85dc-d68a5689b5ee"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2221f441-cb27-4f56-bd1a-e7060acd0139"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.2221f441-cb27-4f56-bd1a-e7060acd0139"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.40fc8287-e992-4bb6-adcf-ee2a3d45874f"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.40fc8287-e992-4bb6-adcf-ee2a3d45874f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4442b61f-ebe4-49bf-85bc-fab7cb7f8621"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.4442b61f-ebe4-49bf-85bc-fab7cb7f8621"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e98133b4-5df5-4142-9d2f-9323bf0fc102"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.e98133b4-5df5-4142-9d2f-9323bf0fc102"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6e81f9d0-e13d-4580-8ae8-3d86b7bad321"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.6e81f9d0-e13d-4580-8ae8-3d86b7bad321"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.60b77fc8-e878-4fbc-8846-2b1e809c2a00"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.60b77fc8-e878-4fbc-8846-2b1e809c2a00"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c00c4290-cd78-4556-816b-1d1806de7e10"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.c00c4290-cd78-4556-816b-1d1806de7e10"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d68cef5b-fc26-4acf-9488-1cdde2501084"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.d68cef5b-fc26-4acf-9488-1cdde2501084"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.39be2e01-06ac-49a6-acf6-a7d0de394e80"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.39be2e01-06ac-49a6-acf6-a7d0de394e80"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.79e67ca7-62c4-40f6-a2ac-28600be6b146"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.79e67ca7-62c4-40f6-a2ac-28600be6b146"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b0dc1af7-16cd-49d8-85b3-704a239696b7"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.b0dc1af7-16cd-49d8-85b3-704a239696b7"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d90920c8-008b-41c9-9386-abc8e526d5ea"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.d90920c8-008b-41c9-9386-abc8e526d5ea"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.59209b5c-0844-4ef2-8d88-c1fafca32589"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.59209b5c-0844-4ef2-8d88-c1fafca32589"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.889652f0-9a8d-401f-98fe-e36617b49c92"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.889652f0-9a8d-401f-98fe-e36617b49c92"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ed2d000b-67fd-4535-b941-be538642382f"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.ed2d000b-67fd-4535-b941-be538642382f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3043e56d-2edd-4137-9d4e-459f278eea33"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.3043e56d-2edd-4137-9d4e-459f278eea33"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.601c0051-28b7-4336-b73e-89fcff107fe3"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.601c0051-28b7-4336-b73e-89fcff107fe3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.445a6058-7853-4097-94c1-0bde01702c3a"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.445a6058-7853-4097-94c1-0bde01702c3a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.851f880a-43d1-4a98-9a44-e8cca847ceef"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.851f880a-43d1-4a98-9a44-e8cca847ceef"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2ed3031e-6dde-4e2d-8eb2-a6b19a726e70"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.2ed3031e-6dde-4e2d-8eb2-a6b19a726e70"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.787ee0ca-e025-4c0f-8ded-a393295b6006"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.787ee0ca-e025-4c0f-8ded-a393295b6006"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.06a74ae3-1be6-44d4-90d9-2687b419d392"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.06a74ae3-1be6-44d4-90d9-2687b419d392"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.fdcca9e6-b8ed-484c-8ce5-9301c9f5cbd5"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.fdcca9e6-b8ed-484c-8ce5-9301c9f5cbd5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9ae2303c-fd77-427a-9387-fe496f349f8f"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.9ae2303c-fd77-427a-9387-fe496f349f8f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4a0eb029-a2ad-44fa-b943-75bd5597837d"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.4a0eb029-a2ad-44fa-b943-75bd5597837d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8c5137ad-39ec-4300-8987-49627f7e56a4"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.8c5137ad-39ec-4300-8987-49627f7e56a4"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2d042d1a-f07e-4175-a720-32ec3449a24c"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.2d042d1a-f07e-4175-a720-32ec3449a24c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ece474bd-d4f2-429d-8ee3-1f9f357ebcb3"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.ece474bd-d4f2-429d-8ee3-1f9f357ebcb3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d77ce008-13d0-49be-b144-998e4009f741"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.d77ce008-13d0-49be-b144-998e4009f741"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.bb987ebf-dda6-4136-8b7a-679f7b3e37b5"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.bb987ebf-dda6-4136-8b7a-679f7b3e37b5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.fe853315-6812-4173-aa01-f6c49eedc9f8"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.fe853315-6812-4173-aa01-f6c49eedc9f8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0aadc6d5-7336-4888-ac30-70e7ad2218a9"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.0aadc6d5-7336-4888-ac30-70e7ad2218a9"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a397afb1-5fde-402e-9f31-bc4ffe45b120"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.a397afb1-5fde-402e-9f31-bc4ffe45b120"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f12a7c39-9899-4fa2-8933-b153c96de8bb"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.f12a7c39-9899-4fa2-8933-b153c96de8bb"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.567d0d55-5f69-47fa-8802-c610ee5f4cca"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.567d0d55-5f69-47fa-8802-c610ee5f4cca"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4e4b55fc-d160-4746-a411-a8e8f0a16f53"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.4e4b55fc-d160-4746-a411-a8e8f0a16f53"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2713bad7-4e3b-4794-b863-d0967510da11"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.2713bad7-4e3b-4794-b863-d0967510da11"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.92722fd6-3788-47c1-9a7c-838e75442dc8"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.92722fd6-3788-47c1-9a7c-838e75442dc8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.39216596-f1ae-46a5-8181-a26918f04bb6"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.39216596-f1ae-46a5-8181-a26918f04bb6"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2274b725-9332-43a2-8df0-19df40491c5a"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.2274b725-9332-43a2-8df0-19df40491c5a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4a056974-53df-4d01-aa5e-8a064aa379be"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.4a056974-53df-4d01-aa5e-8a064aa379be"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.cf67f0e2-7794-4403-8255-a0e6898bd7fb"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.cf67f0e2-7794-4403-8255-a0e6898bd7fb"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3bb93224-7246-4e05-9907-cc4437955731"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.3bb93224-7246-4e05-9907-cc4437955731"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7263c2bc-a895-4e72-b65f-7e22b8f2d2f6"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.7263c2bc-a895-4e72-b65f-7e22b8f2d2f6"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.fd8ff63f-ecac-413a-94f9-5bfd8a4333db"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.fd8ff63f-ecac-413a-94f9-5bfd8a4333db"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.08773f22-972c-405c-8723-00ae2e1c81c1"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.08773f22-972c-405c-8723-00ae2e1c81c1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2ef0c28c-74c0-4d03-817c-7f12d1628650"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.2ef0c28c-74c0-4d03-817c-7f12d1628650"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d26d3a59-31fe-43d5-91b9-2b773863c65a"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.d26d3a59-31fe-43d5-91b9-2b773863c65a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4547c607-6b02-4586-880b-abc4b000100c"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.4547c607-6b02-4586-880b-abc4b000100c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3e3d780f-4e46-4588-b650-730e8d68cd91"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.3e3d780f-4e46-4588-b650-730e8d68cd91"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6cad4bf5-bb89-4a2f-b5ec-8aa78a3b5dbf"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.6cad4bf5-bb89-4a2f-b5ec-8aa78a3b5dbf"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c2f7479c-634f-469d-a1f7-e0122ef6606a"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.c2f7479c-634f-469d-a1f7-e0122ef6606a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4fbdb5ea-de2c-47eb-99df-f1d504b047c0"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.4fbdb5ea-de2c-47eb-99df-f1d504b047c0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8fe2db14-2b31-4c04-97bc-bda937317302"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.8fe2db14-2b31-4c04-97bc-bda937317302"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.83978a7e-afb8-4501-9bdd-541da8f75656"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.83978a7e-afb8-4501-9bdd-541da8f75656"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.24ec08f6-a5fe-4dbd-b347-c8879c786306"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.24ec08f6-a5fe-4dbd-b347-c8879c786306"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b4ad7eaf-5cff-4ef8-900f-d23976d8e9b8"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.b4ad7eaf-5cff-4ef8-900f-d23976d8e9b8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e0f9ddf5-fab0-418d-91f9-f269e3892649"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.e0f9ddf5-fab0-418d-91f9-f269e3892649"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.411a2160-c58a-4fc8-b3ae-21227a167a7b"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.411a2160-c58a-4fc8-b3ae-21227a167a7b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8fb118e4-c405-4f5e-b16a-427ccc2710db"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.8fb118e4-c405-4f5e-b16a-427ccc2710db"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6e17f496-be02-4296-81f6-5f6d072e6966"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.6e17f496-be02-4296-81f6-5f6d072e6966"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1a950915-8158-48da-bc22-e7b124e4bb1c"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.1a950915-8158-48da-bc22-e7b124e4bb1c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.84dbdda4-35ce-4ed9-ae3d-de3258c4253d"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.84dbdda4-35ce-4ed9-ae3d-de3258c4253d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f22ef4c8-ee15-485a-b98f-eeb58a53c0e8"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.f22ef4c8-ee15-485a-b98f-eeb58a53c0e8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4c2cf725-8689-4612-a583-188f9e965b39"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.4c2cf725-8689-4612-a583-188f9e965b39"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c2d733d6-f0fa-43f2-bdbd-50795a5ffe1b"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.c2d733d6-f0fa-43f2-bdbd-50795a5ffe1b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.07c7db03-653f-4fac-83bf-888a5c6d7baf"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.07c7db03-653f-4fac-83bf-888a5c6d7baf"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.be54a64d-ca6e-4cd3-8091-ed8db3050ae8"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.be54a64d-ca6e-4cd3-8091-ed8db3050ae8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b6bfd333-bede-474b-86c7-01a9f8b0b793"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.b6bfd333-bede-474b-86c7-01a9f8b0b793"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b2a352a5-49db-4c95-9e58-f3d7f3c7f430"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.b2a352a5-49db-4c95-9e58-f3d7f3c7f430"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.90bddd6d-3b49-43cf-b0ab-22b4b8a27e67"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.90bddd6d-3b49-43cf-b0ab-22b4b8a27e67"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3270c3ed-6f85-41df-9683-8dbe9bcce158"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.3270c3ed-6f85-41df-9683-8dbe9bcce158"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a6a3aa52-b9ee-4b40-9a30-b449de050d7b"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.a6a3aa52-b9ee-4b40-9a30-b449de050d7b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d15e5efc-0cbd-4428-b604-3fb7123217b6"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.d15e5efc-0cbd-4428-b604-3fb7123217b6"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.723c740e-5777-46a3-955b-ec6710b74f68"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.723c740e-5777-46a3-955b-ec6710b74f68"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.de066e54-ff37-4d65-88d0-802dbfbe5102"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.de066e54-ff37-4d65-88d0-802dbfbe5102"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d42900bf-7397-4cdc-8194-930db0f3c036"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.d42900bf-7397-4cdc-8194-930db0f3c036"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5d9a5559-d2b3-4ab4-a86a-48a0d0d3b3cb"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.5d9a5559-d2b3-4ab4-a86a-48a0d0d3b3cb"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8fe1a19b-55f9-427d-84d7-db63b6366544"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.8fe1a19b-55f9-427d-84d7-db63b6366544"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9d900d5f-b042-4055-92d1-300cf14c9ea1"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.9d900d5f-b042-4055-92d1-300cf14c9ea1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.47d9b524-8a58-4c19-977a-91be0a4ddc40"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.47d9b524-8a58-4c19-977a-91be0a4ddc40"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c55ae41e-ed71-4557-aa93-aa91823f23e7"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.c55ae41e-ed71-4557-aa93-aa91823f23e7"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9da5039e-b15d-4253-ba61-025e5352b756"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.9da5039e-b15d-4253-ba61-025e5352b756"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ec76338f-4ece-4197-b544-66a611d1d584"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.ec76338f-4ece-4197-b544-66a611d1d584"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.76468671-d7e4-4b00-9dbb-bfa7d7c88e76"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.76468671-d7e4-4b00-9dbb-bfa7d7c88e76"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e0cb791e-f74c-4413-9feb-25a31fafba77"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.e0cb791e-f74c-4413-9feb-25a31fafba77"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.41516361-de31-4afa-bf0c-e590da0b6bda"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.41516361-de31-4afa-bf0c-e590da0b6bda"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ac61e40e-aab3-4f1f-8cd6-5de9ffbcec81"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.ac61e40e-aab3-4f1f-8cd6-5de9ffbcec81"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.11097e4b-7d9c-4051-b075-ef81c2819389"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.11097e4b-7d9c-4051-b075-ef81c2819389"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5413a530-588d-40e4-9978-e49829932f38"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.5413a530-588d-40e4-9978-e49829932f38"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.eef69390-ad0b-4676-ba65-a6b1294efe50"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.eef69390-ad0b-4676-ba65-a6b1294efe50"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b32d5706-fc38-4e37-8d96-a866982609c2"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.b32d5706-fc38-4e37-8d96-a866982609c2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.58b348ae-c827-44e6-9176-03548da6e5a6"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.58b348ae-c827-44e6-9176-03548da6e5a6"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2711dcfc-282b-4e64-af17-b71ca5a119fc"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.2711dcfc-282b-4e64-af17-b71ca5a119fc"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a99a5e7f-3e44-4c5c-820d-b98bf7bd569a"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.a99a5e7f-3e44-4c5c-820d-b98bf7bd569a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.fb23b7ef-c5d7-4c77-bc2a-1986478001a2"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.fb23b7ef-c5d7-4c77-bc2a-1986478001a2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.21cf18c3-d61e-42bf-8496-cfeaae78c3db"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.21cf18c3-d61e-42bf-8496-cfeaae78c3db"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2b8f022e-6d77-4ab0-8132-a50cf03699ff"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.2b8f022e-6d77-4ab0-8132-a50cf03699ff"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f214f688-2949-4832-8c3d-82e9e6c77da3"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.f214f688-2949-4832-8c3d-82e9e6c77da3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ee600034-f1dd-40c2-a1b2-6a1dd66a6a21"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.ee600034-f1dd-40c2-a1b2-6a1dd66a6a21"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.38fa3928-fdf1-4211-91fa-a1642560d19d"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.38fa3928-fdf1-4211-91fa-a1642560d19d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.33e76194-e721-4514-a3d4-7aa3aa9ca21d"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.33e76194-e721-4514-a3d4-7aa3aa9ca21d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.02d3c428-088e-402a-acb9-d5749805edac"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.02d3c428-088e-402a-acb9-d5749805edac"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a462d9cb-5a1d-4c79-b843-fcc88b333293"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.a462d9cb-5a1d-4c79-b843-fcc88b333293"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c8b8d983-4ac5-48fc-8382-c11979ecafca"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.c8b8d983-4ac5-48fc-8382-c11979ecafca"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7fd76a71-131e-420f-8fd1-0c9d5672b925"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.7fd76a71-131e-420f-8fd1-0c9d5672b925"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.76b87519-278c-44ad-b7c0-5e0fad363586"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.76b87519-278c-44ad-b7c0-5e0fad363586"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a7e6bbb9-1233-4ff9-ac97-c5ab349cc0cd"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.a7e6bbb9-1233-4ff9-ac97-c5ab349cc0cd"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.791bf8ee-1589-4a32-8303-3e48d75fbf14"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.791bf8ee-1589-4a32-8303-3e48d75fbf14"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.aee8d6f6-baaf-46ec-990b-52588d5e7289"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.aee8d6f6-baaf-46ec-990b-52588d5e7289"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ab44c1ed-6e09-40e2-a11f-73654d176ac3"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.ab44c1ed-6e09-40e2-a11f-73654d176ac3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f2bd582d-8853-4cf4-9f9f-1378a4b2c9bf"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.f2bd582d-8853-4cf4-9f9f-1378a4b2c9bf"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d743e880-1212-4061-8cc9-bf00c12a90b2"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.d743e880-1212-4061-8cc9-bf00c12a90b2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5ffcf7b8-c757-4a3a-a2e1-ab46f8a2d91a"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.5ffcf7b8-c757-4a3a-a2e1-ab46f8a2d91a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9ae4e4f0-5f82-4496-b644-cfefcf4496a4"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.9ae4e4f0-5f82-4496-b644-cfefcf4496a4"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.128d9f62-5383-49c8-bd4f-e6bbbd067b88"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.128d9f62-5383-49c8-bd4f-e6bbbd067b88"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7326b689-c04c-424f-9fd1-f1bbabb9ca58"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.7326b689-c04c-424f-9fd1-f1bbabb9ca58"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2a41dd38-6120-471d-bf35-05d6489f4f27"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.2a41dd38-6120-471d-bf35-05d6489f4f27"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d80520f3-c79a-433b-9279-4830c0374b01"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.d80520f3-c79a-433b-9279-4830c0374b01"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4650c890-c63e-42c8-ab1b-e2ed7b6eeb9a"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.4650c890-c63e-42c8-ab1b-e2ed7b6eeb9a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.03863f76-c90c-4153-ac89-6c88aa81b15a"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.03863f76-c90c-4153-ac89-6c88aa81b15a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5c38993a-17f5-43b3-9bce-5538eb3b935d"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.5c38993a-17f5-43b3-9bce-5538eb3b935d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a5cc9e54-b238-4398-a500-40c845e2d8ac"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.a5cc9e54-b238-4398-a500-40c845e2d8ac"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.828b3906-74f5-4a35-8225-89e70cd2fd46"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.828b3906-74f5-4a35-8225-89e70cd2fd46"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.63d95926-c886-4e40-aa6b-235a2415f245"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.63d95926-c886-4e40-aa6b-235a2415f245"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.665024c3-22d1-439a-8c11-7a323da3bb21"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.665024c3-22d1-439a-8c11-7a323da3bb21"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.de70aa65-39cd-459e-a471-acc9680862c0"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.de70aa65-39cd-459e-a471-acc9680862c0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.19199d88-f215-438e-b8b5-4da9b2df1ee5"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.19199d88-f215-438e-b8b5-4da9b2df1ee5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b7aca6a4-594f-437e-8206-265e9c099b1a"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.b7aca6a4-594f-437e-8206-265e9c099b1a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6d4804cc-b302-4938-bce6-b37ed6eeafbf"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.6d4804cc-b302-4938-bce6-b37ed6eeafbf"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.74b8d704-9dbd-4c76-bc63-80d89a093a51"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.74b8d704-9dbd-4c76-bc63-80d89a093a51"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6b3b228d-a250-436a-8ffd-4b49cc471583"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.6b3b228d-a250-436a-8ffd-4b49cc471583"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.487b9688-5f04-43d0-964e-e4150519498b"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.487b9688-5f04-43d0-964e-e4150519498b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ef32acdc-4576-4cad-a0b2-78b5be5182df"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.ef32acdc-4576-4cad-a0b2-78b5be5182df"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f75f4769-f6b4-416d-b6d2-8cf57e3096de"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.f75f4769-f6b4-416d-b6d2-8cf57e3096de"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b0604a97-3712-478d-a899-154764775590"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.b0604a97-3712-478d-a899-154764775590"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.fd9defd0-c0e4-447e-a149-a989b3dcc42a"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.fd9defd0-c0e4-447e-a149-a989b3dcc42a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.600464a3-969a-4e4a-8615-13ee0f46760a"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.600464a3-969a-4e4a-8615-13ee0f46760a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c0e6d8af-c4c3-46f0-a521-1ccf65595510"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.c0e6d8af-c4c3-46f0-a521-1ccf65595510"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4592e541-ec81-44b7-9980-1bcd2b64a849"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.4592e541-ec81-44b7-9980-1bcd2b64a849"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a8ecef4e-9490-4153-8625-5dd27442681b"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.a8ecef4e-9490-4153-8625-5dd27442681b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a5a23fdb-254d-41b0-a8e0-35d376738b23"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.a5a23fdb-254d-41b0-a8e0-35d376738b23"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b86ad228-29ad-49c6-88d8-b2d0bbf62341"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.b86ad228-29ad-49c6-88d8-b2d0bbf62341"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7ed2ff37-5c34-4185-a0e3-65b969c12efa"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.7ed2ff37-5c34-4185-a0e3-65b969c12efa"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c7a7ec0b-4e69-4524-86cd-d7084facdbe5"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.c7a7ec0b-4e69-4524-86cd-d7084facdbe5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7b6f7d15-9e5f-4e66-bec4-7a100fa485a4"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.7b6f7d15-9e5f-4e66-bec4-7a100fa485a4"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9fbfef04-2732-42d0-b489-37065aad05d4"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.9fbfef04-2732-42d0-b489-37065aad05d4"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.68335d89-9888-4bde-9706-e8426a4ef5e6"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.68335d89-9888-4bde-9706-e8426a4ef5e6"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.755bb61f-831c-42db-a2cc-676a0a382b3a"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.755bb61f-831c-42db-a2cc-676a0a382b3a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.20925e93-eaf6-4605-8af4-d676597fd642"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.20925e93-eaf6-4605-8af4-d676597fd642"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.127d2d88-1497-4c0d-bfff-ea6949c9f371"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.127d2d88-1497-4c0d-bfff-ea6949c9f371"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b3c0bcaa-052e-4de7-9dfa-8430e4ebf3f8"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.b3c0bcaa-052e-4de7-9dfa-8430e4ebf3f8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.bbbcb1ab-e94e-4266-b26d-d547fa440208"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.bbbcb1ab-e94e-4266-b26d-d547fa440208"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.400cc539-a766-45c7-96f0-355ed7a92dd4"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.400cc539-a766-45c7-96f0-355ed7a92dd4"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e0251500-7790-4516-8bdf-1ee8ab1c058d"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.e0251500-7790-4516-8bdf-1ee8ab1c058d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.157bc805-839e-4400-b4c8-cb0e3f255975"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.157bc805-839e-4400-b4c8-cb0e3f255975"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.75c8ad6e-c87b-44d9-b466-0897ce5c0649"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.75c8ad6e-c87b-44d9-b466-0897ce5c0649"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1ea3464a-8d54-4de6-a2aa-4de9a057de40"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.1ea3464a-8d54-4de6-a2aa-4de9a057de40"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ce173da4-b7eb-4ba1-9af7-5f06a9b388b2"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.ce173da4-b7eb-4ba1-9af7-5f06a9b388b2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.384e2576-3670-4e5c-aa76-bb3a41648f18"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.384e2576-3670-4e5c-aa76-bb3a41648f18"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.69085969-6745-4a1c-a706-0e4e735fa287"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.69085969-6745-4a1c-a706-0e4e735fa287"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.da034684-3aa8-4838-a352-d6d243342627"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.da034684-3aa8-4838-a352-d6d243342627"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6e1e910c-9bfc-4ec5-bb54-a2fc5a99285e"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.6e1e910c-9bfc-4ec5-bb54-a2fc5a99285e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.be6b3327-a472-4afe-bc20-feff59a923a2"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.be6b3327-a472-4afe-bc20-feff59a923a2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9e067da2-54ca-43d7-8856-969525fc20ff"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.9e067da2-54ca-43d7-8856-969525fc20ff"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.67609350-09d9-426c-bdf1-f94ea5563385"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.67609350-09d9-426c-bdf1-f94ea5563385"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.57d4b45e-690b-4b5e-86c7-f82b99e43140"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.57d4b45e-690b-4b5e-86c7-f82b99e43140"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ae650c7e-fb4a-4aae-abab-192088843600"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.ae650c7e-fb4a-4aae-abab-192088843600"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.491541bc-f550-4f0c-9aab-5af0a0f9d3ec"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.491541bc-f550-4f0c-9aab-5af0a0f9d3ec"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9e8872c9-a44f-4dda-ace9-85bdc7b44617"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.9e8872c9-a44f-4dda-ace9-85bdc7b44617"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d6ed530b-0f73-466e-a499-87d0e2a3feea"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.d6ed530b-0f73-466e-a499-87d0e2a3feea"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f114d4e3-ba45-4ee2-95b1-2f216b5cceaa"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.f114d4e3-ba45-4ee2-95b1-2f216b5cceaa"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7c66a3d6-4773-4d69-ab18-cce69f247750"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.7c66a3d6-4773-4d69-ab18-cce69f247750"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.12608799-3c0c-4096-b224-74861580f6f8"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.12608799-3c0c-4096-b224-74861580f6f8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.592784cf-07a0-437e-a47f-43f76a79dcde"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.592784cf-07a0-437e-a47f-43f76a79dcde"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.55286dd2-fb11-475a-bb08-dead2227a096"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.55286dd2-fb11-475a-bb08-dead2227a096"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.fb855eeb-5c58-489f-a20b-c6428f912be7"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.fb855eeb-5c58-489f-a20b-c6428f912be7"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.874e22db-86df-4a4f-bc60-2bd6736e246e"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.874e22db-86df-4a4f-bc60-2bd6736e246e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ea910c6f-e81a-439a-8399-eb2bc1e4ecc5"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.ea910c6f-e81a-439a-8399-eb2bc1e4ecc5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e574f26a-9b81-49f4-9b13-8d5c06e28130"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.e574f26a-9b81-49f4-9b13-8d5c06e28130"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.67834b9b-2e90-45b4-9cd4-a415bf487cb5"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.67834b9b-2e90-45b4-9cd4-a415bf487cb5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.304c77a8-2507-49ab-8053-2dd15d010d81"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.304c77a8-2507-49ab-8053-2dd15d010d81"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.549642ad-f334-44b7-ab48-eaff73aae535"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.549642ad-f334-44b7-ab48-eaff73aae535"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b04aea02-5d5c-4321-a75c-9a10cd04192e"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.b04aea02-5d5c-4321-a75c-9a10cd04192e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5bf332ec-fb37-4b80-8bbd-aedb89b4fe3a"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.5bf332ec-fb37-4b80-8bbd-aedb89b4fe3a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8958c8a0-3ad7-4127-94e0-544d8ee80f9e"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.8958c8a0-3ad7-4127-94e0-544d8ee80f9e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2b9e8bfc-62d3-4e21-a984-3f48eb8cf587"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.2b9e8bfc-62d3-4e21-a984-3f48eb8cf587"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c4856ab5-c599-4dfb-b3ac-a77f9e822624"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.c4856ab5-c599-4dfb-b3ac-a77f9e822624"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.38ddd5fe-3d4d-4393-b76e-10121c36a973"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.38ddd5fe-3d4d-4393-b76e-10121c36a973"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c7755b9c-8fae-4e7d-87ef-48dc2f16170c"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.c7755b9c-8fae-4e7d-87ef-48dc2f16170c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0d6d81f8-9634-40b6-99e7-1206d69b1178"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.0d6d81f8-9634-40b6-99e7-1206d69b1178"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.cbe6a2a6-f9b7-4c82-823a-82b35a303103"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.cbe6a2a6-f9b7-4c82-823a-82b35a303103"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.59ceb7d2-d602-4112-9a4e-fc1546184e7c"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.59ceb7d2-d602-4112-9a4e-fc1546184e7c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0c74ad25-f221-459c-8db4-5ae0ba9e8dde"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.0c74ad25-f221-459c-8db4-5ae0ba9e8dde"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.546b116a-3215-4ee0-9922-94ca0696b25a"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.546b116a-3215-4ee0-9922-94ca0696b25a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ad563158-49f6-4d4b-a278-a9913f99742a"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.ad563158-49f6-4d4b-a278-a9913f99742a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2bc9731c-50cb-4bef-9006-08f9876d7338"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.2bc9731c-50cb-4bef-9006-08f9876d7338"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.22e82a83-986d-4619-ba54-4a2fcf7195e8"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.22e82a83-986d-4619-ba54-4a2fcf7195e8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2499ec88-4350-4771-af0f-d88c2cc2dab2"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.2499ec88-4350-4771-af0f-d88c2cc2dab2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.621b12be-1255-4fb7-b8ea-35f65946456e"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.621b12be-1255-4fb7-b8ea-35f65946456e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d1457a39-c70e-4cb7-a81a-60a8205235c4"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.d1457a39-c70e-4cb7-a81a-60a8205235c4"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ae8c49fd-f721-4b85-83fc-504a3a16059d"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.ae8c49fd-f721-4b85-83fc-504a3a16059d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b4f92876-9442-4e42-b9ef-471d686d30d3"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.b4f92876-9442-4e42-b9ef-471d686d30d3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3340e42e-94ad-4c42-ae1a-0a245f0ee7fb"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.3340e42e-94ad-4c42-ae1a-0a245f0ee7fb"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.aa3b1627-d4e2-47db-a7c6-e8f30a65eb53"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.aa3b1627-d4e2-47db-a7c6-e8f30a65eb53"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f1213b14-0cb1-4b09-8699-355e1f4752ad"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.f1213b14-0cb1-4b09-8699-355e1f4752ad"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5ebb3092-b9d7-4951-9849-901912f8a6e4"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.5ebb3092-b9d7-4951-9849-901912f8a6e4"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7ca33fb4-4542-409a-9f55-296e6b6983d5"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.7ca33fb4-4542-409a-9f55-296e6b6983d5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a32f7375-eb90-430d-9ccd-b6ed19f88558"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.a32f7375-eb90-430d-9ccd-b6ed19f88558"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c13d9835-10ad-4f01-946d-d38c677b5ae1"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.c13d9835-10ad-4f01-946d-d38c677b5ae1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.fbcc1db4-18e0-4d3a-8c47-014a964f869e"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.fbcc1db4-18e0-4d3a-8c47-014a964f869e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.58790343-157b-4f57-b2f6-24b87c6b365e"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.58790343-157b-4f57-b2f6-24b87c6b365e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0c2cb5be-97df-4d0b-8048-d43ea16939d3"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.0c2cb5be-97df-4d0b-8048-d43ea16939d3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.879ef1d5-36e5-4417-b4cd-d7e268289b75"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.879ef1d5-36e5-4417-b4cd-d7e268289b75"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.78d55aa5-de45-4e77-97b5-0f05179b69f7"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.78d55aa5-de45-4e77-97b5-0f05179b69f7"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.acc5e7f2-4568-463f-916a-4e2beefd9898"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.acc5e7f2-4568-463f-916a-4e2beefd9898"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.52e22308-f0eb-4128-b8cf-201c413a9696"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.52e22308-f0eb-4128-b8cf-201c413a9696"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.130ae640-949f-4bb5-b970-f5078e4cdb0a"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.130ae640-949f-4bb5-b970-f5078e4cdb0a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.cb8fe276-7a88-4176-b076-1b75d8361265"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.cb8fe276-7a88-4176-b076-1b75d8361265"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d1caba77-80d7-484a-bf8e-0480cd5b9741"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.d1caba77-80d7-484a-bf8e-0480cd5b9741"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4648d7a5-6b38-4834-a866-e2f7ea73688d"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.4648d7a5-6b38-4834-a866-e2f7ea73688d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9831034b-14de-486c-b06e-45dd0ee17fbf"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.9831034b-14de-486c-b06e-45dd0ee17fbf"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7db36bcc-5097-4a66-b386-58abe87c1604"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.7db36bcc-5097-4a66-b386-58abe87c1604"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7e146f99-9250-4850-a3ba-21e9b0f3cfdb"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.7e146f99-9250-4850-a3ba-21e9b0f3cfdb"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.59730449-d2a9-46a1-8665-e0eaa19dd8a4"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.59730449-d2a9-46a1-8665-e0eaa19dd8a4"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2cbd4058-9cb5-44f1-9d24-969750e84f01"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.2cbd4058-9cb5-44f1-9d24-969750e84f01"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ed773d33-49e7-47ee-90bd-18e33b9ffc29"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.ed773d33-49e7-47ee-90bd-18e33b9ffc29"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.dd625303-f1c8-4739-8572-6100c7af95af"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.dd625303-f1c8-4739-8572-6100c7af95af"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d08f25e3-6743-432f-9968-8e1f586523cd"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.d08f25e3-6743-432f-9968-8e1f586523cd"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6bb8d1c8-13fb-40c6-9ad5-b6e1017e6bb8"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.6bb8d1c8-13fb-40c6-9ad5-b6e1017e6bb8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d4d288f8-ade2-4479-92e0-e6ed0ebd7e96"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.d4d288f8-ade2-4479-92e0-e6ed0ebd7e96"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.91ec4cd6-b5a9-4d0f-95a3-4ec651a7c36b"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.91ec4cd6-b5a9-4d0f-95a3-4ec651a7c36b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c264d65f-9b5e-43a9-8e73-1f868abc1102"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.c264d65f-9b5e-43a9-8e73-1f868abc1102"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6702c6c4-1064-485c-87b1-3ed2a25bc859"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.6702c6c4-1064-485c-87b1-3ed2a25bc859"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.98d2a69b-7eda-49dc-a091-9d9820a57a6e"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.98d2a69b-7eda-49dc-a091-9d9820a57a6e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.722ccd98-832c-443e-8b7a-603ab8e32665"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.722ccd98-832c-443e-8b7a-603ab8e32665"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b449afea-1cf4-4c68-bb34-2570e821daf5"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.b449afea-1cf4-4c68-bb34-2570e821daf5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.552f30c0-fa98-4a1d-8850-c31974c5e95d"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.552f30c0-fa98-4a1d-8850-c31974c5e95d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.17f84b65-8e65-44c4-8fde-cfdb467c8df9"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.17f84b65-8e65-44c4-8fde-cfdb467c8df9"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c7a2de21-cd82-4d22-a984-b0867970fa5d"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.c7a2de21-cd82-4d22-a984-b0867970fa5d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.299b9e86-aae4-4500-aa2d-ea5f81e71444"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.299b9e86-aae4-4500-aa2d-ea5f81e71444"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.cb513880-5ebc-4934-9a57-6102026981fd"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.cb513880-5ebc-4934-9a57-6102026981fd"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.bf380f09-1040-4fa3-b877-abe4d3e098b7"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.bf380f09-1040-4fa3-b877-abe4d3e098b7"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b278d573-ad46-4355-92b1-99f030cdb750"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.b278d573-ad46-4355-92b1-99f030cdb750"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a39112d4-4319-42a6-99cb-f845a6ed5050"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.a39112d4-4319-42a6-99cb-f845a6ed5050"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5b0a408e-f79b-4f56-95db-a6999689aba6"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.5b0a408e-f79b-4f56-95db-a6999689aba6"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d9a919f2-8036-454e-aef6-d03a7768d414"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.d9a919f2-8036-454e-aef6-d03a7768d414"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.58ad51c1-154d-4d50-994d-2d0b29112b1e"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.58ad51c1-154d-4d50-994d-2d0b29112b1e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.bebecb3b-ad49-437a-bdab-b73b2096ff95"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.bebecb3b-ad49-437a-bdab-b73b2096ff95"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a1ac8d35-fcc2-4581-9efa-9367451124f2"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.a1ac8d35-fcc2-4581-9efa-9367451124f2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b8b8ef73-1830-455d-a3fc-f363a3b3324b"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.b8b8ef73-1830-455d-a3fc-f363a3b3324b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e20a07e6-e30c-470b-9c5f-4e9e34888567"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.e20a07e6-e30c-470b-9c5f-4e9e34888567"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1d0f0c43-3a56-416a-8d2a-6563aea4dc13"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.1d0f0c43-3a56-416a-8d2a-6563aea4dc13"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f72bcbd7-6975-465b-93a0-3d14628e33ba"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.f72bcbd7-6975-465b-93a0-3d14628e33ba"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d633b265-859e-4fe0-a03c-fd4d3e48de91"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.d633b265-859e-4fe0-a03c-fd4d3e48de91"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a159eb9c-116f-45d1-b2ff-879f83ba3e89"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.a159eb9c-116f-45d1-b2ff-879f83ba3e89"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.591fce97-20cf-4499-ba87-d2f7e2011d51"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.591fce97-20cf-4499-ba87-d2f7e2011d51"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1bbfc6fc-f318-44a5-b31a-ca216e983c0f"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.1bbfc6fc-f318-44a5-b31a-ca216e983c0f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.933f2c9f-77a8-481b-b3d8-687c3696fa76"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.933f2c9f-77a8-481b-b3d8-687c3696fa76"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.80cb1367-8eb9-415d-a9ab-d13683a2caf7"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.80cb1367-8eb9-415d-a9ab-d13683a2caf7"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.811faf8f-da66-4147-b2cf-15eb6ac66e0d"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.811faf8f-da66-4147-b2cf-15eb6ac66e0d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3af056ad-7530-4c5d-a36a-b3fd16599b80"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.3af056ad-7530-4c5d-a36a-b3fd16599b80"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.419f0eb2-182d-44b3-bdfd-f8745f953d0c"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.419f0eb2-182d-44b3-bdfd-f8745f953d0c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e00a1790-0bc5-455a-9f1c-9c38afcc7805"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.e00a1790-0bc5-455a-9f1c-9c38afcc7805"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a410e9f0-754f-4933-bd5a-c20881e1c796"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.a410e9f0-754f-4933-bd5a-c20881e1c796"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7ff25548-5c3a-4c8d-9d2e-f4d16356f26c"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.7ff25548-5c3a-4c8d-9d2e-f4d16356f26c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ba2391e4-a481-4154-bdd8-522660ffe6bb"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.ba2391e4-a481-4154-bdd8-522660ffe6bb"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.220c5b93-950a-4897-9506-fccad02aa5d7"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.220c5b93-950a-4897-9506-fccad02aa5d7"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7063c0bf-630d-4569-9cb1-c7568db5c9ad"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.7063c0bf-630d-4569-9cb1-c7568db5c9ad"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a54158e9-ec7e-4a58-b5c3-278af0615da1"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.a54158e9-ec7e-4a58-b5c3-278af0615da1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f6392a42-15c7-4423-b831-173774c3abc2"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.f6392a42-15c7-4423-b831-173774c3abc2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.63a7d13b-76ad-47b3-917a-f070e141c0e0"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.63a7d13b-76ad-47b3-917a-f070e141c0e0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c5a4615c-ccdb-4051-80c7-c720952d6495"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.c5a4615c-ccdb-4051-80c7-c720952d6495"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1a4d84b1-fc7c-445e-9c27-1b2b8fd32862"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.1a4d84b1-fc7c-445e-9c27-1b2b8fd32862"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.40d492f9-2d5e-469e-955b-d77dc297c439"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.40d492f9-2d5e-469e-955b-d77dc297c439"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ee93032e-c87f-4d8e-8887-d2518530b57a"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.ee93032e-c87f-4d8e-8887-d2518530b57a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b13e5046-0f20-450c-a512-abb4588839ef"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.b13e5046-0f20-450c-a512-abb4588839ef"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.28dd79ff-d941-405c-b4c1-dac85be115b5"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.28dd79ff-d941-405c-b4c1-dac85be115b5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.52e1930c-fb7c-48f3-ad04-701fe910fb85"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.52e1930c-fb7c-48f3-ad04-701fe910fb85"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a53e45a3-aa16-44fb-ac0e-f78138b8b836"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.a53e45a3-aa16-44fb-ac0e-f78138b8b836"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.49a093e2-6484-4944-b6ff-1516f58806f7"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.49a093e2-6484-4944-b6ff-1516f58806f7"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b82cf951-f7bd-4136-93c4-7807e5295f1d"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.b82cf951-f7bd-4136-93c4-7807e5295f1d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f9c7f7f8-0f21-4f18-b101-b4f0a247fb4e"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.f9c7f7f8-0f21-4f18-b101-b4f0a247fb4e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.25b9e2a4-e75d-408d-aed4-aff40b3710d7"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.25b9e2a4-e75d-408d-aed4-aff40b3710d7"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6dbfd4ae-0972-48f7-b384-2b9ca5439ce1"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.6dbfd4ae-0972-48f7-b384-2b9ca5439ce1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.62916d27-919e-48c3-a2a2-89974f362a25"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.62916d27-919e-48c3-a2a2-89974f362a25"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.33acf40e-31b9-4333-a857-2593491ef5e8"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.33acf40e-31b9-4333-a857-2593491ef5e8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.032b2da2-6be2-48b5-8c6d-1aac5d632761"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.032b2da2-6be2-48b5-8c6d-1aac5d632761"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.cc1e6f5a-98d5-4ce3-8444-88c5be5ba412"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.cc1e6f5a-98d5-4ce3-8444-88c5be5ba412"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8ced1dde-6c6d-4aca-8d6c-28a7b559be23"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.8ced1dde-6c6d-4aca-8d6c-28a7b559be23"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.855410f2-c9c7-4b5e-be0a-b8484927fc38"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.855410f2-c9c7-4b5e-be0a-b8484927fc38"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d8949234-173c-470e-8124-65f0446087f5"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.d8949234-173c-470e-8124-65f0446087f5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.90b957ec-8f73-4895-b05b-2dcdcd32fed3"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.90b957ec-8f73-4895-b05b-2dcdcd32fed3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.29a09a5d-b958-4095-affc-21510bb9ab06"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.29a09a5d-b958-4095-affc-21510bb9ab06"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2558d22d-db75-4a18-b054-1afd7e2ff6a8"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.2558d22d-db75-4a18-b054-1afd7e2ff6a8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3ac9be82-d985-4be8-aa38-ee17ed75d523"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.3ac9be82-d985-4be8-aa38-ee17ed75d523"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8a9a9e02-de8c-49ac-854c-d2d3dc1ca206"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.8a9a9e02-de8c-49ac-854c-d2d3dc1ca206"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4a8967c8-f9cc-4825-966f-2a7e5277a44e"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.4a8967c8-f9cc-4825-966f-2a7e5277a44e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5075f665-c0ce-44e7-8c19-2f675899161c"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.5075f665-c0ce-44e7-8c19-2f675899161c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.fcd18adf-a0de-4fd3-ac6c-a246d8fabae0"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.fcd18adf-a0de-4fd3-ac6c-a246d8fabae0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0494e016-c75a-4918-b21f-25b31707fcc9"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.0494e016-c75a-4918-b21f-25b31707fcc9"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.545af153-73b8-49b2-a96a-082f2caa1679"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.545af153-73b8-49b2-a96a-082f2caa1679"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9207cda2-50e4-48a3-84b3-87dec9b7e4a0"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.9207cda2-50e4-48a3-84b3-87dec9b7e4a0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.cffe12c9-1e2b-4e07-9c97-1887edcee386"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.cffe12c9-1e2b-4e07-9c97-1887edcee386"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.13dc597e-37e5-44a1-813e-e3b2ff9692d5"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.13dc597e-37e5-44a1-813e-e3b2ff9692d5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0916c22b-1f61-47ee-b71c-6b87f69f3faf"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.0916c22b-1f61-47ee-b71c-6b87f69f3faf"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.aa04d09a-a636-46b1-81b5-51855e7bfafb"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.aa04d09a-a636-46b1-81b5-51855e7bfafb"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b455bfe7-7d95-45fc-9aae-d0116d7fe47c"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.b455bfe7-7d95-45fc-9aae-d0116d7fe47c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2962aef7-4b8f-404a-b242-e293f0348738"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.2962aef7-4b8f-404a-b242-e293f0348738"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.11d1b2d0-ab0c-40dd-98b8-2d171388cb4b"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.11d1b2d0-ab0c-40dd-98b8-2d171388cb4b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.dd71fd20-bb81-4e2b-8a87-8640228ca9a0"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.dd71fd20-bb81-4e2b-8a87-8640228ca9a0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.fbb61e5c-c4aa-4ed0-81bd-570241f74f17"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.fbb61e5c-c4aa-4ed0-81bd-570241f74f17"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f388a217-e6ea-47e5-a6aa-d32b6e2b22a3"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.f388a217-e6ea-47e5-a6aa-d32b6e2b22a3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9ff99c3c-557d-4fd2-820a-0def86ff1de6"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.9ff99c3c-557d-4fd2-820a-0def86ff1de6"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4372b16d-adf4-41fe-98bc-7631332eebc3"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.4372b16d-adf4-41fe-98bc-7631332eebc3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2fd9b904-9bea-419f-b2c4-f7f780de524f"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.2fd9b904-9bea-419f-b2c4-f7f780de524f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.90c91310-f566-4f57-8e63-518b9ff8b866"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.90c91310-f566-4f57-8e63-518b9ff8b866"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.114e0edd-fd87-4a46-af01-5869a8653b6b"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.114e0edd-fd87-4a46-af01-5869a8653b6b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c87a4366-359d-46af-ad5b-e10db4e0c4d9"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.c87a4366-359d-46af-ad5b-e10db4e0c4d9"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.154774f1-91eb-4e1a-a093-b7fe9ad3da7c"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.154774f1-91eb-4e1a-a093-b7fe9ad3da7c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2bb61dac-a863-48f9-9158-c1116cca43d0"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.2bb61dac-a863-48f9-9158-c1116cca43d0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3b01b642-892a-4137-81bd-2043722cad09"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.3b01b642-892a-4137-81bd-2043722cad09"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f50f9a3a-7434-47d9-9906-84e592480d72"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.f50f9a3a-7434-47d9-9906-84e592480d72"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a2fc53c2-f21a-4b01-aeba-ec309b1e86e3"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.a2fc53c2-f21a-4b01-aeba-ec309b1e86e3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.81e577e7-0414-4136-9f4a-9190fd9968ec"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.81e577e7-0414-4136-9f4a-9190fd9968ec"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b35713f7-d7d2-4ac0-a2a3-0d7f558a6f11"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.b35713f7-d7d2-4ac0-a2a3-0d7f558a6f11"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.44222720-acaf-4998-a8d2-1c128e0e2ecf"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.44222720-acaf-4998-a8d2-1c128e0e2ecf"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.801a5529-aedb-4043-b97a-dde80f128c27"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.801a5529-aedb-4043-b97a-dde80f128c27"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.fb980e54-3eac-491c-8981-f8a7ede6198b"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.fb980e54-3eac-491c-8981-f8a7ede6198b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.531ee204-be0a-4282-8eb4-603f4eeed1ea"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.531ee204-be0a-4282-8eb4-603f4eeed1ea"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.96e9cc07-fffb-458d-b188-b77f0ebebfe0"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.96e9cc07-fffb-458d-b188-b77f0ebebfe0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0e9dcdb3-cbdd-47a3-a03e-5190347aa049"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.0e9dcdb3-cbdd-47a3-a03e-5190347aa049"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4143a529-5cec-4ab3-b9b8-b715885e647e"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.4143a529-5cec-4ab3-b9b8-b715885e647e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.23665905-610c-4302-b503-f00f82cf6cf9"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.23665905-610c-4302-b503-f00f82cf6cf9"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.02fcfa28-cd9a-47dd-94de-b4190724d431"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.02fcfa28-cd9a-47dd-94de-b4190724d431"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.25743c4a-59be-4807-a0b2-b3c3058869a0"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.25743c4a-59be-4807-a0b2-b3c3058869a0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.598fa6b8-62a0-46e6-beee-66851152e89c"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.598fa6b8-62a0-46e6-beee-66851152e89c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.45511b87-231f-40cb-9762-3e393bbf656c"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.45511b87-231f-40cb-9762-3e393bbf656c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.58d2e7f5-0f70-4877-87d6-f96635eb9d6e"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.58d2e7f5-0f70-4877-87d6-f96635eb9d6e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f22930d3-11eb-4b51-a7d5-4f68564c08d2"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.f22930d3-11eb-4b51-a7d5-4f68564c08d2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0f9d8790-34be-4d66-8012-e2d66b472317"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.0f9d8790-34be-4d66-8012-e2d66b472317"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.64d35a8e-535b-4c73-a484-bc45dee6bcbc"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.64d35a8e-535b-4c73-a484-bc45dee6bcbc"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a9544827-32fd-4877-8f76-22d570b3dc78"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.a9544827-32fd-4877-8f76-22d570b3dc78"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.cb6ed6e4-a4eb-4d5a-9d04-b460c71c33fd"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.cb6ed6e4-a4eb-4d5a-9d04-b460c71c33fd"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0728ee6f-a38d-4ade-8806-c6f481e7c71e"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.0728ee6f-a38d-4ade-8806-c6f481e7c71e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8d33304e-633f-4e6d-b22a-dc49cc6484ba"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.8d33304e-633f-4e6d-b22a-dc49cc6484ba"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f0dce47a-ce23-411d-b30b-5ab8e2941b3f"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.f0dce47a-ce23-411d-b30b-5ab8e2941b3f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d125a016-585f-4ed7-b7e7-c954002fd701"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.d125a016-585f-4ed7-b7e7-c954002fd701"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c9dbe1e6-e3f0-4e5d-af74-fe3f2371299a"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.c9dbe1e6-e3f0-4e5d-af74-fe3f2371299a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.bcf627a9-6d7b-4276-accb-e15e9152d8e3"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.bcf627a9-6d7b-4276-accb-e15e9152d8e3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.fdf6a51a-0a02-4107-89f6-08cebc65b7a5"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.fdf6a51a-0a02-4107-89f6-08cebc65b7a5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0b486107-18f4-4a7a-ae5f-b7b735f00567"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.0b486107-18f4-4a7a-ae5f-b7b735f00567"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.51c2e938-9c19-44c7-acd1-283b300b296d"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.51c2e938-9c19-44c7-acd1-283b300b296d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e35d558a-a6e8-4597-a64a-d3b3014a219b"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.e35d558a-a6e8-4597-a64a-d3b3014a219b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a7aadeda-010e-44d7-8ddf-177cd94faf78"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.a7aadeda-010e-44d7-8ddf-177cd94faf78"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e08eb978-6a35-420d-b778-fc88edfe7e7c"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.e08eb978-6a35-420d-b778-fc88edfe7e7c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.264f6dfd-75f6-48e6-a72d-f730d47457e2"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.264f6dfd-75f6-48e6-a72d-f730d47457e2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4bec99e7-cc30-4319-b4fa-fbab485e178d"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.4bec99e7-cc30-4319-b4fa-fbab485e178d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.44970e4d-19de-4e94-8c4c-0eb4ae54d7b1"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.44970e4d-19de-4e94-8c4c-0eb4ae54d7b1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.26409998-adc2-4d26-b872-07d3b7ecb9eb"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.26409998-adc2-4d26-b872-07d3b7ecb9eb"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.476eb3d1-7c09-409a-8eab-52f371c92bbb"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.476eb3d1-7c09-409a-8eab-52f371c92bbb"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.00eca89c-1ad9-4360-a2a9-6f45313668b7"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.00eca89c-1ad9-4360-a2a9-6f45313668b7"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6926a25c-85a4-49f2-a0ee-5b17831ba761"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.6926a25c-85a4-49f2-a0ee-5b17831ba761"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ec722836-27a0-4bb4-93d6-d974ddda3803"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.ec722836-27a0-4bb4-93d6-d974ddda3803"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.54b31073-217d-4a6b-8a4c-76d544a9ab01"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.54b31073-217d-4a6b-8a4c-76d544a9ab01"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3453dcf7-a23b-4247-9e08-2cc94286164b"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.3453dcf7-a23b-4247-9e08-2cc94286164b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1a837800-acbc-4bef-97f1-3dc70f920980"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.1a837800-acbc-4bef-97f1-3dc70f920980"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d5278ab4-afa1-477e-93ab-56c89e175c93"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.d5278ab4-afa1-477e-93ab-56c89e175c93"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e50fee74-7d0b-44d4-853d-9b3c315d231b"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.e50fee74-7d0b-44d4-853d-9b3c315d231b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2b2184e3-2c8b-41ad-8493-d988d788ac43"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.2b2184e3-2c8b-41ad-8493-d988d788ac43"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4b2873e3-ef7a-4b4a-9dff-e714165892fc"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.4b2873e3-ef7a-4b4a-9dff-e714165892fc"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.01e3c0d7-78ad-4fdf-8778-52612fe397f5"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.01e3c0d7-78ad-4fdf-8778-52612fe397f5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4680918c-4506-4b11-b771-c68490e6b980"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.4680918c-4506-4b11-b771-c68490e6b980"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.bcfc8a20-6bd5-4fbc-b217-0105b6420ff3"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.bcfc8a20-6bd5-4fbc-b217-0105b6420ff3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9f7ff9a8-f648-4bd3-9506-91f38ed512f0"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.9f7ff9a8-f648-4bd3-9506-91f38ed512f0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.74d7e449-1f7a-466a-a9d3-95984f9dafd2"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.74d7e449-1f7a-466a-a9d3-95984f9dafd2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.54fb0544-8b4e-4f74-a5b8-d22f3c3f8dac"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.54fb0544-8b4e-4f74-a5b8-d22f3c3f8dac"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6b58ef79-63cb-4e8a-a8e9-b753f97a241d"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.6b58ef79-63cb-4e8a-a8e9-b753f97a241d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1786b337-f153-4311-93eb-90207038b24c"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.1786b337-f153-4311-93eb-90207038b24c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5b009ed7-e198-4abe-a471-49d03d04124f"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.5b009ed7-e198-4abe-a471-49d03d04124f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.072d521d-dead-44da-88d6-6a6ffd706b4d"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.072d521d-dead-44da-88d6-6a6ffd706b4d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4d334907-58b4-4a93-ae9f-b16f33db8838"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.4d334907-58b4-4a93-ae9f-b16f33db8838"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.23beae62-35d6-42cb-9690-b014364457aa"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.23beae62-35d6-42cb-9690-b014364457aa"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.32c9b26a-7cf6-4649-a79a-18a2226e88ca"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.32c9b26a-7cf6-4649-a79a-18a2226e88ca"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9669b4c5-7011-49bf-b008-fefdad4b5374"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.9669b4c5-7011-49bf-b008-fefdad4b5374"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b8289683-fc09-4d25-a2c0-95182b8922dd"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.b8289683-fc09-4d25-a2c0-95182b8922dd"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4bd666a9-d481-4339-8463-67eb743f9c36"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.4bd666a9-d481-4339-8463-67eb743f9c36"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4a7fbd47-c6b2-455f-a3f8-8d30c0d3eb21"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.4a7fbd47-c6b2-455f-a3f8-8d30c0d3eb21"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c6f1b4cf-ec8b-49ef-8555-78632c64823c"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.c6f1b4cf-ec8b-49ef-8555-78632c64823c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7d766b84-029d-4a42-83b6-b08ab014bc0b"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.7d766b84-029d-4a42-83b6-b08ab014bc0b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d1099dc9-07fd-470f-bcd9-97882348c6df"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.d1099dc9-07fd-470f-bcd9-97882348c6df"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a0852507-5881-46a3-a2ac-e3445afafb6d"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.a0852507-5881-46a3-a2ac-e3445afafb6d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.50c9a4b5-d5c8-4845-b667-2010a582a2c2"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.50c9a4b5-d5c8-4845-b667-2010a582a2c2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d1e35d7d-07de-4234-abc0-4da67cd6711e"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.d1e35d7d-07de-4234-abc0-4da67cd6711e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e2a75eea-b076-43a9-aca7-dceb8223a5be"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.e2a75eea-b076-43a9-aca7-dceb8223a5be"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.46038f9b-5067-454b-9369-88a65d8334a8"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.46038f9b-5067-454b-9369-88a65d8334a8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5a79bc39-dfa4-4380-8195-abead6cc762d"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.5a79bc39-dfa4-4380-8195-abead6cc762d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5e72dd41-245d-4897-b4f2-2b084a5dbdfb"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.5e72dd41-245d-4897-b4f2-2b084a5dbdfb"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e50e437f-a867-41c2-ada2-d41c1ad74f0d"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.e50e437f-a867-41c2-ada2-d41c1ad74f0d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5f720557-c4e4-43c7-9ce6-b2bae324007a"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.5f720557-c4e4-43c7-9ce6-b2bae324007a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6d621cd4-0e75-42cf-befe-09676130954a"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.6d621cd4-0e75-42cf-befe-09676130954a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.39fbfe57-cd40-4e3b-9473-9506ad0d9ef5"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.39fbfe57-cd40-4e3b-9473-9506ad0d9ef5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b7ed2cce-ae36-4f0f-a302-6e87ed99fb14"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.b7ed2cce-ae36-4f0f-a302-6e87ed99fb14"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ce5238af-81ce-4b7a-a78d-a9d96d44f93a"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.ce5238af-81ce-4b7a-a78d-a9d96d44f93a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c0c72173-6e6e-486b-9e29-31d79b6f1b96"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.c0c72173-6e6e-486b-9e29-31d79b6f1b96"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4254f1bc-6ef1-4b80-9933-68240d7db979"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.4254f1bc-6ef1-4b80-9933-68240d7db979"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7eb6ace0-62d8-483b-b123-7c0edd17785e"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.7eb6ace0-62d8-483b-b123-7c0edd17785e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.89dbeca9-9584-439d-8450-c16421ad2dd3"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.89dbeca9-9584-439d-8450-c16421ad2dd3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ebde7911-69c5-4c00-9f47-2a497c0b9979"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.ebde7911-69c5-4c00-9f47-2a497c0b9979"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.736f9ec9-8650-4ae4-a557-1b666ab99de2"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.736f9ec9-8650-4ae4-a557-1b666ab99de2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c1fd4fa6-b65e-4a09-9fb3-d3fbf3731448"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.c1fd4fa6-b65e-4a09-9fb3-d3fbf3731448"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.fe08373a-46fb-4597-ac8c-29f1824924ce"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.fe08373a-46fb-4597-ac8c-29f1824924ce"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.189477cd-fdb0-4c62-9f84-c6e7b5f766d3"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.189477cd-fdb0-4c62-9f84-c6e7b5f766d3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c022dc78-fb55-43c5-b4f9-4ddfc58ae8e3"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.c022dc78-fb55-43c5-b4f9-4ddfc58ae8e3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3b69f2f8-148c-4618-8481-6d046464a929"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.3b69f2f8-148c-4618-8481-6d046464a929"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8e984915-c151-4552-878f-3563428f15a4"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.8e984915-c151-4552-878f-3563428f15a4"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8cf9d6b2-72c2-4918-b902-9daaa7b7d07d"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.8cf9d6b2-72c2-4918-b902-9daaa7b7d07d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.602253f3-9e2c-4f6b-8389-cd7130d562d2"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.602253f3-9e2c-4f6b-8389-cd7130d562d2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f6be101c-caf1-49eb-a8e5-6cab1010c44d"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.f6be101c-caf1-49eb-a8e5-6cab1010c44d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.28cdf8b1-706c-40de-b61b-355c8859329f"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.28cdf8b1-706c-40de-b61b-355c8859329f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.75ae1715-b930-410c-8c86-1c3088f7e322"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.75ae1715-b930-410c-8c86-1c3088f7e322"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1c3ba167-83fb-4d71-9a74-31969bae84ab"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.1c3ba167-83fb-4d71-9a74-31969bae84ab"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8f9ba6f0-59f5-4222-b5e4-37c63b931af9"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.8f9ba6f0-59f5-4222-b5e4-37c63b931af9"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e87f8f9d-c688-49ae-a4e3-b92ef4e85547"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.e87f8f9d-c688-49ae-a4e3-b92ef4e85547"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.975a2e01-c061-40da-b57b-a2adfc66a9ea"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.975a2e01-c061-40da-b57b-a2adfc66a9ea"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.bee406b0-ccca-4f44-b704-75c164e4d408"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.bee406b0-ccca-4f44-b704-75c164e4d408"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.28f431e2-1664-4035-bd1f-605969382482"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.28f431e2-1664-4035-bd1f-605969382482"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f78de831-2978-4288-9274-85ac61c0510e"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.f78de831-2978-4288-9274-85ac61c0510e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c1b26a20-5a66-4948-8566-0d43aec0a768"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.c1b26a20-5a66-4948-8566-0d43aec0a768"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ecc58650-b4e7-40c7-b2e2-fd77e53bd7b1"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.ecc58650-b4e7-40c7-b2e2-fd77e53bd7b1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b38d5835-ed1c-4017-be1f-b9b8d6d65985"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.b38d5835-ed1c-4017-be1f-b9b8d6d65985"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.01333da0-9769-4ec8-9df8-20bdb62bd021"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.01333da0-9769-4ec8-9df8-20bdb62bd021"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3bfdb747-d1e7-4695-9a21-5fdff8a7bc2f"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.3bfdb747-d1e7-4695-9a21-5fdff8a7bc2f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.32bdca96-67a0-4e19-aa9f-5732a1197667"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.32bdca96-67a0-4e19-aa9f-5732a1197667"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8b27e2fd-a570-4c8d-9f36-038e289713fb"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.8b27e2fd-a570-4c8d-9f36-038e289713fb"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.bb23a053-d84a-44ae-9d33-ff4a6ef897d3"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.bb23a053-d84a-44ae-9d33-ff4a6ef897d3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7e1bcbe6-0b6d-44ab-b409-4af6a2e7bd37"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.7e1bcbe6-0b6d-44ab-b409-4af6a2e7bd37"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.568e83a4-ebbe-4f03-aa1c-a75223b902a8"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.568e83a4-ebbe-4f03-aa1c-a75223b902a8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5a77d697-daac-4a6d-b832-d48989694f8e"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.5a77d697-daac-4a6d-b832-d48989694f8e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6cabf015-1300-453b-a25a-c561ece05b50"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.6cabf015-1300-453b-a25a-c561ece05b50"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1d200dfb-6721-4f45-885c-85c27f701d2b"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.1d200dfb-6721-4f45-885c-85c27f701d2b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b73b11a5-3643-45ba-83c2-230c09440cc1"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.b73b11a5-3643-45ba-83c2-230c09440cc1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d4032213-fe76-4b54-870e-b0498eb08b65"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.d4032213-fe76-4b54-870e-b0498eb08b65"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.af17aad6-662e-42c2-b19d-95e5de93ec50"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.af17aad6-662e-42c2-b19d-95e5de93ec50"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6e59cb6f-27f0-439c-a19f-e8f215a5c102"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.6e59cb6f-27f0-439c-a19f-e8f215a5c102"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8ac716d8-39c5-4204-a7a5-50e7f96d96e5"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.8ac716d8-39c5-4204-a7a5-50e7f96d96e5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2ba410ea-d308-4b83-9440-0bcdcf5863e9"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.2ba410ea-d308-4b83-9440-0bcdcf5863e9"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.bc14b6e7-1f00-4b47-990b-beb1f3d72032"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.bc14b6e7-1f00-4b47-990b-beb1f3d72032"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3a462a95-728a-444b-9684-bb9a5936a58d"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.3a462a95-728a-444b-9684-bb9a5936a58d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9276e406-2269-4512-b736-0efb51584b00"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.9276e406-2269-4512-b736-0efb51584b00"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.86d1a4a4-70e9-4493-a5cf-2fbc85db0e71"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.86d1a4a4-70e9-4493-a5cf-2fbc85db0e71"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.04ef62fb-a26d-462f-88c2-ed6144172f7a"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.04ef62fb-a26d-462f-88c2-ed6144172f7a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.cb78331f-392f-4c54-affb-804a68ed36f4"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.cb78331f-392f-4c54-affb-804a68ed36f4"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0f5fc889-1084-42ca-a09d-8a7f751a390e"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.0f5fc889-1084-42ca-a09d-8a7f751a390e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.444cee45-9a40-4625-98c5-ebef60690224"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.444cee45-9a40-4625-98c5-ebef60690224"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.59014a34-5f60-46c5-92a7-74c47848dea2"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.59014a34-5f60-46c5-92a7-74c47848dea2"};

MERGE (n:InterfaceType:OntologyEntity {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
SET n += {api_name: "i3d_representable", category: "OBJECT_INTERFACE", description: "声明该对象具备在三维场景中存在的能力，是所有子接口的前提。", display_name: "三维存在接口", lifecycle_status: "ACTIVE", rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"};

MERGE (n:InterfaceType:OntologyEntity {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
SET n += {api_name: "i3d_spatial", category: "OBJECT_INTERFACE", description: "赋予对象在三维空间中定位、旋转、缩放的能力（坐标单位：cm，现实 1:1）。", display_name: "空间变换接口", lifecycle_status: "ACTIVE", rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"};

MERGE (n:InterfaceType:OntologyEntity {rid: "ri.iface.52e53e5c-9bb4-4558-8d52-ce11cdf1a5fc"})
SET n += {api_name: "i3d_visual", category: "OBJECT_INTERFACE", description: "赋予对象切换材质外观的能力。资产加载与整体显隐由 I3D_Representable 管理。", display_name: "视觉表达接口", lifecycle_status: "ACTIVE", rid: "ri.iface.52e53e5c-9bb4-4558-8d52-ce11cdf1a5fc"};

MERGE (n:InterfaceType:OntologyEntity {rid: "ri.iface.4e406e03-6c7b-41c7-b08d-9d0f50b0ee02"})
SET n += {api_name: "i3d_behavioral", category: "OBJECT_INTERFACE", description: "赋予对象执行动态行为与信息标注的能力。", display_name: "动态行为接口", lifecycle_status: "ACTIVE", rid: "ri.iface.4e406e03-6c7b-41c7-b08d-9d0f50b0ee02"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"})
SET n += {api_name: "pe16a_3052", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "PE16A-3052", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.deed57c9-d4e6-4396-be88-cb189bf1edbe"], rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"})
SET n += {api_name: "obj_bbb0411d", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "四工位收放", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.f92cab76-e18f-47fd-8bc2-333dcb476205"], rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"})
SET n += {api_name: "c_1", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "c垂直塞1", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.0ceb36a4-bc22-43d0-b3aa-d405160107b0"], rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"})
SET n += {api_name: "obj_086006c2", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "刮平机", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.f1da4ebf-2a1e-4eb3-ae29-eb86bba63284"], rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"})
SET n += {api_name: "sdt_0200_4", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "SDT-0200-新-4", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.e503bcce-1da1-4778-bb10-0bf9ce07a499"], rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"})
SET n += {api_name: "obj_4ff8efe3", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "钻孔清洗收板机", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.f26b1983-ccc4-41d3-9120-1427aa2ad207"], rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
SET n += {api_name: "di", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "库特勒外层DI放", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.6702c5b2-195b-407c-b471-82dbefdacbb5"], rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"})
SET n += {api_name: "hthathateha", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "hthathateha", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.caffa8e7-bf48-4266-859a-873cd3ec0f15"], rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"})
SET n += {api_name: "ypg1", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "ypg1", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.86aa5387-99aa-41fd-8995-029254829371"], rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"})
SET n += {api_name: "swr_0720hnil", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "SWR-0720HNIL-鍗澶缃", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.5191154a-a0d2-490d-8ce0-1011d7163a56"], rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"})
SET n += {api_name: "chaoyinbo_2", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "chaoyinbo-2", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.590ba183-9122-400d-964c-ee6881286989"], rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"})
SET n += {api_name: "sdt_0200_1", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "SDT-0200-新-1", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.b178b58b-e5cd-4567-b06a-46436d715224"], rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"})
SET n += {api_name: "obj_8e0f8dbf", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "外层检修站", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.3021943b-99d0-4043-a310-d23af5514adb"], rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"})
SET n += {api_name: "drfjh", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "DRFJH", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.d0e479c6-f907-407f-a090-7687cd983b9b"], rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"})
SET n += {api_name: "fmnfxm", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "fmnfxm", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.25db2e98-1e52-4b74-9e39-630201f526ad"], rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"})
SET n += {api_name: "sht_2500sus", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "SHT-2500SUS", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.2221f441-cb27-4f56-bd1a-e7060acd0139"], rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"})
SET n += {api_name: "sht_6500", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "SHT-6500", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.59209b5c-0844-4ef2-8d88-c1fafca32589"], rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"})
SET n += {api_name: "sht_4000sus", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "SHT-4000SUS", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.4a0eb029-a2ad-44fa-b943-75bd5597837d"], rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"})
SET n += {api_name: "sht_1500", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "SHT-1500", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.2713bad7-4e3b-4794-b863-d0967510da11"], rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"})
SET n += {api_name: "aoi", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "单机AOI单机", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.4547c607-6b02-4586-880b-abc4b000100c"], rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"})
SET n += {api_name: "obj_720431fd", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "平放收放板机", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.6e17f496-be02-4296-81f6-5f6d072e6966"], rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"})
SET n += {api_name: "obj_1ad0585f", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "无尘鞋柜", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.a6a3aa52-b9ee-4b40-9a30-b449de050d7b"], rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"})
SET n += {api_name: "erhfgheh", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "ERHFGHEH", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.76468671-d7e4-4b00-9dbb-bfa7d7c88e76"], rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"})
SET n += {api_name: "yqtick", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "YQTICK", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.21cf18c3-d61e-42bf-8496-cfeaae78c3db"], rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"})
SET n += {api_name: "obj_b5394828", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "沉铜收放板机", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.791bf8ee-1589-4a32-8303-3e48d75fbf14"], rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"})
SET n += {api_name: "agv", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "AGV", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.03863f76-c90c-4153-ac89-6c88aa81b15a"], rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"})
SET n += {api_name: "g5hg5eh", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "g5hg5eh", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.487b9688-5f04-43d0-964e-e4150519498b"], rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"})
SET n += {api_name: "obj_b9cf038d", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "氮气烘箱", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.c7a7ec0b-4e69-4524-86cd-d7084facdbe5"], rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"})
SET n += {api_name: "beizuan_aoi", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "beizuan AOI", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.75c8ad6e-c87b-44d9-b466-0897ce5c0649"], rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"})
SET n += {api_name: "obj_c74d97b0", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "16", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.491541bc-f550-4f0c-9aab-5af0a0f9d3ec"], rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"})
SET n += {api_name: "nwrt", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "NWRT", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.67834b9b-2e90-45b4-9cd4-a415bf487cb5"], rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"})
SET n += {api_name: "ghyj", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "GHYJ", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.59ceb7d2-d602-4112-9a4e-fc1546184e7c"], rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"})
SET n += {api_name: "futureplbcu6_r_l", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "futurePLBCu6_R-L", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.aa3b1627-d4e2-47db-a7c6-e8f30a65eb53"], rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"})
SET n += {api_name: "obj_811a65b3", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "网版传递", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.52e22308-f0eb-4128-b8cf-201c413a9696"], rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"})
SET n += {api_name: "chaoyinbo_3", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "chaoyinbo-3", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.d08f25e3-6743-432f-9968-8e1f586523cd"], rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"})
SET n += {api_name: "e4htfgh", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "E4HTFGH", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.299b9e86-aae4-4500-aa2d-ea5f81e71444"], rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"})
SET n += {api_name: "sdt_0200_8", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "SDT-0200-8", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.1d0f0c43-3a56-416a-8d2a-6563aea4dc13"], rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"})
SET n += {api_name: "sht_3000sus", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "SHT-3000SUS", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.a410e9f0-754f-4933-bd5a-c20881e1c796"], rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"})
SET n += {api_name: "sct_3000", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "SCT-3000", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.b13e5046-0f20-450c-a512-abb4588839ef"], rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"})
SET n += {api_name: "sct_5000", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "SCT-5000", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.cc1e6f5a-98d5-4ce3-8444-88c5be5ba412"], rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"})
SET n += {api_name: "sht_5000sus", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "SHT-5000SUS", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.0494e016-c75a-4918-b21f-25b31707fcc9"], rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"})
SET n += {api_name: "rgsgv", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "rgsgv", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.f388a217-e6ea-47e5-a6aa-d32b6e2b22a3"], rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"})
SET n += {api_name: "obj_d1f491a4", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "129", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.81e577e7-0414-4136-9f4a-9190fd9968ec"], rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"})
SET n += {api_name: "obj_60e3d488", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "半球摄像头", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.598fa6b8-62a0-46e6-beee-66851152e89c"], rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"})
SET n += {api_name: "ai", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "AI", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.c9dbe1e6-e3f0-4e5d-af74-fe3f2371299a"], rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"})
SET n += {api_name: "dw", description: "由 CAD 解析自动创建（来源：废弃塔.dxf）", display_name: "溶铜槽DW", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.476eb3d1-7c09-409a-8eab-52f371c92bbb"], rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"})
SET n += {api_name: "obj_e044a9f8", description: "由 CAD 解析自动创建（来源：废弃塔.dxf）", display_name: "低位槽", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.4680918c-4506-4b11-b771-c68490e6b980"], rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"})
SET n += {api_name: "sdt_0200_3", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "SDT-0200-新-3", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.9669b4c5-7011-49bf-b008-fefdad4b5374"], rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"})
SET n += {api_name: "smt_1500", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "SMT-1500", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.5a79bc39-dfa4-4380-8195-abead6cc762d"], rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"})
SET n += {api_name: "aerhatjhaerhaerarha", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "aerhatjhaerhaerarha", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.ebde7911-69c5-4c00-9f47-2a497c0b9979"], rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"})
SET n += {api_name: "gdfghfdhjhj", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "GDFGHFDHJHJ", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.75ae1715-b930-410c-8c86-1c3088f7e322"], rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"})
SET n += {api_name: "rthrtharhaer", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "rthrtharhaer", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.3bfdb747-d1e7-4695-9a21-5fdff8a7bc2f"], rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"})
SET n += {api_name: "dsv_1200_1", description: "由 CAD 解析自动创建（来源：四楼.dxf）", display_name: "DSV-1200-1", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.6e59cb6f-27f0-439c-a19f-e8f215a5c102"], rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"};

// Relationships
MATCH (a:PropertyType {rid: "ri.prop.deed57c9-d4e6-4396-be88-cb189bf1edbe"})
MATCH (b:ObjectType {rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.deed57c9-d4e6-4396-be88-cb189bf1edbe"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c9bc0aa4-545f-41bc-abd7-8259966abc35"})
MATCH (b:ObjectType {rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c9bc0aa4-545f-41bc-abd7-8259966abc35"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.91be0407-31f1-47b8-b869-fb78ddb05472"})
MATCH (b:ObjectType {rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.91be0407-31f1-47b8-b869-fb78ddb05472"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.68a8d855-9aff-4475-b138-2a0ef8a93f4a"})
MATCH (b:ObjectType {rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.68a8d855-9aff-4475-b138-2a0ef8a93f4a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dcf1beca-2b81-4a30-9f22-92a8c1e17617"})
MATCH (b:ObjectType {rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dcf1beca-2b81-4a30-9f22-92a8c1e17617"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a9b0d52a-3e6a-41b1-8a22-60949a5cb20b"})
MATCH (b:ObjectType {rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a9b0d52a-3e6a-41b1-8a22-60949a5cb20b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ce5eb5b4-055b-4b14-ade6-01c1b01b8371"})
MATCH (b:ObjectType {rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ce5eb5b4-055b-4b14-ade6-01c1b01b8371"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0a6cacc3-7d3f-4446-8cab-40df582aa6a0"})
MATCH (b:ObjectType {rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0a6cacc3-7d3f-4446-8cab-40df582aa6a0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a35d9477-0df7-43a9-8e30-219bbe91ef6d"})
MATCH (b:ObjectType {rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a35d9477-0df7-43a9-8e30-219bbe91ef6d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.39fe01e0-c128-4b93-b11b-52e5539719bc"})
MATCH (b:ObjectType {rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.39fe01e0-c128-4b93-b11b-52e5539719bc"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c471ef32-18d0-4f1e-873b-873e6e65f9f1"})
MATCH (b:ObjectType {rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c471ef32-18d0-4f1e-873b-873e6e65f9f1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3c168335-c1d6-4b50-80e2-78633657b36d"})
MATCH (b:ObjectType {rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3c168335-c1d6-4b50-80e2-78633657b36d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f92cab76-e18f-47fd-8bc2-333dcb476205"})
MATCH (b:ObjectType {rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f92cab76-e18f-47fd-8bc2-333dcb476205"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.935dfae1-739e-4b6c-b2c8-d13fe13f21fd"})
MATCH (b:ObjectType {rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.935dfae1-739e-4b6c-b2c8-d13fe13f21fd"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d7bb8989-8516-4fb4-afa2-4dca2acf6236"})
MATCH (b:ObjectType {rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d7bb8989-8516-4fb4-afa2-4dca2acf6236"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f9ff6e3e-0b14-4076-8ae2-f061d4378d47"})
MATCH (b:ObjectType {rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f9ff6e3e-0b14-4076-8ae2-f061d4378d47"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3b4a566c-528c-43d9-9b79-5c4c8e2d16ac"})
MATCH (b:ObjectType {rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3b4a566c-528c-43d9-9b79-5c4c8e2d16ac"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.411b3e59-5e9f-4e7b-82d0-ee3eed8140d7"})
MATCH (b:ObjectType {rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.411b3e59-5e9f-4e7b-82d0-ee3eed8140d7"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e2f064a4-710c-4fa4-a1bc-bdca146dbd2f"})
MATCH (b:ObjectType {rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e2f064a4-710c-4fa4-a1bc-bdca146dbd2f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.84674453-6d4e-42db-8bac-6958d31ff159"})
MATCH (b:ObjectType {rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.84674453-6d4e-42db-8bac-6958d31ff159"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.53f81a89-0c3b-4ab2-8237-7efdec10e37d"})
MATCH (b:ObjectType {rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.53f81a89-0c3b-4ab2-8237-7efdec10e37d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e040f715-a64d-410f-b95e-8670923831cd"})
MATCH (b:ObjectType {rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e040f715-a64d-410f-b95e-8670923831cd"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9c60b219-9d4a-417a-9257-5b2d5fea456b"})
MATCH (b:ObjectType {rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9c60b219-9d4a-417a-9257-5b2d5fea456b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6a16093b-a083-4d6f-af1f-b75470d5d987"})
MATCH (b:ObjectType {rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6a16093b-a083-4d6f-af1f-b75470d5d987"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0ceb36a4-bc22-43d0-b3aa-d405160107b0"})
MATCH (b:ObjectType {rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0ceb36a4-bc22-43d0-b3aa-d405160107b0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9fb2974f-dda7-4129-9aa9-5a98141f31c7"})
MATCH (b:ObjectType {rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9fb2974f-dda7-4129-9aa9-5a98141f31c7"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.43b16a60-0068-422e-bdb3-f61dc4361030"})
MATCH (b:ObjectType {rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.43b16a60-0068-422e-bdb3-f61dc4361030"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.64e2bfc9-af76-4497-8e56-4e375657daad"})
MATCH (b:ObjectType {rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.64e2bfc9-af76-4497-8e56-4e375657daad"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f10a77c9-5130-4b6e-98fe-2967322e53af"})
MATCH (b:ObjectType {rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f10a77c9-5130-4b6e-98fe-2967322e53af"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.25ef1142-902f-422b-9933-7fc639b21f19"})
MATCH (b:ObjectType {rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.25ef1142-902f-422b-9933-7fc639b21f19"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ed7e086a-6342-49cf-b06c-7d1dbe4f2b66"})
MATCH (b:ObjectType {rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ed7e086a-6342-49cf-b06c-7d1dbe4f2b66"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.601a2794-f887-4e85-93ba-82a93e36dae3"})
MATCH (b:ObjectType {rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.601a2794-f887-4e85-93ba-82a93e36dae3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5856c1f5-c5eb-4efc-b772-73611fbf1e4d"})
MATCH (b:ObjectType {rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5856c1f5-c5eb-4efc-b772-73611fbf1e4d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e5a285cc-dbf4-430a-a696-a507d8e7a865"})
MATCH (b:ObjectType {rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e5a285cc-dbf4-430a-a696-a507d8e7a865"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a5554ba7-9874-4a03-bace-72e5d3aaa544"})
MATCH (b:ObjectType {rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a5554ba7-9874-4a03-bace-72e5d3aaa544"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1a973526-9812-4e0b-b7dc-80707d86d13f"})
MATCH (b:ObjectType {rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1a973526-9812-4e0b-b7dc-80707d86d13f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f1da4ebf-2a1e-4eb3-ae29-eb86bba63284"})
MATCH (b:ObjectType {rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f1da4ebf-2a1e-4eb3-ae29-eb86bba63284"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a0b1d85f-a45f-4c81-8992-d1c6a4998111"})
MATCH (b:ObjectType {rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a0b1d85f-a45f-4c81-8992-d1c6a4998111"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d172bc31-785c-4e57-b6da-f4253e372511"})
MATCH (b:ObjectType {rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d172bc31-785c-4e57-b6da-f4253e372511"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f49d0716-2a20-45aa-a593-d01ced4f0e61"})
MATCH (b:ObjectType {rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f49d0716-2a20-45aa-a593-d01ced4f0e61"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bed1902a-b10f-462b-a070-c961e60e2ded"})
MATCH (b:ObjectType {rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bed1902a-b10f-462b-a070-c961e60e2ded"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e2645f87-7b2e-408c-8790-c98ed3d24216"})
MATCH (b:ObjectType {rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e2645f87-7b2e-408c-8790-c98ed3d24216"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.38f39f7c-9c32-457c-a156-1c8369bb5245"})
MATCH (b:ObjectType {rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.38f39f7c-9c32-457c-a156-1c8369bb5245"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8fae8474-493e-456e-91cd-94717bb8ece9"})
MATCH (b:ObjectType {rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8fae8474-493e-456e-91cd-94717bb8ece9"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f7dedb41-1ab2-442d-9670-91da17c492b0"})
MATCH (b:ObjectType {rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f7dedb41-1ab2-442d-9670-91da17c492b0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.05d35b07-622b-4437-aa56-ed118b04982c"})
MATCH (b:ObjectType {rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.05d35b07-622b-4437-aa56-ed118b04982c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ff9cfda0-f26a-4ffc-895b-45fb0c4b1497"})
MATCH (b:ObjectType {rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ff9cfda0-f26a-4ffc-895b-45fb0c4b1497"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4a1976f3-1315-48a5-9c13-36404936ff6d"})
MATCH (b:ObjectType {rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4a1976f3-1315-48a5-9c13-36404936ff6d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e503bcce-1da1-4778-bb10-0bf9ce07a499"})
MATCH (b:ObjectType {rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e503bcce-1da1-4778-bb10-0bf9ce07a499"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.caa39e88-e849-40d3-866e-5799acd81908"})
MATCH (b:ObjectType {rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.caa39e88-e849-40d3-866e-5799acd81908"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3026e034-dea5-4915-9c0c-a86052669aee"})
MATCH (b:ObjectType {rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3026e034-dea5-4915-9c0c-a86052669aee"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f929d92b-f0dd-4ae7-9823-40f3b760ce69"})
MATCH (b:ObjectType {rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f929d92b-f0dd-4ae7-9823-40f3b760ce69"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d01ee882-5d14-44cb-a3a3-500e4e28a642"})
MATCH (b:ObjectType {rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d01ee882-5d14-44cb-a3a3-500e4e28a642"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.245e573b-0908-4bec-9b4d-39df386040a4"})
MATCH (b:ObjectType {rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.245e573b-0908-4bec-9b4d-39df386040a4"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.22a2be3e-cc87-470c-8556-60710f985c8d"})
MATCH (b:ObjectType {rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.22a2be3e-cc87-470c-8556-60710f985c8d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9dc17eb7-27d4-48c5-9e2a-7e30c685f83a"})
MATCH (b:ObjectType {rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9dc17eb7-27d4-48c5-9e2a-7e30c685f83a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.db3e2bbe-ea45-4e43-a148-7d978840ec53"})
MATCH (b:ObjectType {rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.db3e2bbe-ea45-4e43-a148-7d978840ec53"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f54ff19f-17b6-4ae0-8030-40ebc458f094"})
MATCH (b:ObjectType {rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f54ff19f-17b6-4ae0-8030-40ebc458f094"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2f772e0e-d60a-4d56-af3a-933759c65a93"})
MATCH (b:ObjectType {rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2f772e0e-d60a-4d56-af3a-933759c65a93"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c2890215-e2a6-40a7-ab87-5ea9e66ba6ff"})
MATCH (b:ObjectType {rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c2890215-e2a6-40a7-ab87-5ea9e66ba6ff"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f26b1983-ccc4-41d3-9120-1427aa2ad207"})
MATCH (b:ObjectType {rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f26b1983-ccc4-41d3-9120-1427aa2ad207"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1cbb8182-7ca8-4bd8-a6a2-c1d3096dd195"})
MATCH (b:ObjectType {rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1cbb8182-7ca8-4bd8-a6a2-c1d3096dd195"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9fd69543-ea79-4bb3-80a9-4543e4da3af3"})
MATCH (b:ObjectType {rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9fd69543-ea79-4bb3-80a9-4543e4da3af3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.adccc361-17e0-4ee1-8cb2-aea40bf6dd08"})
MATCH (b:ObjectType {rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.adccc361-17e0-4ee1-8cb2-aea40bf6dd08"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dbb1d60c-b2db-474b-b44a-30798737dc33"})
MATCH (b:ObjectType {rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dbb1d60c-b2db-474b-b44a-30798737dc33"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3aff4994-6f06-44ae-b2a7-985773e62a8e"})
MATCH (b:ObjectType {rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3aff4994-6f06-44ae-b2a7-985773e62a8e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.50d66bcb-758f-4bf7-9cdf-e5a1e6b5092c"})
MATCH (b:ObjectType {rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.50d66bcb-758f-4bf7-9cdf-e5a1e6b5092c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.22ececb3-55da-4a74-9dad-003023086b86"})
MATCH (b:ObjectType {rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.22ececb3-55da-4a74-9dad-003023086b86"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.323c116a-62c3-4dca-ba0d-581ea8f3cc5b"})
MATCH (b:ObjectType {rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.323c116a-62c3-4dca-ba0d-581ea8f3cc5b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7eaacf18-016e-4d89-958b-2762099a0f7e"})
MATCH (b:ObjectType {rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7eaacf18-016e-4d89-958b-2762099a0f7e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.09b8b174-e82b-48ba-b9ce-dbde46a6f510"})
MATCH (b:ObjectType {rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.09b8b174-e82b-48ba-b9ce-dbde46a6f510"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c1c7ed25-8659-4263-bab7-6bc594115dde"})
MATCH (b:ObjectType {rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c1c7ed25-8659-4263-bab7-6bc594115dde"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6702c5b2-195b-407c-b471-82dbefdacbb5"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6702c5b2-195b-407c-b471-82dbefdacbb5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.467231c7-6fa1-447d-bdb8-13eefb481f9d"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.467231c7-6fa1-447d-bdb8-13eefb481f9d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2528b454-3bfc-40f8-8e34-21b98cd311e3"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2528b454-3bfc-40f8-8e34-21b98cd311e3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a307be12-8cec-4c69-8e38-83c3664beabf"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a307be12-8cec-4c69-8e38-83c3664beabf"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.78e7e192-dcb1-4bd8-9f80-d5274e0d1b59"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6cb214ed-e5de-4771-9a62-d7ba7aa3ce35"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6cb214ed-e5de-4771-9a62-d7ba7aa3ce35"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6ff032b3-d6cd-4251-aba4-0e002e1b160d"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6ff032b3-d6cd-4251-aba4-0e002e1b160d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3f6b8f03-f43b-4d1a-a02f-de78646dd921"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3f6b8f03-f43b-4d1a-a02f-de78646dd921"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fd67fd6e-f85b-45b4-9392-e2192d860340"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fd67fd6e-f85b-45b4-9392-e2192d860340"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d177d39a-b40c-4d13-a850-b489429872a6"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d177d39a-b40c-4d13-a850-b489429872a6"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9b38dd41-dba5-4275-a3c7-586f0896afb5"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9b38dd41-dba5-4275-a3c7-586f0896afb5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cb3116e1-a76f-4c99-a44a-b3ca40793f68"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cb3116e1-a76f-4c99-a44a-b3ca40793f68"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cd07bb0a-70a0-4aa0-92d0-1ea92d33b2b1"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cd07bb0a-70a0-4aa0-92d0-1ea92d33b2b1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a72cabab-dd4d-4b20-b9d7-8cdf060e9540"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a72cabab-dd4d-4b20-b9d7-8cdf060e9540"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a3231a9f-4ff7-4945-a6ef-f70c4a57d9d1"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a3231a9f-4ff7-4945-a6ef-f70c4a57d9d1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.85fc9d92-0476-452a-b1b9-752305265e05"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cc4200f5-7491-4086-a572-56bf7c00fb55"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cc4200f5-7491-4086-a572-56bf7c00fb55"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b64ab3e5-5605-4e05-ad15-3e48ebcec617"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8ed71c5f-d708-4e78-94e7-7ef668118646"})
MATCH (b:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8ed71c5f-d708-4e78-94e7-7ef668118646"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.4ed3a458-a659-4bb5-b93e-55342ef61253"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.caffa8e7-bf48-4266-859a-873cd3ec0f15"})
MATCH (b:ObjectType {rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.caffa8e7-bf48-4266-859a-873cd3ec0f15"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.df596391-b3c4-46a9-8f72-91aaaaad63b2"})
MATCH (b:ObjectType {rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.df596391-b3c4-46a9-8f72-91aaaaad63b2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.151a4d1d-781f-4716-a1c9-5f8440ada99f"})
MATCH (b:ObjectType {rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.151a4d1d-781f-4716-a1c9-5f8440ada99f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.51ffab5a-7056-4cdf-a28a-326fa6bc01d0"})
MATCH (b:ObjectType {rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.51ffab5a-7056-4cdf-a28a-326fa6bc01d0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.07c1fa8b-e5d6-41dc-af6d-3f507a3fb387"})
MATCH (b:ObjectType {rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.07c1fa8b-e5d6-41dc-af6d-3f507a3fb387"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.673f64bf-7117-4190-8b5b-5075ba8d43bb"})
MATCH (b:ObjectType {rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.673f64bf-7117-4190-8b5b-5075ba8d43bb"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9fdf3d14-3931-41a4-b1b5-362e2782c1ff"})
MATCH (b:ObjectType {rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9fdf3d14-3931-41a4-b1b5-362e2782c1ff"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.007dc89b-488c-4601-82fb-f9871ccc624d"})
MATCH (b:ObjectType {rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.007dc89b-488c-4601-82fb-f9871ccc624d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1db107c1-c3bf-44df-bb42-08bfe89a28ef"})
MATCH (b:ObjectType {rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1db107c1-c3bf-44df-bb42-08bfe89a28ef"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a268efe4-c8d9-4600-a9f4-ab2c482b5ceb"})
MATCH (b:ObjectType {rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a268efe4-c8d9-4600-a9f4-ab2c482b5ceb"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d239aced-17d2-4e2e-98dc-fc363a891c52"})
MATCH (b:ObjectType {rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d239aced-17d2-4e2e-98dc-fc363a891c52"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.74d67d0e-13da-4c4d-9576-584300fad9ab"})
MATCH (b:ObjectType {rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.74d67d0e-13da-4c4d-9576-584300fad9ab"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.86aa5387-99aa-41fd-8995-029254829371"})
MATCH (b:ObjectType {rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.86aa5387-99aa-41fd-8995-029254829371"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f33be0e3-116c-4e01-8ddc-3bc00625bfba"})
MATCH (b:ObjectType {rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f33be0e3-116c-4e01-8ddc-3bc00625bfba"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2af7184a-582d-435f-8ce9-8f9f1350ddbe"})
MATCH (b:ObjectType {rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2af7184a-582d-435f-8ce9-8f9f1350ddbe"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.24e94381-a6eb-4303-82db-e920dbd1af84"})
MATCH (b:ObjectType {rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.24e94381-a6eb-4303-82db-e920dbd1af84"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e183731b-aaa5-40d9-a381-98bf5ec3f5f5"})
MATCH (b:ObjectType {rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e183731b-aaa5-40d9-a381-98bf5ec3f5f5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8da2011f-7479-407e-bd76-ec8294a20721"})
MATCH (b:ObjectType {rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8da2011f-7479-407e-bd76-ec8294a20721"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8bc5b954-ddfe-41cb-8c93-d22dccdd6b33"})
MATCH (b:ObjectType {rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8bc5b954-ddfe-41cb-8c93-d22dccdd6b33"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5ddee043-fa7e-42e1-857b-c63cf12775ef"})
MATCH (b:ObjectType {rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5ddee043-fa7e-42e1-857b-c63cf12775ef"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f19a3a29-207a-4162-bb63-5b0c8c896972"})
MATCH (b:ObjectType {rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f19a3a29-207a-4162-bb63-5b0c8c896972"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.11a495cc-ec44-46dc-a6bb-29abf8d02cfd"})
MATCH (b:ObjectType {rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.11a495cc-ec44-46dc-a6bb-29abf8d02cfd"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.23eab455-1189-4116-9276-9ad042fcdcf3"})
MATCH (b:ObjectType {rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.23eab455-1189-4116-9276-9ad042fcdcf3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.50ad6ea9-a53c-45a4-abfe-7e2aa8374ea8"})
MATCH (b:ObjectType {rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.50ad6ea9-a53c-45a4-abfe-7e2aa8374ea8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5191154a-a0d2-490d-8ce0-1011d7163a56"})
MATCH (b:ObjectType {rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5191154a-a0d2-490d-8ce0-1011d7163a56"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2622f719-70b8-4791-a5cd-80e8b1e5ab97"})
MATCH (b:ObjectType {rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2622f719-70b8-4791-a5cd-80e8b1e5ab97"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a5f702ee-b5ea-4606-a9ab-051ed2d2df96"})
MATCH (b:ObjectType {rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a5f702ee-b5ea-4606-a9ab-051ed2d2df96"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e286f528-3d59-4f06-bdfb-56cba646b3da"})
MATCH (b:ObjectType {rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e286f528-3d59-4f06-bdfb-56cba646b3da"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.da78d997-50de-4f00-a6d7-732bb9c15255"})
MATCH (b:ObjectType {rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.da78d997-50de-4f00-a6d7-732bb9c15255"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8b92d492-bb35-44d3-b379-03bad0e71531"})
MATCH (b:ObjectType {rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8b92d492-bb35-44d3-b379-03bad0e71531"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.49d4f0a2-e913-4e19-9eba-0e0ff6f0ab90"})
MATCH (b:ObjectType {rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.49d4f0a2-e913-4e19-9eba-0e0ff6f0ab90"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.626eeacf-ab39-4eec-935e-96e43d7fca56"})
MATCH (b:ObjectType {rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.626eeacf-ab39-4eec-935e-96e43d7fca56"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.755acf5c-e251-435d-9d25-0e26ed14451a"})
MATCH (b:ObjectType {rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.755acf5c-e251-435d-9d25-0e26ed14451a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1d2a45da-5fc5-49e8-87ae-c34bfe6bd127"})
MATCH (b:ObjectType {rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1d2a45da-5fc5-49e8-87ae-c34bfe6bd127"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4f8ca48e-8f01-40e0-b2d1-ac1418cec28c"})
MATCH (b:ObjectType {rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4f8ca48e-8f01-40e0-b2d1-ac1418cec28c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e411ce62-77a0-4b9d-8da8-78d81a299521"})
MATCH (b:ObjectType {rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e411ce62-77a0-4b9d-8da8-78d81a299521"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.590ba183-9122-400d-964c-ee6881286989"})
MATCH (b:ObjectType {rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.590ba183-9122-400d-964c-ee6881286989"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0313a341-db15-4cc9-bde3-d930cc02ae31"})
MATCH (b:ObjectType {rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0313a341-db15-4cc9-bde3-d930cc02ae31"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.77669b70-b57f-43e4-888b-dba8f753e3c8"})
MATCH (b:ObjectType {rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.77669b70-b57f-43e4-888b-dba8f753e3c8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.de4354f1-8731-4c1c-9e3e-53aca72a3634"})
MATCH (b:ObjectType {rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.de4354f1-8731-4c1c-9e3e-53aca72a3634"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.54f0029f-a59d-472f-ba79-669203655d9e"})
MATCH (b:ObjectType {rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.54f0029f-a59d-472f-ba79-669203655d9e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f70bdb3e-aea7-4dd7-ade6-08d6737ff59c"})
MATCH (b:ObjectType {rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f70bdb3e-aea7-4dd7-ade6-08d6737ff59c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3dd88e4d-9cf0-4b32-a69a-1a30c2d22c47"})
MATCH (b:ObjectType {rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3dd88e4d-9cf0-4b32-a69a-1a30c2d22c47"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5ed0bb8f-f175-4e3f-9aee-cc11a0728f0d"})
MATCH (b:ObjectType {rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5ed0bb8f-f175-4e3f-9aee-cc11a0728f0d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.beb7032b-0bb4-4d33-93a3-36d64b6dd631"})
MATCH (b:ObjectType {rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.beb7032b-0bb4-4d33-93a3-36d64b6dd631"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.800cd3a4-bbf0-406d-b595-4bfc8c97f251"})
MATCH (b:ObjectType {rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.800cd3a4-bbf0-406d-b595-4bfc8c97f251"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c9c4e792-aebe-4f01-94be-9f59d88d88ea"})
MATCH (b:ObjectType {rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c9c4e792-aebe-4f01-94be-9f59d88d88ea"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6be14a42-d178-4c24-b195-169a45576c33"})
MATCH (b:ObjectType {rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6be14a42-d178-4c24-b195-169a45576c33"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b178b58b-e5cd-4567-b06a-46436d715224"})
MATCH (b:ObjectType {rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b178b58b-e5cd-4567-b06a-46436d715224"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8ad72184-cd7c-4bee-b93a-a76bfbedee53"})
MATCH (b:ObjectType {rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8ad72184-cd7c-4bee-b93a-a76bfbedee53"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3583621f-9781-4cb1-b7c3-b30978064849"})
MATCH (b:ObjectType {rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3583621f-9781-4cb1-b7c3-b30978064849"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9e4ceec5-eb2b-4337-ab9d-5270aa6b8cfc"})
MATCH (b:ObjectType {rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9e4ceec5-eb2b-4337-ab9d-5270aa6b8cfc"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4151ec16-36d5-4a92-8675-a1ce5629177c"})
MATCH (b:ObjectType {rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4151ec16-36d5-4a92-8675-a1ce5629177c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3deb9135-58c1-48aa-9d77-7a11d7eb9a91"})
MATCH (b:ObjectType {rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3deb9135-58c1-48aa-9d77-7a11d7eb9a91"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8cf0c835-a522-4968-94af-aa3920a72519"})
MATCH (b:ObjectType {rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8cf0c835-a522-4968-94af-aa3920a72519"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5b851716-d36f-4c53-b116-666bfb31803b"})
MATCH (b:ObjectType {rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5b851716-d36f-4c53-b116-666bfb31803b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a813085a-ea8e-43b7-9e82-37e311ec489e"})
MATCH (b:ObjectType {rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a813085a-ea8e-43b7-9e82-37e311ec489e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e6b49d14-1d4c-4564-b967-b34767a4a593"})
MATCH (b:ObjectType {rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e6b49d14-1d4c-4564-b967-b34767a4a593"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.beded43e-0e3d-4e5a-ab7f-fb7dd7089d80"})
MATCH (b:ObjectType {rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.beded43e-0e3d-4e5a-ab7f-fb7dd7089d80"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5c7493b7-7e06-4637-847b-7e2e82328cfe"})
MATCH (b:ObjectType {rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5c7493b7-7e06-4637-847b-7e2e82328cfe"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3021943b-99d0-4043-a310-d23af5514adb"})
MATCH (b:ObjectType {rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3021943b-99d0-4043-a310-d23af5514adb"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.270fec92-2445-468c-8004-0edf7d660eb9"})
MATCH (b:ObjectType {rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.270fec92-2445-468c-8004-0edf7d660eb9"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.838e38ae-ae4b-4972-b5b7-5788d9630b1d"})
MATCH (b:ObjectType {rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.838e38ae-ae4b-4972-b5b7-5788d9630b1d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d9564e67-81a1-4173-96ae-92e1ca93a290"})
MATCH (b:ObjectType {rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d9564e67-81a1-4173-96ae-92e1ca93a290"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.06e2462f-d0b8-45ff-93e7-1314dfed15ea"})
MATCH (b:ObjectType {rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.06e2462f-d0b8-45ff-93e7-1314dfed15ea"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.743306e4-e1b2-4af5-866f-bf6f8b276cb0"})
MATCH (b:ObjectType {rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.743306e4-e1b2-4af5-866f-bf6f8b276cb0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.78434de5-7b88-42d3-8212-24dffdbf5c4f"})
MATCH (b:ObjectType {rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.78434de5-7b88-42d3-8212-24dffdbf5c4f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8177c5d3-87be-4d8b-85f8-a77d871baba8"})
MATCH (b:ObjectType {rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8177c5d3-87be-4d8b-85f8-a77d871baba8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c336a3b2-dafa-43ff-a39b-8e524c686810"})
MATCH (b:ObjectType {rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c336a3b2-dafa-43ff-a39b-8e524c686810"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dd7e2799-9649-4ad0-ae7d-740f60266b59"})
MATCH (b:ObjectType {rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dd7e2799-9649-4ad0-ae7d-740f60266b59"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.562a6170-6a1b-453e-b1da-91edc9185743"})
MATCH (b:ObjectType {rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.562a6170-6a1b-453e-b1da-91edc9185743"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.24df180d-6f1f-4787-8098-0b1514895bab"})
MATCH (b:ObjectType {rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.24df180d-6f1f-4787-8098-0b1514895bab"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d0e479c6-f907-407f-a090-7687cd983b9b"})
MATCH (b:ObjectType {rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d0e479c6-f907-407f-a090-7687cd983b9b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6fe38279-61d3-40da-bd4b-e1eafae930b1"})
MATCH (b:ObjectType {rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6fe38279-61d3-40da-bd4b-e1eafae930b1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0dadbcfa-148b-4051-b431-6ac7b6387de4"})
MATCH (b:ObjectType {rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0dadbcfa-148b-4051-b431-6ac7b6387de4"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.75474bc3-d4bd-4736-a069-071c5697bbe8"})
MATCH (b:ObjectType {rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.75474bc3-d4bd-4736-a069-071c5697bbe8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.825cd8f0-5abc-4735-8aea-a762c2c1cec2"})
MATCH (b:ObjectType {rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.825cd8f0-5abc-4735-8aea-a762c2c1cec2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.56063b64-69ae-446c-91b6-0779abd7b90d"})
MATCH (b:ObjectType {rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.56063b64-69ae-446c-91b6-0779abd7b90d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c86c5409-df22-486f-9092-86ed1bc451d0"})
MATCH (b:ObjectType {rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c86c5409-df22-486f-9092-86ed1bc451d0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3ba398d2-be63-4563-baa2-b45768b82804"})
MATCH (b:ObjectType {rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3ba398d2-be63-4563-baa2-b45768b82804"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0ccaaf9a-33be-43a6-b93e-daef41221713"})
MATCH (b:ObjectType {rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0ccaaf9a-33be-43a6-b93e-daef41221713"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e0490e5d-71cd-4378-88ba-cfd7782860c0"})
MATCH (b:ObjectType {rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e0490e5d-71cd-4378-88ba-cfd7782860c0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b8c5f9c2-ce46-431e-aa2d-79d7c490e0a9"})
MATCH (b:ObjectType {rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b8c5f9c2-ce46-431e-aa2d-79d7c490e0a9"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.52c5a021-12a9-43cd-afd8-12e4d1c7e5c5"})
MATCH (b:ObjectType {rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.52c5a021-12a9-43cd-afd8-12e4d1c7e5c5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.25db2e98-1e52-4b74-9e39-630201f526ad"})
MATCH (b:ObjectType {rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.25db2e98-1e52-4b74-9e39-630201f526ad"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9a0085c3-bdea-47e0-aa6c-6384a5fd84e7"})
MATCH (b:ObjectType {rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9a0085c3-bdea-47e0-aa6c-6384a5fd84e7"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f1bec52a-9d24-4127-b35b-286a22f997ec"})
MATCH (b:ObjectType {rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f1bec52a-9d24-4127-b35b-286a22f997ec"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.766034db-285c-47c2-8853-9ac88c7443e5"})
MATCH (b:ObjectType {rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.766034db-285c-47c2-8853-9ac88c7443e5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dcf6740b-3b1c-4bfc-968e-6fcad703a6cf"})
MATCH (b:ObjectType {rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dcf6740b-3b1c-4bfc-968e-6fcad703a6cf"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ece6772b-f5ae-4592-a13d-55690faab422"})
MATCH (b:ObjectType {rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ece6772b-f5ae-4592-a13d-55690faab422"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f4c9703c-4478-47e0-9654-f3c23e184029"})
MATCH (b:ObjectType {rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f4c9703c-4478-47e0-9654-f3c23e184029"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dc4f3b9e-31d5-4896-b4b4-262aed78a778"})
MATCH (b:ObjectType {rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dc4f3b9e-31d5-4896-b4b4-262aed78a778"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2d2b9440-8856-433a-99ed-57480da8ca63"})
MATCH (b:ObjectType {rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2d2b9440-8856-433a-99ed-57480da8ca63"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9124a638-d5d7-4ccd-9075-65d6b5c79de0"})
MATCH (b:ObjectType {rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9124a638-d5d7-4ccd-9075-65d6b5c79de0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.37766ce4-6e02-4a66-a091-4d970e6d39de"})
MATCH (b:ObjectType {rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.37766ce4-6e02-4a66-a091-4d970e6d39de"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0b79c893-2e36-4568-85dc-d68a5689b5ee"})
MATCH (b:ObjectType {rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0b79c893-2e36-4568-85dc-d68a5689b5ee"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2221f441-cb27-4f56-bd1a-e7060acd0139"})
MATCH (b:ObjectType {rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2221f441-cb27-4f56-bd1a-e7060acd0139"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.40fc8287-e992-4bb6-adcf-ee2a3d45874f"})
MATCH (b:ObjectType {rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.40fc8287-e992-4bb6-adcf-ee2a3d45874f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4442b61f-ebe4-49bf-85bc-fab7cb7f8621"})
MATCH (b:ObjectType {rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4442b61f-ebe4-49bf-85bc-fab7cb7f8621"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e98133b4-5df5-4142-9d2f-9323bf0fc102"})
MATCH (b:ObjectType {rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e98133b4-5df5-4142-9d2f-9323bf0fc102"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6e81f9d0-e13d-4580-8ae8-3d86b7bad321"})
MATCH (b:ObjectType {rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6e81f9d0-e13d-4580-8ae8-3d86b7bad321"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.60b77fc8-e878-4fbc-8846-2b1e809c2a00"})
MATCH (b:ObjectType {rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.60b77fc8-e878-4fbc-8846-2b1e809c2a00"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c00c4290-cd78-4556-816b-1d1806de7e10"})
MATCH (b:ObjectType {rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c00c4290-cd78-4556-816b-1d1806de7e10"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d68cef5b-fc26-4acf-9488-1cdde2501084"})
MATCH (b:ObjectType {rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d68cef5b-fc26-4acf-9488-1cdde2501084"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.39be2e01-06ac-49a6-acf6-a7d0de394e80"})
MATCH (b:ObjectType {rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.39be2e01-06ac-49a6-acf6-a7d0de394e80"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.79e67ca7-62c4-40f6-a2ac-28600be6b146"})
MATCH (b:ObjectType {rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.79e67ca7-62c4-40f6-a2ac-28600be6b146"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b0dc1af7-16cd-49d8-85b3-704a239696b7"})
MATCH (b:ObjectType {rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b0dc1af7-16cd-49d8-85b3-704a239696b7"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d90920c8-008b-41c9-9386-abc8e526d5ea"})
MATCH (b:ObjectType {rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d90920c8-008b-41c9-9386-abc8e526d5ea"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.59209b5c-0844-4ef2-8d88-c1fafca32589"})
MATCH (b:ObjectType {rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.59209b5c-0844-4ef2-8d88-c1fafca32589"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.889652f0-9a8d-401f-98fe-e36617b49c92"})
MATCH (b:ObjectType {rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.889652f0-9a8d-401f-98fe-e36617b49c92"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ed2d000b-67fd-4535-b941-be538642382f"})
MATCH (b:ObjectType {rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ed2d000b-67fd-4535-b941-be538642382f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3043e56d-2edd-4137-9d4e-459f278eea33"})
MATCH (b:ObjectType {rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3043e56d-2edd-4137-9d4e-459f278eea33"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.601c0051-28b7-4336-b73e-89fcff107fe3"})
MATCH (b:ObjectType {rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.601c0051-28b7-4336-b73e-89fcff107fe3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.445a6058-7853-4097-94c1-0bde01702c3a"})
MATCH (b:ObjectType {rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.445a6058-7853-4097-94c1-0bde01702c3a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.851f880a-43d1-4a98-9a44-e8cca847ceef"})
MATCH (b:ObjectType {rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.851f880a-43d1-4a98-9a44-e8cca847ceef"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2ed3031e-6dde-4e2d-8eb2-a6b19a726e70"})
MATCH (b:ObjectType {rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2ed3031e-6dde-4e2d-8eb2-a6b19a726e70"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.787ee0ca-e025-4c0f-8ded-a393295b6006"})
MATCH (b:ObjectType {rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.787ee0ca-e025-4c0f-8ded-a393295b6006"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.06a74ae3-1be6-44d4-90d9-2687b419d392"})
MATCH (b:ObjectType {rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.06a74ae3-1be6-44d4-90d9-2687b419d392"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fdcca9e6-b8ed-484c-8ce5-9301c9f5cbd5"})
MATCH (b:ObjectType {rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fdcca9e6-b8ed-484c-8ce5-9301c9f5cbd5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9ae2303c-fd77-427a-9387-fe496f349f8f"})
MATCH (b:ObjectType {rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9ae2303c-fd77-427a-9387-fe496f349f8f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4a0eb029-a2ad-44fa-b943-75bd5597837d"})
MATCH (b:ObjectType {rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4a0eb029-a2ad-44fa-b943-75bd5597837d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8c5137ad-39ec-4300-8987-49627f7e56a4"})
MATCH (b:ObjectType {rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8c5137ad-39ec-4300-8987-49627f7e56a4"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2d042d1a-f07e-4175-a720-32ec3449a24c"})
MATCH (b:ObjectType {rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2d042d1a-f07e-4175-a720-32ec3449a24c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ece474bd-d4f2-429d-8ee3-1f9f357ebcb3"})
MATCH (b:ObjectType {rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ece474bd-d4f2-429d-8ee3-1f9f357ebcb3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d77ce008-13d0-49be-b144-998e4009f741"})
MATCH (b:ObjectType {rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d77ce008-13d0-49be-b144-998e4009f741"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bb987ebf-dda6-4136-8b7a-679f7b3e37b5"})
MATCH (b:ObjectType {rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bb987ebf-dda6-4136-8b7a-679f7b3e37b5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fe853315-6812-4173-aa01-f6c49eedc9f8"})
MATCH (b:ObjectType {rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fe853315-6812-4173-aa01-f6c49eedc9f8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0aadc6d5-7336-4888-ac30-70e7ad2218a9"})
MATCH (b:ObjectType {rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0aadc6d5-7336-4888-ac30-70e7ad2218a9"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a397afb1-5fde-402e-9f31-bc4ffe45b120"})
MATCH (b:ObjectType {rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a397afb1-5fde-402e-9f31-bc4ffe45b120"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f12a7c39-9899-4fa2-8933-b153c96de8bb"})
MATCH (b:ObjectType {rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f12a7c39-9899-4fa2-8933-b153c96de8bb"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.567d0d55-5f69-47fa-8802-c610ee5f4cca"})
MATCH (b:ObjectType {rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.567d0d55-5f69-47fa-8802-c610ee5f4cca"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4e4b55fc-d160-4746-a411-a8e8f0a16f53"})
MATCH (b:ObjectType {rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4e4b55fc-d160-4746-a411-a8e8f0a16f53"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2713bad7-4e3b-4794-b863-d0967510da11"})
MATCH (b:ObjectType {rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2713bad7-4e3b-4794-b863-d0967510da11"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.92722fd6-3788-47c1-9a7c-838e75442dc8"})
MATCH (b:ObjectType {rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.92722fd6-3788-47c1-9a7c-838e75442dc8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.39216596-f1ae-46a5-8181-a26918f04bb6"})
MATCH (b:ObjectType {rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.39216596-f1ae-46a5-8181-a26918f04bb6"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2274b725-9332-43a2-8df0-19df40491c5a"})
MATCH (b:ObjectType {rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2274b725-9332-43a2-8df0-19df40491c5a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4a056974-53df-4d01-aa5e-8a064aa379be"})
MATCH (b:ObjectType {rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4a056974-53df-4d01-aa5e-8a064aa379be"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cf67f0e2-7794-4403-8255-a0e6898bd7fb"})
MATCH (b:ObjectType {rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cf67f0e2-7794-4403-8255-a0e6898bd7fb"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3bb93224-7246-4e05-9907-cc4437955731"})
MATCH (b:ObjectType {rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3bb93224-7246-4e05-9907-cc4437955731"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7263c2bc-a895-4e72-b65f-7e22b8f2d2f6"})
MATCH (b:ObjectType {rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7263c2bc-a895-4e72-b65f-7e22b8f2d2f6"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fd8ff63f-ecac-413a-94f9-5bfd8a4333db"})
MATCH (b:ObjectType {rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fd8ff63f-ecac-413a-94f9-5bfd8a4333db"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.08773f22-972c-405c-8723-00ae2e1c81c1"})
MATCH (b:ObjectType {rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.08773f22-972c-405c-8723-00ae2e1c81c1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2ef0c28c-74c0-4d03-817c-7f12d1628650"})
MATCH (b:ObjectType {rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2ef0c28c-74c0-4d03-817c-7f12d1628650"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d26d3a59-31fe-43d5-91b9-2b773863c65a"})
MATCH (b:ObjectType {rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d26d3a59-31fe-43d5-91b9-2b773863c65a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4547c607-6b02-4586-880b-abc4b000100c"})
MATCH (b:ObjectType {rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4547c607-6b02-4586-880b-abc4b000100c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3e3d780f-4e46-4588-b650-730e8d68cd91"})
MATCH (b:ObjectType {rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3e3d780f-4e46-4588-b650-730e8d68cd91"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6cad4bf5-bb89-4a2f-b5ec-8aa78a3b5dbf"})
MATCH (b:ObjectType {rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6cad4bf5-bb89-4a2f-b5ec-8aa78a3b5dbf"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c2f7479c-634f-469d-a1f7-e0122ef6606a"})
MATCH (b:ObjectType {rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c2f7479c-634f-469d-a1f7-e0122ef6606a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4fbdb5ea-de2c-47eb-99df-f1d504b047c0"})
MATCH (b:ObjectType {rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4fbdb5ea-de2c-47eb-99df-f1d504b047c0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8fe2db14-2b31-4c04-97bc-bda937317302"})
MATCH (b:ObjectType {rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8fe2db14-2b31-4c04-97bc-bda937317302"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.83978a7e-afb8-4501-9bdd-541da8f75656"})
MATCH (b:ObjectType {rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.83978a7e-afb8-4501-9bdd-541da8f75656"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.24ec08f6-a5fe-4dbd-b347-c8879c786306"})
MATCH (b:ObjectType {rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.24ec08f6-a5fe-4dbd-b347-c8879c786306"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b4ad7eaf-5cff-4ef8-900f-d23976d8e9b8"})
MATCH (b:ObjectType {rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b4ad7eaf-5cff-4ef8-900f-d23976d8e9b8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e0f9ddf5-fab0-418d-91f9-f269e3892649"})
MATCH (b:ObjectType {rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e0f9ddf5-fab0-418d-91f9-f269e3892649"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.411a2160-c58a-4fc8-b3ae-21227a167a7b"})
MATCH (b:ObjectType {rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.411a2160-c58a-4fc8-b3ae-21227a167a7b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8fb118e4-c405-4f5e-b16a-427ccc2710db"})
MATCH (b:ObjectType {rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8fb118e4-c405-4f5e-b16a-427ccc2710db"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6e17f496-be02-4296-81f6-5f6d072e6966"})
MATCH (b:ObjectType {rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6e17f496-be02-4296-81f6-5f6d072e6966"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1a950915-8158-48da-bc22-e7b124e4bb1c"})
MATCH (b:ObjectType {rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1a950915-8158-48da-bc22-e7b124e4bb1c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.84dbdda4-35ce-4ed9-ae3d-de3258c4253d"})
MATCH (b:ObjectType {rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.84dbdda4-35ce-4ed9-ae3d-de3258c4253d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f22ef4c8-ee15-485a-b98f-eeb58a53c0e8"})
MATCH (b:ObjectType {rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f22ef4c8-ee15-485a-b98f-eeb58a53c0e8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4c2cf725-8689-4612-a583-188f9e965b39"})
MATCH (b:ObjectType {rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4c2cf725-8689-4612-a583-188f9e965b39"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c2d733d6-f0fa-43f2-bdbd-50795a5ffe1b"})
MATCH (b:ObjectType {rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c2d733d6-f0fa-43f2-bdbd-50795a5ffe1b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.07c7db03-653f-4fac-83bf-888a5c6d7baf"})
MATCH (b:ObjectType {rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.07c7db03-653f-4fac-83bf-888a5c6d7baf"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.be54a64d-ca6e-4cd3-8091-ed8db3050ae8"})
MATCH (b:ObjectType {rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.be54a64d-ca6e-4cd3-8091-ed8db3050ae8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b6bfd333-bede-474b-86c7-01a9f8b0b793"})
MATCH (b:ObjectType {rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b6bfd333-bede-474b-86c7-01a9f8b0b793"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b2a352a5-49db-4c95-9e58-f3d7f3c7f430"})
MATCH (b:ObjectType {rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b2a352a5-49db-4c95-9e58-f3d7f3c7f430"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.90bddd6d-3b49-43cf-b0ab-22b4b8a27e67"})
MATCH (b:ObjectType {rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.90bddd6d-3b49-43cf-b0ab-22b4b8a27e67"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3270c3ed-6f85-41df-9683-8dbe9bcce158"})
MATCH (b:ObjectType {rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3270c3ed-6f85-41df-9683-8dbe9bcce158"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a6a3aa52-b9ee-4b40-9a30-b449de050d7b"})
MATCH (b:ObjectType {rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a6a3aa52-b9ee-4b40-9a30-b449de050d7b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d15e5efc-0cbd-4428-b604-3fb7123217b6"})
MATCH (b:ObjectType {rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d15e5efc-0cbd-4428-b604-3fb7123217b6"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.723c740e-5777-46a3-955b-ec6710b74f68"})
MATCH (b:ObjectType {rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.723c740e-5777-46a3-955b-ec6710b74f68"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.de066e54-ff37-4d65-88d0-802dbfbe5102"})
MATCH (b:ObjectType {rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.de066e54-ff37-4d65-88d0-802dbfbe5102"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d42900bf-7397-4cdc-8194-930db0f3c036"})
MATCH (b:ObjectType {rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d42900bf-7397-4cdc-8194-930db0f3c036"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5d9a5559-d2b3-4ab4-a86a-48a0d0d3b3cb"})
MATCH (b:ObjectType {rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5d9a5559-d2b3-4ab4-a86a-48a0d0d3b3cb"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8fe1a19b-55f9-427d-84d7-db63b6366544"})
MATCH (b:ObjectType {rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8fe1a19b-55f9-427d-84d7-db63b6366544"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9d900d5f-b042-4055-92d1-300cf14c9ea1"})
MATCH (b:ObjectType {rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9d900d5f-b042-4055-92d1-300cf14c9ea1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.47d9b524-8a58-4c19-977a-91be0a4ddc40"})
MATCH (b:ObjectType {rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.47d9b524-8a58-4c19-977a-91be0a4ddc40"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c55ae41e-ed71-4557-aa93-aa91823f23e7"})
MATCH (b:ObjectType {rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c55ae41e-ed71-4557-aa93-aa91823f23e7"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9da5039e-b15d-4253-ba61-025e5352b756"})
MATCH (b:ObjectType {rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9da5039e-b15d-4253-ba61-025e5352b756"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ec76338f-4ece-4197-b544-66a611d1d584"})
MATCH (b:ObjectType {rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ec76338f-4ece-4197-b544-66a611d1d584"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.76468671-d7e4-4b00-9dbb-bfa7d7c88e76"})
MATCH (b:ObjectType {rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.76468671-d7e4-4b00-9dbb-bfa7d7c88e76"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e0cb791e-f74c-4413-9feb-25a31fafba77"})
MATCH (b:ObjectType {rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e0cb791e-f74c-4413-9feb-25a31fafba77"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.41516361-de31-4afa-bf0c-e590da0b6bda"})
MATCH (b:ObjectType {rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.41516361-de31-4afa-bf0c-e590da0b6bda"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ac61e40e-aab3-4f1f-8cd6-5de9ffbcec81"})
MATCH (b:ObjectType {rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ac61e40e-aab3-4f1f-8cd6-5de9ffbcec81"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.11097e4b-7d9c-4051-b075-ef81c2819389"})
MATCH (b:ObjectType {rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.11097e4b-7d9c-4051-b075-ef81c2819389"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5413a530-588d-40e4-9978-e49829932f38"})
MATCH (b:ObjectType {rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5413a530-588d-40e4-9978-e49829932f38"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.eef69390-ad0b-4676-ba65-a6b1294efe50"})
MATCH (b:ObjectType {rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.eef69390-ad0b-4676-ba65-a6b1294efe50"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b32d5706-fc38-4e37-8d96-a866982609c2"})
MATCH (b:ObjectType {rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b32d5706-fc38-4e37-8d96-a866982609c2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.58b348ae-c827-44e6-9176-03548da6e5a6"})
MATCH (b:ObjectType {rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.58b348ae-c827-44e6-9176-03548da6e5a6"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2711dcfc-282b-4e64-af17-b71ca5a119fc"})
MATCH (b:ObjectType {rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2711dcfc-282b-4e64-af17-b71ca5a119fc"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a99a5e7f-3e44-4c5c-820d-b98bf7bd569a"})
MATCH (b:ObjectType {rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a99a5e7f-3e44-4c5c-820d-b98bf7bd569a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fb23b7ef-c5d7-4c77-bc2a-1986478001a2"})
MATCH (b:ObjectType {rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fb23b7ef-c5d7-4c77-bc2a-1986478001a2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.21cf18c3-d61e-42bf-8496-cfeaae78c3db"})
MATCH (b:ObjectType {rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.21cf18c3-d61e-42bf-8496-cfeaae78c3db"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2b8f022e-6d77-4ab0-8132-a50cf03699ff"})
MATCH (b:ObjectType {rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2b8f022e-6d77-4ab0-8132-a50cf03699ff"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f214f688-2949-4832-8c3d-82e9e6c77da3"})
MATCH (b:ObjectType {rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f214f688-2949-4832-8c3d-82e9e6c77da3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ee600034-f1dd-40c2-a1b2-6a1dd66a6a21"})
MATCH (b:ObjectType {rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ee600034-f1dd-40c2-a1b2-6a1dd66a6a21"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.38fa3928-fdf1-4211-91fa-a1642560d19d"})
MATCH (b:ObjectType {rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.38fa3928-fdf1-4211-91fa-a1642560d19d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.33e76194-e721-4514-a3d4-7aa3aa9ca21d"})
MATCH (b:ObjectType {rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.33e76194-e721-4514-a3d4-7aa3aa9ca21d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.02d3c428-088e-402a-acb9-d5749805edac"})
MATCH (b:ObjectType {rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.02d3c428-088e-402a-acb9-d5749805edac"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a462d9cb-5a1d-4c79-b843-fcc88b333293"})
MATCH (b:ObjectType {rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a462d9cb-5a1d-4c79-b843-fcc88b333293"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c8b8d983-4ac5-48fc-8382-c11979ecafca"})
MATCH (b:ObjectType {rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c8b8d983-4ac5-48fc-8382-c11979ecafca"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7fd76a71-131e-420f-8fd1-0c9d5672b925"})
MATCH (b:ObjectType {rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7fd76a71-131e-420f-8fd1-0c9d5672b925"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.76b87519-278c-44ad-b7c0-5e0fad363586"})
MATCH (b:ObjectType {rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.76b87519-278c-44ad-b7c0-5e0fad363586"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a7e6bbb9-1233-4ff9-ac97-c5ab349cc0cd"})
MATCH (b:ObjectType {rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a7e6bbb9-1233-4ff9-ac97-c5ab349cc0cd"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.791bf8ee-1589-4a32-8303-3e48d75fbf14"})
MATCH (b:ObjectType {rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.791bf8ee-1589-4a32-8303-3e48d75fbf14"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.aee8d6f6-baaf-46ec-990b-52588d5e7289"})
MATCH (b:ObjectType {rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.aee8d6f6-baaf-46ec-990b-52588d5e7289"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ab44c1ed-6e09-40e2-a11f-73654d176ac3"})
MATCH (b:ObjectType {rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ab44c1ed-6e09-40e2-a11f-73654d176ac3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f2bd582d-8853-4cf4-9f9f-1378a4b2c9bf"})
MATCH (b:ObjectType {rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f2bd582d-8853-4cf4-9f9f-1378a4b2c9bf"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d743e880-1212-4061-8cc9-bf00c12a90b2"})
MATCH (b:ObjectType {rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d743e880-1212-4061-8cc9-bf00c12a90b2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5ffcf7b8-c757-4a3a-a2e1-ab46f8a2d91a"})
MATCH (b:ObjectType {rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5ffcf7b8-c757-4a3a-a2e1-ab46f8a2d91a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9ae4e4f0-5f82-4496-b644-cfefcf4496a4"})
MATCH (b:ObjectType {rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9ae4e4f0-5f82-4496-b644-cfefcf4496a4"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.128d9f62-5383-49c8-bd4f-e6bbbd067b88"})
MATCH (b:ObjectType {rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.128d9f62-5383-49c8-bd4f-e6bbbd067b88"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7326b689-c04c-424f-9fd1-f1bbabb9ca58"})
MATCH (b:ObjectType {rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7326b689-c04c-424f-9fd1-f1bbabb9ca58"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2a41dd38-6120-471d-bf35-05d6489f4f27"})
MATCH (b:ObjectType {rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2a41dd38-6120-471d-bf35-05d6489f4f27"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d80520f3-c79a-433b-9279-4830c0374b01"})
MATCH (b:ObjectType {rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d80520f3-c79a-433b-9279-4830c0374b01"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4650c890-c63e-42c8-ab1b-e2ed7b6eeb9a"})
MATCH (b:ObjectType {rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4650c890-c63e-42c8-ab1b-e2ed7b6eeb9a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.03863f76-c90c-4153-ac89-6c88aa81b15a"})
MATCH (b:ObjectType {rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.03863f76-c90c-4153-ac89-6c88aa81b15a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5c38993a-17f5-43b3-9bce-5538eb3b935d"})
MATCH (b:ObjectType {rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5c38993a-17f5-43b3-9bce-5538eb3b935d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a5cc9e54-b238-4398-a500-40c845e2d8ac"})
MATCH (b:ObjectType {rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a5cc9e54-b238-4398-a500-40c845e2d8ac"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.828b3906-74f5-4a35-8225-89e70cd2fd46"})
MATCH (b:ObjectType {rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.828b3906-74f5-4a35-8225-89e70cd2fd46"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.63d95926-c886-4e40-aa6b-235a2415f245"})
MATCH (b:ObjectType {rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.63d95926-c886-4e40-aa6b-235a2415f245"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.665024c3-22d1-439a-8c11-7a323da3bb21"})
MATCH (b:ObjectType {rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.665024c3-22d1-439a-8c11-7a323da3bb21"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.de70aa65-39cd-459e-a471-acc9680862c0"})
MATCH (b:ObjectType {rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.de70aa65-39cd-459e-a471-acc9680862c0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.19199d88-f215-438e-b8b5-4da9b2df1ee5"})
MATCH (b:ObjectType {rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.19199d88-f215-438e-b8b5-4da9b2df1ee5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b7aca6a4-594f-437e-8206-265e9c099b1a"})
MATCH (b:ObjectType {rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b7aca6a4-594f-437e-8206-265e9c099b1a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6d4804cc-b302-4938-bce6-b37ed6eeafbf"})
MATCH (b:ObjectType {rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6d4804cc-b302-4938-bce6-b37ed6eeafbf"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.74b8d704-9dbd-4c76-bc63-80d89a093a51"})
MATCH (b:ObjectType {rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.74b8d704-9dbd-4c76-bc63-80d89a093a51"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6b3b228d-a250-436a-8ffd-4b49cc471583"})
MATCH (b:ObjectType {rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6b3b228d-a250-436a-8ffd-4b49cc471583"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.487b9688-5f04-43d0-964e-e4150519498b"})
MATCH (b:ObjectType {rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.487b9688-5f04-43d0-964e-e4150519498b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ef32acdc-4576-4cad-a0b2-78b5be5182df"})
MATCH (b:ObjectType {rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ef32acdc-4576-4cad-a0b2-78b5be5182df"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f75f4769-f6b4-416d-b6d2-8cf57e3096de"})
MATCH (b:ObjectType {rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f75f4769-f6b4-416d-b6d2-8cf57e3096de"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b0604a97-3712-478d-a899-154764775590"})
MATCH (b:ObjectType {rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b0604a97-3712-478d-a899-154764775590"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fd9defd0-c0e4-447e-a149-a989b3dcc42a"})
MATCH (b:ObjectType {rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fd9defd0-c0e4-447e-a149-a989b3dcc42a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.600464a3-969a-4e4a-8615-13ee0f46760a"})
MATCH (b:ObjectType {rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.600464a3-969a-4e4a-8615-13ee0f46760a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c0e6d8af-c4c3-46f0-a521-1ccf65595510"})
MATCH (b:ObjectType {rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c0e6d8af-c4c3-46f0-a521-1ccf65595510"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4592e541-ec81-44b7-9980-1bcd2b64a849"})
MATCH (b:ObjectType {rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4592e541-ec81-44b7-9980-1bcd2b64a849"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a8ecef4e-9490-4153-8625-5dd27442681b"})
MATCH (b:ObjectType {rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a8ecef4e-9490-4153-8625-5dd27442681b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a5a23fdb-254d-41b0-a8e0-35d376738b23"})
MATCH (b:ObjectType {rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a5a23fdb-254d-41b0-a8e0-35d376738b23"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b86ad228-29ad-49c6-88d8-b2d0bbf62341"})
MATCH (b:ObjectType {rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b86ad228-29ad-49c6-88d8-b2d0bbf62341"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7ed2ff37-5c34-4185-a0e3-65b969c12efa"})
MATCH (b:ObjectType {rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7ed2ff37-5c34-4185-a0e3-65b969c12efa"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c7a7ec0b-4e69-4524-86cd-d7084facdbe5"})
MATCH (b:ObjectType {rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c7a7ec0b-4e69-4524-86cd-d7084facdbe5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7b6f7d15-9e5f-4e66-bec4-7a100fa485a4"})
MATCH (b:ObjectType {rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7b6f7d15-9e5f-4e66-bec4-7a100fa485a4"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9fbfef04-2732-42d0-b489-37065aad05d4"})
MATCH (b:ObjectType {rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9fbfef04-2732-42d0-b489-37065aad05d4"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.68335d89-9888-4bde-9706-e8426a4ef5e6"})
MATCH (b:ObjectType {rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.68335d89-9888-4bde-9706-e8426a4ef5e6"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.755bb61f-831c-42db-a2cc-676a0a382b3a"})
MATCH (b:ObjectType {rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.755bb61f-831c-42db-a2cc-676a0a382b3a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.20925e93-eaf6-4605-8af4-d676597fd642"})
MATCH (b:ObjectType {rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.20925e93-eaf6-4605-8af4-d676597fd642"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.127d2d88-1497-4c0d-bfff-ea6949c9f371"})
MATCH (b:ObjectType {rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.127d2d88-1497-4c0d-bfff-ea6949c9f371"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b3c0bcaa-052e-4de7-9dfa-8430e4ebf3f8"})
MATCH (b:ObjectType {rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b3c0bcaa-052e-4de7-9dfa-8430e4ebf3f8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bbbcb1ab-e94e-4266-b26d-d547fa440208"})
MATCH (b:ObjectType {rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bbbcb1ab-e94e-4266-b26d-d547fa440208"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.400cc539-a766-45c7-96f0-355ed7a92dd4"})
MATCH (b:ObjectType {rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.400cc539-a766-45c7-96f0-355ed7a92dd4"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e0251500-7790-4516-8bdf-1ee8ab1c058d"})
MATCH (b:ObjectType {rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e0251500-7790-4516-8bdf-1ee8ab1c058d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.157bc805-839e-4400-b4c8-cb0e3f255975"})
MATCH (b:ObjectType {rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.157bc805-839e-4400-b4c8-cb0e3f255975"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.75c8ad6e-c87b-44d9-b466-0897ce5c0649"})
MATCH (b:ObjectType {rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.75c8ad6e-c87b-44d9-b466-0897ce5c0649"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1ea3464a-8d54-4de6-a2aa-4de9a057de40"})
MATCH (b:ObjectType {rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1ea3464a-8d54-4de6-a2aa-4de9a057de40"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ce173da4-b7eb-4ba1-9af7-5f06a9b388b2"})
MATCH (b:ObjectType {rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ce173da4-b7eb-4ba1-9af7-5f06a9b388b2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.384e2576-3670-4e5c-aa76-bb3a41648f18"})
MATCH (b:ObjectType {rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.384e2576-3670-4e5c-aa76-bb3a41648f18"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.69085969-6745-4a1c-a706-0e4e735fa287"})
MATCH (b:ObjectType {rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.69085969-6745-4a1c-a706-0e4e735fa287"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.da034684-3aa8-4838-a352-d6d243342627"})
MATCH (b:ObjectType {rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.da034684-3aa8-4838-a352-d6d243342627"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6e1e910c-9bfc-4ec5-bb54-a2fc5a99285e"})
MATCH (b:ObjectType {rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6e1e910c-9bfc-4ec5-bb54-a2fc5a99285e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.be6b3327-a472-4afe-bc20-feff59a923a2"})
MATCH (b:ObjectType {rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.be6b3327-a472-4afe-bc20-feff59a923a2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9e067da2-54ca-43d7-8856-969525fc20ff"})
MATCH (b:ObjectType {rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9e067da2-54ca-43d7-8856-969525fc20ff"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.67609350-09d9-426c-bdf1-f94ea5563385"})
MATCH (b:ObjectType {rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.67609350-09d9-426c-bdf1-f94ea5563385"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.57d4b45e-690b-4b5e-86c7-f82b99e43140"})
MATCH (b:ObjectType {rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.57d4b45e-690b-4b5e-86c7-f82b99e43140"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ae650c7e-fb4a-4aae-abab-192088843600"})
MATCH (b:ObjectType {rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ae650c7e-fb4a-4aae-abab-192088843600"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.491541bc-f550-4f0c-9aab-5af0a0f9d3ec"})
MATCH (b:ObjectType {rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.491541bc-f550-4f0c-9aab-5af0a0f9d3ec"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9e8872c9-a44f-4dda-ace9-85bdc7b44617"})
MATCH (b:ObjectType {rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9e8872c9-a44f-4dda-ace9-85bdc7b44617"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d6ed530b-0f73-466e-a499-87d0e2a3feea"})
MATCH (b:ObjectType {rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d6ed530b-0f73-466e-a499-87d0e2a3feea"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f114d4e3-ba45-4ee2-95b1-2f216b5cceaa"})
MATCH (b:ObjectType {rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f114d4e3-ba45-4ee2-95b1-2f216b5cceaa"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7c66a3d6-4773-4d69-ab18-cce69f247750"})
MATCH (b:ObjectType {rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7c66a3d6-4773-4d69-ab18-cce69f247750"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.12608799-3c0c-4096-b224-74861580f6f8"})
MATCH (b:ObjectType {rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.12608799-3c0c-4096-b224-74861580f6f8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.592784cf-07a0-437e-a47f-43f76a79dcde"})
MATCH (b:ObjectType {rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.592784cf-07a0-437e-a47f-43f76a79dcde"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.55286dd2-fb11-475a-bb08-dead2227a096"})
MATCH (b:ObjectType {rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.55286dd2-fb11-475a-bb08-dead2227a096"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fb855eeb-5c58-489f-a20b-c6428f912be7"})
MATCH (b:ObjectType {rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fb855eeb-5c58-489f-a20b-c6428f912be7"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.874e22db-86df-4a4f-bc60-2bd6736e246e"})
MATCH (b:ObjectType {rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.874e22db-86df-4a4f-bc60-2bd6736e246e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ea910c6f-e81a-439a-8399-eb2bc1e4ecc5"})
MATCH (b:ObjectType {rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ea910c6f-e81a-439a-8399-eb2bc1e4ecc5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e574f26a-9b81-49f4-9b13-8d5c06e28130"})
MATCH (b:ObjectType {rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e574f26a-9b81-49f4-9b13-8d5c06e28130"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.67834b9b-2e90-45b4-9cd4-a415bf487cb5"})
MATCH (b:ObjectType {rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.67834b9b-2e90-45b4-9cd4-a415bf487cb5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.304c77a8-2507-49ab-8053-2dd15d010d81"})
MATCH (b:ObjectType {rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.304c77a8-2507-49ab-8053-2dd15d010d81"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.549642ad-f334-44b7-ab48-eaff73aae535"})
MATCH (b:ObjectType {rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.549642ad-f334-44b7-ab48-eaff73aae535"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b04aea02-5d5c-4321-a75c-9a10cd04192e"})
MATCH (b:ObjectType {rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b04aea02-5d5c-4321-a75c-9a10cd04192e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5bf332ec-fb37-4b80-8bbd-aedb89b4fe3a"})
MATCH (b:ObjectType {rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5bf332ec-fb37-4b80-8bbd-aedb89b4fe3a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8958c8a0-3ad7-4127-94e0-544d8ee80f9e"})
MATCH (b:ObjectType {rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8958c8a0-3ad7-4127-94e0-544d8ee80f9e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2b9e8bfc-62d3-4e21-a984-3f48eb8cf587"})
MATCH (b:ObjectType {rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2b9e8bfc-62d3-4e21-a984-3f48eb8cf587"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c4856ab5-c599-4dfb-b3ac-a77f9e822624"})
MATCH (b:ObjectType {rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c4856ab5-c599-4dfb-b3ac-a77f9e822624"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.38ddd5fe-3d4d-4393-b76e-10121c36a973"})
MATCH (b:ObjectType {rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.38ddd5fe-3d4d-4393-b76e-10121c36a973"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c7755b9c-8fae-4e7d-87ef-48dc2f16170c"})
MATCH (b:ObjectType {rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c7755b9c-8fae-4e7d-87ef-48dc2f16170c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0d6d81f8-9634-40b6-99e7-1206d69b1178"})
MATCH (b:ObjectType {rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0d6d81f8-9634-40b6-99e7-1206d69b1178"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cbe6a2a6-f9b7-4c82-823a-82b35a303103"})
MATCH (b:ObjectType {rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cbe6a2a6-f9b7-4c82-823a-82b35a303103"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.59ceb7d2-d602-4112-9a4e-fc1546184e7c"})
MATCH (b:ObjectType {rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.59ceb7d2-d602-4112-9a4e-fc1546184e7c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0c74ad25-f221-459c-8db4-5ae0ba9e8dde"})
MATCH (b:ObjectType {rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0c74ad25-f221-459c-8db4-5ae0ba9e8dde"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.546b116a-3215-4ee0-9922-94ca0696b25a"})
MATCH (b:ObjectType {rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.546b116a-3215-4ee0-9922-94ca0696b25a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ad563158-49f6-4d4b-a278-a9913f99742a"})
MATCH (b:ObjectType {rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ad563158-49f6-4d4b-a278-a9913f99742a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2bc9731c-50cb-4bef-9006-08f9876d7338"})
MATCH (b:ObjectType {rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2bc9731c-50cb-4bef-9006-08f9876d7338"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.22e82a83-986d-4619-ba54-4a2fcf7195e8"})
MATCH (b:ObjectType {rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.22e82a83-986d-4619-ba54-4a2fcf7195e8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2499ec88-4350-4771-af0f-d88c2cc2dab2"})
MATCH (b:ObjectType {rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2499ec88-4350-4771-af0f-d88c2cc2dab2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.621b12be-1255-4fb7-b8ea-35f65946456e"})
MATCH (b:ObjectType {rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.621b12be-1255-4fb7-b8ea-35f65946456e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d1457a39-c70e-4cb7-a81a-60a8205235c4"})
MATCH (b:ObjectType {rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d1457a39-c70e-4cb7-a81a-60a8205235c4"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ae8c49fd-f721-4b85-83fc-504a3a16059d"})
MATCH (b:ObjectType {rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ae8c49fd-f721-4b85-83fc-504a3a16059d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b4f92876-9442-4e42-b9ef-471d686d30d3"})
MATCH (b:ObjectType {rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b4f92876-9442-4e42-b9ef-471d686d30d3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3340e42e-94ad-4c42-ae1a-0a245f0ee7fb"})
MATCH (b:ObjectType {rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3340e42e-94ad-4c42-ae1a-0a245f0ee7fb"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.aa3b1627-d4e2-47db-a7c6-e8f30a65eb53"})
MATCH (b:ObjectType {rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.aa3b1627-d4e2-47db-a7c6-e8f30a65eb53"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f1213b14-0cb1-4b09-8699-355e1f4752ad"})
MATCH (b:ObjectType {rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f1213b14-0cb1-4b09-8699-355e1f4752ad"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5ebb3092-b9d7-4951-9849-901912f8a6e4"})
MATCH (b:ObjectType {rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5ebb3092-b9d7-4951-9849-901912f8a6e4"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7ca33fb4-4542-409a-9f55-296e6b6983d5"})
MATCH (b:ObjectType {rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7ca33fb4-4542-409a-9f55-296e6b6983d5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a32f7375-eb90-430d-9ccd-b6ed19f88558"})
MATCH (b:ObjectType {rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a32f7375-eb90-430d-9ccd-b6ed19f88558"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c13d9835-10ad-4f01-946d-d38c677b5ae1"})
MATCH (b:ObjectType {rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c13d9835-10ad-4f01-946d-d38c677b5ae1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fbcc1db4-18e0-4d3a-8c47-014a964f869e"})
MATCH (b:ObjectType {rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fbcc1db4-18e0-4d3a-8c47-014a964f869e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.58790343-157b-4f57-b2f6-24b87c6b365e"})
MATCH (b:ObjectType {rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.58790343-157b-4f57-b2f6-24b87c6b365e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0c2cb5be-97df-4d0b-8048-d43ea16939d3"})
MATCH (b:ObjectType {rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0c2cb5be-97df-4d0b-8048-d43ea16939d3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.879ef1d5-36e5-4417-b4cd-d7e268289b75"})
MATCH (b:ObjectType {rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.879ef1d5-36e5-4417-b4cd-d7e268289b75"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.78d55aa5-de45-4e77-97b5-0f05179b69f7"})
MATCH (b:ObjectType {rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.78d55aa5-de45-4e77-97b5-0f05179b69f7"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.acc5e7f2-4568-463f-916a-4e2beefd9898"})
MATCH (b:ObjectType {rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.acc5e7f2-4568-463f-916a-4e2beefd9898"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.52e22308-f0eb-4128-b8cf-201c413a9696"})
MATCH (b:ObjectType {rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.52e22308-f0eb-4128-b8cf-201c413a9696"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.130ae640-949f-4bb5-b970-f5078e4cdb0a"})
MATCH (b:ObjectType {rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.130ae640-949f-4bb5-b970-f5078e4cdb0a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cb8fe276-7a88-4176-b076-1b75d8361265"})
MATCH (b:ObjectType {rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cb8fe276-7a88-4176-b076-1b75d8361265"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d1caba77-80d7-484a-bf8e-0480cd5b9741"})
MATCH (b:ObjectType {rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d1caba77-80d7-484a-bf8e-0480cd5b9741"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4648d7a5-6b38-4834-a866-e2f7ea73688d"})
MATCH (b:ObjectType {rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4648d7a5-6b38-4834-a866-e2f7ea73688d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9831034b-14de-486c-b06e-45dd0ee17fbf"})
MATCH (b:ObjectType {rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9831034b-14de-486c-b06e-45dd0ee17fbf"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7db36bcc-5097-4a66-b386-58abe87c1604"})
MATCH (b:ObjectType {rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7db36bcc-5097-4a66-b386-58abe87c1604"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7e146f99-9250-4850-a3ba-21e9b0f3cfdb"})
MATCH (b:ObjectType {rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7e146f99-9250-4850-a3ba-21e9b0f3cfdb"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.59730449-d2a9-46a1-8665-e0eaa19dd8a4"})
MATCH (b:ObjectType {rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.59730449-d2a9-46a1-8665-e0eaa19dd8a4"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2cbd4058-9cb5-44f1-9d24-969750e84f01"})
MATCH (b:ObjectType {rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2cbd4058-9cb5-44f1-9d24-969750e84f01"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ed773d33-49e7-47ee-90bd-18e33b9ffc29"})
MATCH (b:ObjectType {rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ed773d33-49e7-47ee-90bd-18e33b9ffc29"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dd625303-f1c8-4739-8572-6100c7af95af"})
MATCH (b:ObjectType {rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dd625303-f1c8-4739-8572-6100c7af95af"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d08f25e3-6743-432f-9968-8e1f586523cd"})
MATCH (b:ObjectType {rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d08f25e3-6743-432f-9968-8e1f586523cd"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6bb8d1c8-13fb-40c6-9ad5-b6e1017e6bb8"})
MATCH (b:ObjectType {rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6bb8d1c8-13fb-40c6-9ad5-b6e1017e6bb8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d4d288f8-ade2-4479-92e0-e6ed0ebd7e96"})
MATCH (b:ObjectType {rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d4d288f8-ade2-4479-92e0-e6ed0ebd7e96"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.91ec4cd6-b5a9-4d0f-95a3-4ec651a7c36b"})
MATCH (b:ObjectType {rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.91ec4cd6-b5a9-4d0f-95a3-4ec651a7c36b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c264d65f-9b5e-43a9-8e73-1f868abc1102"})
MATCH (b:ObjectType {rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c264d65f-9b5e-43a9-8e73-1f868abc1102"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6702c6c4-1064-485c-87b1-3ed2a25bc859"})
MATCH (b:ObjectType {rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6702c6c4-1064-485c-87b1-3ed2a25bc859"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.98d2a69b-7eda-49dc-a091-9d9820a57a6e"})
MATCH (b:ObjectType {rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.98d2a69b-7eda-49dc-a091-9d9820a57a6e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.722ccd98-832c-443e-8b7a-603ab8e32665"})
MATCH (b:ObjectType {rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.722ccd98-832c-443e-8b7a-603ab8e32665"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b449afea-1cf4-4c68-bb34-2570e821daf5"})
MATCH (b:ObjectType {rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b449afea-1cf4-4c68-bb34-2570e821daf5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.552f30c0-fa98-4a1d-8850-c31974c5e95d"})
MATCH (b:ObjectType {rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.552f30c0-fa98-4a1d-8850-c31974c5e95d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.17f84b65-8e65-44c4-8fde-cfdb467c8df9"})
MATCH (b:ObjectType {rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.17f84b65-8e65-44c4-8fde-cfdb467c8df9"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c7a2de21-cd82-4d22-a984-b0867970fa5d"})
MATCH (b:ObjectType {rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c7a2de21-cd82-4d22-a984-b0867970fa5d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.299b9e86-aae4-4500-aa2d-ea5f81e71444"})
MATCH (b:ObjectType {rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.299b9e86-aae4-4500-aa2d-ea5f81e71444"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cb513880-5ebc-4934-9a57-6102026981fd"})
MATCH (b:ObjectType {rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cb513880-5ebc-4934-9a57-6102026981fd"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bf380f09-1040-4fa3-b877-abe4d3e098b7"})
MATCH (b:ObjectType {rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bf380f09-1040-4fa3-b877-abe4d3e098b7"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b278d573-ad46-4355-92b1-99f030cdb750"})
MATCH (b:ObjectType {rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b278d573-ad46-4355-92b1-99f030cdb750"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a39112d4-4319-42a6-99cb-f845a6ed5050"})
MATCH (b:ObjectType {rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a39112d4-4319-42a6-99cb-f845a6ed5050"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5b0a408e-f79b-4f56-95db-a6999689aba6"})
MATCH (b:ObjectType {rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5b0a408e-f79b-4f56-95db-a6999689aba6"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d9a919f2-8036-454e-aef6-d03a7768d414"})
MATCH (b:ObjectType {rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d9a919f2-8036-454e-aef6-d03a7768d414"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.58ad51c1-154d-4d50-994d-2d0b29112b1e"})
MATCH (b:ObjectType {rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.58ad51c1-154d-4d50-994d-2d0b29112b1e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bebecb3b-ad49-437a-bdab-b73b2096ff95"})
MATCH (b:ObjectType {rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bebecb3b-ad49-437a-bdab-b73b2096ff95"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a1ac8d35-fcc2-4581-9efa-9367451124f2"})
MATCH (b:ObjectType {rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a1ac8d35-fcc2-4581-9efa-9367451124f2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b8b8ef73-1830-455d-a3fc-f363a3b3324b"})
MATCH (b:ObjectType {rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b8b8ef73-1830-455d-a3fc-f363a3b3324b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e20a07e6-e30c-470b-9c5f-4e9e34888567"})
MATCH (b:ObjectType {rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e20a07e6-e30c-470b-9c5f-4e9e34888567"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1d0f0c43-3a56-416a-8d2a-6563aea4dc13"})
MATCH (b:ObjectType {rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1d0f0c43-3a56-416a-8d2a-6563aea4dc13"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f72bcbd7-6975-465b-93a0-3d14628e33ba"})
MATCH (b:ObjectType {rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f72bcbd7-6975-465b-93a0-3d14628e33ba"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d633b265-859e-4fe0-a03c-fd4d3e48de91"})
MATCH (b:ObjectType {rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d633b265-859e-4fe0-a03c-fd4d3e48de91"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a159eb9c-116f-45d1-b2ff-879f83ba3e89"})
MATCH (b:ObjectType {rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a159eb9c-116f-45d1-b2ff-879f83ba3e89"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.591fce97-20cf-4499-ba87-d2f7e2011d51"})
MATCH (b:ObjectType {rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.591fce97-20cf-4499-ba87-d2f7e2011d51"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1bbfc6fc-f318-44a5-b31a-ca216e983c0f"})
MATCH (b:ObjectType {rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1bbfc6fc-f318-44a5-b31a-ca216e983c0f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.933f2c9f-77a8-481b-b3d8-687c3696fa76"})
MATCH (b:ObjectType {rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.933f2c9f-77a8-481b-b3d8-687c3696fa76"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.80cb1367-8eb9-415d-a9ab-d13683a2caf7"})
MATCH (b:ObjectType {rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.80cb1367-8eb9-415d-a9ab-d13683a2caf7"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.811faf8f-da66-4147-b2cf-15eb6ac66e0d"})
MATCH (b:ObjectType {rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.811faf8f-da66-4147-b2cf-15eb6ac66e0d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3af056ad-7530-4c5d-a36a-b3fd16599b80"})
MATCH (b:ObjectType {rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3af056ad-7530-4c5d-a36a-b3fd16599b80"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.419f0eb2-182d-44b3-bdfd-f8745f953d0c"})
MATCH (b:ObjectType {rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.419f0eb2-182d-44b3-bdfd-f8745f953d0c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e00a1790-0bc5-455a-9f1c-9c38afcc7805"})
MATCH (b:ObjectType {rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e00a1790-0bc5-455a-9f1c-9c38afcc7805"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a410e9f0-754f-4933-bd5a-c20881e1c796"})
MATCH (b:ObjectType {rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a410e9f0-754f-4933-bd5a-c20881e1c796"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7ff25548-5c3a-4c8d-9d2e-f4d16356f26c"})
MATCH (b:ObjectType {rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7ff25548-5c3a-4c8d-9d2e-f4d16356f26c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ba2391e4-a481-4154-bdd8-522660ffe6bb"})
MATCH (b:ObjectType {rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ba2391e4-a481-4154-bdd8-522660ffe6bb"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.220c5b93-950a-4897-9506-fccad02aa5d7"})
MATCH (b:ObjectType {rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.220c5b93-950a-4897-9506-fccad02aa5d7"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7063c0bf-630d-4569-9cb1-c7568db5c9ad"})
MATCH (b:ObjectType {rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7063c0bf-630d-4569-9cb1-c7568db5c9ad"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a54158e9-ec7e-4a58-b5c3-278af0615da1"})
MATCH (b:ObjectType {rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a54158e9-ec7e-4a58-b5c3-278af0615da1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f6392a42-15c7-4423-b831-173774c3abc2"})
MATCH (b:ObjectType {rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f6392a42-15c7-4423-b831-173774c3abc2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.63a7d13b-76ad-47b3-917a-f070e141c0e0"})
MATCH (b:ObjectType {rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.63a7d13b-76ad-47b3-917a-f070e141c0e0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c5a4615c-ccdb-4051-80c7-c720952d6495"})
MATCH (b:ObjectType {rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c5a4615c-ccdb-4051-80c7-c720952d6495"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1a4d84b1-fc7c-445e-9c27-1b2b8fd32862"})
MATCH (b:ObjectType {rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1a4d84b1-fc7c-445e-9c27-1b2b8fd32862"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.40d492f9-2d5e-469e-955b-d77dc297c439"})
MATCH (b:ObjectType {rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.40d492f9-2d5e-469e-955b-d77dc297c439"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ee93032e-c87f-4d8e-8887-d2518530b57a"})
MATCH (b:ObjectType {rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ee93032e-c87f-4d8e-8887-d2518530b57a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b13e5046-0f20-450c-a512-abb4588839ef"})
MATCH (b:ObjectType {rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b13e5046-0f20-450c-a512-abb4588839ef"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.28dd79ff-d941-405c-b4c1-dac85be115b5"})
MATCH (b:ObjectType {rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.28dd79ff-d941-405c-b4c1-dac85be115b5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.52e1930c-fb7c-48f3-ad04-701fe910fb85"})
MATCH (b:ObjectType {rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.52e1930c-fb7c-48f3-ad04-701fe910fb85"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a53e45a3-aa16-44fb-ac0e-f78138b8b836"})
MATCH (b:ObjectType {rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a53e45a3-aa16-44fb-ac0e-f78138b8b836"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.49a093e2-6484-4944-b6ff-1516f58806f7"})
MATCH (b:ObjectType {rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.49a093e2-6484-4944-b6ff-1516f58806f7"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b82cf951-f7bd-4136-93c4-7807e5295f1d"})
MATCH (b:ObjectType {rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b82cf951-f7bd-4136-93c4-7807e5295f1d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f9c7f7f8-0f21-4f18-b101-b4f0a247fb4e"})
MATCH (b:ObjectType {rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f9c7f7f8-0f21-4f18-b101-b4f0a247fb4e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.25b9e2a4-e75d-408d-aed4-aff40b3710d7"})
MATCH (b:ObjectType {rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.25b9e2a4-e75d-408d-aed4-aff40b3710d7"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6dbfd4ae-0972-48f7-b384-2b9ca5439ce1"})
MATCH (b:ObjectType {rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6dbfd4ae-0972-48f7-b384-2b9ca5439ce1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.62916d27-919e-48c3-a2a2-89974f362a25"})
MATCH (b:ObjectType {rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.62916d27-919e-48c3-a2a2-89974f362a25"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.33acf40e-31b9-4333-a857-2593491ef5e8"})
MATCH (b:ObjectType {rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.33acf40e-31b9-4333-a857-2593491ef5e8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.032b2da2-6be2-48b5-8c6d-1aac5d632761"})
MATCH (b:ObjectType {rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.032b2da2-6be2-48b5-8c6d-1aac5d632761"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cc1e6f5a-98d5-4ce3-8444-88c5be5ba412"})
MATCH (b:ObjectType {rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cc1e6f5a-98d5-4ce3-8444-88c5be5ba412"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8ced1dde-6c6d-4aca-8d6c-28a7b559be23"})
MATCH (b:ObjectType {rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8ced1dde-6c6d-4aca-8d6c-28a7b559be23"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.855410f2-c9c7-4b5e-be0a-b8484927fc38"})
MATCH (b:ObjectType {rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.855410f2-c9c7-4b5e-be0a-b8484927fc38"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d8949234-173c-470e-8124-65f0446087f5"})
MATCH (b:ObjectType {rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d8949234-173c-470e-8124-65f0446087f5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.90b957ec-8f73-4895-b05b-2dcdcd32fed3"})
MATCH (b:ObjectType {rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.90b957ec-8f73-4895-b05b-2dcdcd32fed3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.29a09a5d-b958-4095-affc-21510bb9ab06"})
MATCH (b:ObjectType {rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.29a09a5d-b958-4095-affc-21510bb9ab06"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2558d22d-db75-4a18-b054-1afd7e2ff6a8"})
MATCH (b:ObjectType {rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2558d22d-db75-4a18-b054-1afd7e2ff6a8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3ac9be82-d985-4be8-aa38-ee17ed75d523"})
MATCH (b:ObjectType {rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3ac9be82-d985-4be8-aa38-ee17ed75d523"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8a9a9e02-de8c-49ac-854c-d2d3dc1ca206"})
MATCH (b:ObjectType {rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8a9a9e02-de8c-49ac-854c-d2d3dc1ca206"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4a8967c8-f9cc-4825-966f-2a7e5277a44e"})
MATCH (b:ObjectType {rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4a8967c8-f9cc-4825-966f-2a7e5277a44e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5075f665-c0ce-44e7-8c19-2f675899161c"})
MATCH (b:ObjectType {rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5075f665-c0ce-44e7-8c19-2f675899161c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fcd18adf-a0de-4fd3-ac6c-a246d8fabae0"})
MATCH (b:ObjectType {rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fcd18adf-a0de-4fd3-ac6c-a246d8fabae0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0494e016-c75a-4918-b21f-25b31707fcc9"})
MATCH (b:ObjectType {rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0494e016-c75a-4918-b21f-25b31707fcc9"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.545af153-73b8-49b2-a96a-082f2caa1679"})
MATCH (b:ObjectType {rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.545af153-73b8-49b2-a96a-082f2caa1679"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9207cda2-50e4-48a3-84b3-87dec9b7e4a0"})
MATCH (b:ObjectType {rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9207cda2-50e4-48a3-84b3-87dec9b7e4a0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cffe12c9-1e2b-4e07-9c97-1887edcee386"})
MATCH (b:ObjectType {rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cffe12c9-1e2b-4e07-9c97-1887edcee386"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.13dc597e-37e5-44a1-813e-e3b2ff9692d5"})
MATCH (b:ObjectType {rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.13dc597e-37e5-44a1-813e-e3b2ff9692d5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0916c22b-1f61-47ee-b71c-6b87f69f3faf"})
MATCH (b:ObjectType {rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0916c22b-1f61-47ee-b71c-6b87f69f3faf"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.aa04d09a-a636-46b1-81b5-51855e7bfafb"})
MATCH (b:ObjectType {rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.aa04d09a-a636-46b1-81b5-51855e7bfafb"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b455bfe7-7d95-45fc-9aae-d0116d7fe47c"})
MATCH (b:ObjectType {rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b455bfe7-7d95-45fc-9aae-d0116d7fe47c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2962aef7-4b8f-404a-b242-e293f0348738"})
MATCH (b:ObjectType {rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2962aef7-4b8f-404a-b242-e293f0348738"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.11d1b2d0-ab0c-40dd-98b8-2d171388cb4b"})
MATCH (b:ObjectType {rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.11d1b2d0-ab0c-40dd-98b8-2d171388cb4b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dd71fd20-bb81-4e2b-8a87-8640228ca9a0"})
MATCH (b:ObjectType {rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dd71fd20-bb81-4e2b-8a87-8640228ca9a0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fbb61e5c-c4aa-4ed0-81bd-570241f74f17"})
MATCH (b:ObjectType {rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fbb61e5c-c4aa-4ed0-81bd-570241f74f17"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f388a217-e6ea-47e5-a6aa-d32b6e2b22a3"})
MATCH (b:ObjectType {rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f388a217-e6ea-47e5-a6aa-d32b6e2b22a3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9ff99c3c-557d-4fd2-820a-0def86ff1de6"})
MATCH (b:ObjectType {rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9ff99c3c-557d-4fd2-820a-0def86ff1de6"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4372b16d-adf4-41fe-98bc-7631332eebc3"})
MATCH (b:ObjectType {rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4372b16d-adf4-41fe-98bc-7631332eebc3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2fd9b904-9bea-419f-b2c4-f7f780de524f"})
MATCH (b:ObjectType {rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2fd9b904-9bea-419f-b2c4-f7f780de524f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.90c91310-f566-4f57-8e63-518b9ff8b866"})
MATCH (b:ObjectType {rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.90c91310-f566-4f57-8e63-518b9ff8b866"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.114e0edd-fd87-4a46-af01-5869a8653b6b"})
MATCH (b:ObjectType {rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.114e0edd-fd87-4a46-af01-5869a8653b6b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c87a4366-359d-46af-ad5b-e10db4e0c4d9"})
MATCH (b:ObjectType {rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c87a4366-359d-46af-ad5b-e10db4e0c4d9"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.154774f1-91eb-4e1a-a093-b7fe9ad3da7c"})
MATCH (b:ObjectType {rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.154774f1-91eb-4e1a-a093-b7fe9ad3da7c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2bb61dac-a863-48f9-9158-c1116cca43d0"})
MATCH (b:ObjectType {rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2bb61dac-a863-48f9-9158-c1116cca43d0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3b01b642-892a-4137-81bd-2043722cad09"})
MATCH (b:ObjectType {rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3b01b642-892a-4137-81bd-2043722cad09"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f50f9a3a-7434-47d9-9906-84e592480d72"})
MATCH (b:ObjectType {rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f50f9a3a-7434-47d9-9906-84e592480d72"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a2fc53c2-f21a-4b01-aeba-ec309b1e86e3"})
MATCH (b:ObjectType {rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a2fc53c2-f21a-4b01-aeba-ec309b1e86e3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.81e577e7-0414-4136-9f4a-9190fd9968ec"})
MATCH (b:ObjectType {rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.81e577e7-0414-4136-9f4a-9190fd9968ec"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b35713f7-d7d2-4ac0-a2a3-0d7f558a6f11"})
MATCH (b:ObjectType {rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b35713f7-d7d2-4ac0-a2a3-0d7f558a6f11"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.44222720-acaf-4998-a8d2-1c128e0e2ecf"})
MATCH (b:ObjectType {rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.44222720-acaf-4998-a8d2-1c128e0e2ecf"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.801a5529-aedb-4043-b97a-dde80f128c27"})
MATCH (b:ObjectType {rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.801a5529-aedb-4043-b97a-dde80f128c27"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fb980e54-3eac-491c-8981-f8a7ede6198b"})
MATCH (b:ObjectType {rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fb980e54-3eac-491c-8981-f8a7ede6198b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.531ee204-be0a-4282-8eb4-603f4eeed1ea"})
MATCH (b:ObjectType {rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.531ee204-be0a-4282-8eb4-603f4eeed1ea"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.96e9cc07-fffb-458d-b188-b77f0ebebfe0"})
MATCH (b:ObjectType {rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.96e9cc07-fffb-458d-b188-b77f0ebebfe0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0e9dcdb3-cbdd-47a3-a03e-5190347aa049"})
MATCH (b:ObjectType {rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0e9dcdb3-cbdd-47a3-a03e-5190347aa049"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4143a529-5cec-4ab3-b9b8-b715885e647e"})
MATCH (b:ObjectType {rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4143a529-5cec-4ab3-b9b8-b715885e647e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.23665905-610c-4302-b503-f00f82cf6cf9"})
MATCH (b:ObjectType {rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.23665905-610c-4302-b503-f00f82cf6cf9"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.02fcfa28-cd9a-47dd-94de-b4190724d431"})
MATCH (b:ObjectType {rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.02fcfa28-cd9a-47dd-94de-b4190724d431"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.25743c4a-59be-4807-a0b2-b3c3058869a0"})
MATCH (b:ObjectType {rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.25743c4a-59be-4807-a0b2-b3c3058869a0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.598fa6b8-62a0-46e6-beee-66851152e89c"})
MATCH (b:ObjectType {rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.598fa6b8-62a0-46e6-beee-66851152e89c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.45511b87-231f-40cb-9762-3e393bbf656c"})
MATCH (b:ObjectType {rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.45511b87-231f-40cb-9762-3e393bbf656c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.58d2e7f5-0f70-4877-87d6-f96635eb9d6e"})
MATCH (b:ObjectType {rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.58d2e7f5-0f70-4877-87d6-f96635eb9d6e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f22930d3-11eb-4b51-a7d5-4f68564c08d2"})
MATCH (b:ObjectType {rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f22930d3-11eb-4b51-a7d5-4f68564c08d2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0f9d8790-34be-4d66-8012-e2d66b472317"})
MATCH (b:ObjectType {rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0f9d8790-34be-4d66-8012-e2d66b472317"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.64d35a8e-535b-4c73-a484-bc45dee6bcbc"})
MATCH (b:ObjectType {rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.64d35a8e-535b-4c73-a484-bc45dee6bcbc"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a9544827-32fd-4877-8f76-22d570b3dc78"})
MATCH (b:ObjectType {rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a9544827-32fd-4877-8f76-22d570b3dc78"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cb6ed6e4-a4eb-4d5a-9d04-b460c71c33fd"})
MATCH (b:ObjectType {rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cb6ed6e4-a4eb-4d5a-9d04-b460c71c33fd"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0728ee6f-a38d-4ade-8806-c6f481e7c71e"})
MATCH (b:ObjectType {rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0728ee6f-a38d-4ade-8806-c6f481e7c71e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8d33304e-633f-4e6d-b22a-dc49cc6484ba"})
MATCH (b:ObjectType {rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8d33304e-633f-4e6d-b22a-dc49cc6484ba"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f0dce47a-ce23-411d-b30b-5ab8e2941b3f"})
MATCH (b:ObjectType {rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f0dce47a-ce23-411d-b30b-5ab8e2941b3f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d125a016-585f-4ed7-b7e7-c954002fd701"})
MATCH (b:ObjectType {rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d125a016-585f-4ed7-b7e7-c954002fd701"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c9dbe1e6-e3f0-4e5d-af74-fe3f2371299a"})
MATCH (b:ObjectType {rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c9dbe1e6-e3f0-4e5d-af74-fe3f2371299a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bcf627a9-6d7b-4276-accb-e15e9152d8e3"})
MATCH (b:ObjectType {rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bcf627a9-6d7b-4276-accb-e15e9152d8e3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fdf6a51a-0a02-4107-89f6-08cebc65b7a5"})
MATCH (b:ObjectType {rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fdf6a51a-0a02-4107-89f6-08cebc65b7a5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0b486107-18f4-4a7a-ae5f-b7b735f00567"})
MATCH (b:ObjectType {rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0b486107-18f4-4a7a-ae5f-b7b735f00567"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.51c2e938-9c19-44c7-acd1-283b300b296d"})
MATCH (b:ObjectType {rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.51c2e938-9c19-44c7-acd1-283b300b296d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e35d558a-a6e8-4597-a64a-d3b3014a219b"})
MATCH (b:ObjectType {rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e35d558a-a6e8-4597-a64a-d3b3014a219b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a7aadeda-010e-44d7-8ddf-177cd94faf78"})
MATCH (b:ObjectType {rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a7aadeda-010e-44d7-8ddf-177cd94faf78"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e08eb978-6a35-420d-b778-fc88edfe7e7c"})
MATCH (b:ObjectType {rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e08eb978-6a35-420d-b778-fc88edfe7e7c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.264f6dfd-75f6-48e6-a72d-f730d47457e2"})
MATCH (b:ObjectType {rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.264f6dfd-75f6-48e6-a72d-f730d47457e2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4bec99e7-cc30-4319-b4fa-fbab485e178d"})
MATCH (b:ObjectType {rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4bec99e7-cc30-4319-b4fa-fbab485e178d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.44970e4d-19de-4e94-8c4c-0eb4ae54d7b1"})
MATCH (b:ObjectType {rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.44970e4d-19de-4e94-8c4c-0eb4ae54d7b1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.26409998-adc2-4d26-b872-07d3b7ecb9eb"})
MATCH (b:ObjectType {rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.26409998-adc2-4d26-b872-07d3b7ecb9eb"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.476eb3d1-7c09-409a-8eab-52f371c92bbb"})
MATCH (b:ObjectType {rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.476eb3d1-7c09-409a-8eab-52f371c92bbb"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.00eca89c-1ad9-4360-a2a9-6f45313668b7"})
MATCH (b:ObjectType {rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.00eca89c-1ad9-4360-a2a9-6f45313668b7"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6926a25c-85a4-49f2-a0ee-5b17831ba761"})
MATCH (b:ObjectType {rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6926a25c-85a4-49f2-a0ee-5b17831ba761"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ec722836-27a0-4bb4-93d6-d974ddda3803"})
MATCH (b:ObjectType {rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ec722836-27a0-4bb4-93d6-d974ddda3803"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.54b31073-217d-4a6b-8a4c-76d544a9ab01"})
MATCH (b:ObjectType {rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.54b31073-217d-4a6b-8a4c-76d544a9ab01"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3453dcf7-a23b-4247-9e08-2cc94286164b"})
MATCH (b:ObjectType {rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3453dcf7-a23b-4247-9e08-2cc94286164b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1a837800-acbc-4bef-97f1-3dc70f920980"})
MATCH (b:ObjectType {rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1a837800-acbc-4bef-97f1-3dc70f920980"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d5278ab4-afa1-477e-93ab-56c89e175c93"})
MATCH (b:ObjectType {rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d5278ab4-afa1-477e-93ab-56c89e175c93"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e50fee74-7d0b-44d4-853d-9b3c315d231b"})
MATCH (b:ObjectType {rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e50fee74-7d0b-44d4-853d-9b3c315d231b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2b2184e3-2c8b-41ad-8493-d988d788ac43"})
MATCH (b:ObjectType {rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2b2184e3-2c8b-41ad-8493-d988d788ac43"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4b2873e3-ef7a-4b4a-9dff-e714165892fc"})
MATCH (b:ObjectType {rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4b2873e3-ef7a-4b4a-9dff-e714165892fc"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.01e3c0d7-78ad-4fdf-8778-52612fe397f5"})
MATCH (b:ObjectType {rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.01e3c0d7-78ad-4fdf-8778-52612fe397f5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4680918c-4506-4b11-b771-c68490e6b980"})
MATCH (b:ObjectType {rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4680918c-4506-4b11-b771-c68490e6b980"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bcfc8a20-6bd5-4fbc-b217-0105b6420ff3"})
MATCH (b:ObjectType {rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bcfc8a20-6bd5-4fbc-b217-0105b6420ff3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9f7ff9a8-f648-4bd3-9506-91f38ed512f0"})
MATCH (b:ObjectType {rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9f7ff9a8-f648-4bd3-9506-91f38ed512f0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.74d7e449-1f7a-466a-a9d3-95984f9dafd2"})
MATCH (b:ObjectType {rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.74d7e449-1f7a-466a-a9d3-95984f9dafd2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.54fb0544-8b4e-4f74-a5b8-d22f3c3f8dac"})
MATCH (b:ObjectType {rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.54fb0544-8b4e-4f74-a5b8-d22f3c3f8dac"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6b58ef79-63cb-4e8a-a8e9-b753f97a241d"})
MATCH (b:ObjectType {rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6b58ef79-63cb-4e8a-a8e9-b753f97a241d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1786b337-f153-4311-93eb-90207038b24c"})
MATCH (b:ObjectType {rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1786b337-f153-4311-93eb-90207038b24c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5b009ed7-e198-4abe-a471-49d03d04124f"})
MATCH (b:ObjectType {rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5b009ed7-e198-4abe-a471-49d03d04124f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.072d521d-dead-44da-88d6-6a6ffd706b4d"})
MATCH (b:ObjectType {rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.072d521d-dead-44da-88d6-6a6ffd706b4d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4d334907-58b4-4a93-ae9f-b16f33db8838"})
MATCH (b:ObjectType {rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4d334907-58b4-4a93-ae9f-b16f33db8838"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.23beae62-35d6-42cb-9690-b014364457aa"})
MATCH (b:ObjectType {rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.23beae62-35d6-42cb-9690-b014364457aa"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.32c9b26a-7cf6-4649-a79a-18a2226e88ca"})
MATCH (b:ObjectType {rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.32c9b26a-7cf6-4649-a79a-18a2226e88ca"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9669b4c5-7011-49bf-b008-fefdad4b5374"})
MATCH (b:ObjectType {rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9669b4c5-7011-49bf-b008-fefdad4b5374"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b8289683-fc09-4d25-a2c0-95182b8922dd"})
MATCH (b:ObjectType {rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b8289683-fc09-4d25-a2c0-95182b8922dd"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4bd666a9-d481-4339-8463-67eb743f9c36"})
MATCH (b:ObjectType {rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4bd666a9-d481-4339-8463-67eb743f9c36"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4a7fbd47-c6b2-455f-a3f8-8d30c0d3eb21"})
MATCH (b:ObjectType {rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4a7fbd47-c6b2-455f-a3f8-8d30c0d3eb21"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c6f1b4cf-ec8b-49ef-8555-78632c64823c"})
MATCH (b:ObjectType {rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c6f1b4cf-ec8b-49ef-8555-78632c64823c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7d766b84-029d-4a42-83b6-b08ab014bc0b"})
MATCH (b:ObjectType {rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7d766b84-029d-4a42-83b6-b08ab014bc0b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d1099dc9-07fd-470f-bcd9-97882348c6df"})
MATCH (b:ObjectType {rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d1099dc9-07fd-470f-bcd9-97882348c6df"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a0852507-5881-46a3-a2ac-e3445afafb6d"})
MATCH (b:ObjectType {rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a0852507-5881-46a3-a2ac-e3445afafb6d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.50c9a4b5-d5c8-4845-b667-2010a582a2c2"})
MATCH (b:ObjectType {rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.50c9a4b5-d5c8-4845-b667-2010a582a2c2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d1e35d7d-07de-4234-abc0-4da67cd6711e"})
MATCH (b:ObjectType {rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d1e35d7d-07de-4234-abc0-4da67cd6711e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e2a75eea-b076-43a9-aca7-dceb8223a5be"})
MATCH (b:ObjectType {rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e2a75eea-b076-43a9-aca7-dceb8223a5be"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.46038f9b-5067-454b-9369-88a65d8334a8"})
MATCH (b:ObjectType {rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.46038f9b-5067-454b-9369-88a65d8334a8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5a79bc39-dfa4-4380-8195-abead6cc762d"})
MATCH (b:ObjectType {rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5a79bc39-dfa4-4380-8195-abead6cc762d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5e72dd41-245d-4897-b4f2-2b084a5dbdfb"})
MATCH (b:ObjectType {rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5e72dd41-245d-4897-b4f2-2b084a5dbdfb"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e50e437f-a867-41c2-ada2-d41c1ad74f0d"})
MATCH (b:ObjectType {rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e50e437f-a867-41c2-ada2-d41c1ad74f0d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5f720557-c4e4-43c7-9ce6-b2bae324007a"})
MATCH (b:ObjectType {rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5f720557-c4e4-43c7-9ce6-b2bae324007a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6d621cd4-0e75-42cf-befe-09676130954a"})
MATCH (b:ObjectType {rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6d621cd4-0e75-42cf-befe-09676130954a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.39fbfe57-cd40-4e3b-9473-9506ad0d9ef5"})
MATCH (b:ObjectType {rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.39fbfe57-cd40-4e3b-9473-9506ad0d9ef5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b7ed2cce-ae36-4f0f-a302-6e87ed99fb14"})
MATCH (b:ObjectType {rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b7ed2cce-ae36-4f0f-a302-6e87ed99fb14"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ce5238af-81ce-4b7a-a78d-a9d96d44f93a"})
MATCH (b:ObjectType {rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ce5238af-81ce-4b7a-a78d-a9d96d44f93a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c0c72173-6e6e-486b-9e29-31d79b6f1b96"})
MATCH (b:ObjectType {rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c0c72173-6e6e-486b-9e29-31d79b6f1b96"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4254f1bc-6ef1-4b80-9933-68240d7db979"})
MATCH (b:ObjectType {rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4254f1bc-6ef1-4b80-9933-68240d7db979"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7eb6ace0-62d8-483b-b123-7c0edd17785e"})
MATCH (b:ObjectType {rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7eb6ace0-62d8-483b-b123-7c0edd17785e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.89dbeca9-9584-439d-8450-c16421ad2dd3"})
MATCH (b:ObjectType {rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.89dbeca9-9584-439d-8450-c16421ad2dd3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ebde7911-69c5-4c00-9f47-2a497c0b9979"})
MATCH (b:ObjectType {rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ebde7911-69c5-4c00-9f47-2a497c0b9979"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.736f9ec9-8650-4ae4-a557-1b666ab99de2"})
MATCH (b:ObjectType {rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.736f9ec9-8650-4ae4-a557-1b666ab99de2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c1fd4fa6-b65e-4a09-9fb3-d3fbf3731448"})
MATCH (b:ObjectType {rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c1fd4fa6-b65e-4a09-9fb3-d3fbf3731448"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fe08373a-46fb-4597-ac8c-29f1824924ce"})
MATCH (b:ObjectType {rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fe08373a-46fb-4597-ac8c-29f1824924ce"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.189477cd-fdb0-4c62-9f84-c6e7b5f766d3"})
MATCH (b:ObjectType {rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.189477cd-fdb0-4c62-9f84-c6e7b5f766d3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c022dc78-fb55-43c5-b4f9-4ddfc58ae8e3"})
MATCH (b:ObjectType {rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c022dc78-fb55-43c5-b4f9-4ddfc58ae8e3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3b69f2f8-148c-4618-8481-6d046464a929"})
MATCH (b:ObjectType {rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3b69f2f8-148c-4618-8481-6d046464a929"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8e984915-c151-4552-878f-3563428f15a4"})
MATCH (b:ObjectType {rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8e984915-c151-4552-878f-3563428f15a4"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8cf9d6b2-72c2-4918-b902-9daaa7b7d07d"})
MATCH (b:ObjectType {rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8cf9d6b2-72c2-4918-b902-9daaa7b7d07d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.602253f3-9e2c-4f6b-8389-cd7130d562d2"})
MATCH (b:ObjectType {rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.602253f3-9e2c-4f6b-8389-cd7130d562d2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f6be101c-caf1-49eb-a8e5-6cab1010c44d"})
MATCH (b:ObjectType {rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f6be101c-caf1-49eb-a8e5-6cab1010c44d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.28cdf8b1-706c-40de-b61b-355c8859329f"})
MATCH (b:ObjectType {rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.28cdf8b1-706c-40de-b61b-355c8859329f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.75ae1715-b930-410c-8c86-1c3088f7e322"})
MATCH (b:ObjectType {rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.75ae1715-b930-410c-8c86-1c3088f7e322"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1c3ba167-83fb-4d71-9a74-31969bae84ab"})
MATCH (b:ObjectType {rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1c3ba167-83fb-4d71-9a74-31969bae84ab"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8f9ba6f0-59f5-4222-b5e4-37c63b931af9"})
MATCH (b:ObjectType {rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8f9ba6f0-59f5-4222-b5e4-37c63b931af9"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e87f8f9d-c688-49ae-a4e3-b92ef4e85547"})
MATCH (b:ObjectType {rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e87f8f9d-c688-49ae-a4e3-b92ef4e85547"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.975a2e01-c061-40da-b57b-a2adfc66a9ea"})
MATCH (b:ObjectType {rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.975a2e01-c061-40da-b57b-a2adfc66a9ea"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bee406b0-ccca-4f44-b704-75c164e4d408"})
MATCH (b:ObjectType {rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bee406b0-ccca-4f44-b704-75c164e4d408"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.28f431e2-1664-4035-bd1f-605969382482"})
MATCH (b:ObjectType {rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.28f431e2-1664-4035-bd1f-605969382482"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f78de831-2978-4288-9274-85ac61c0510e"})
MATCH (b:ObjectType {rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f78de831-2978-4288-9274-85ac61c0510e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c1b26a20-5a66-4948-8566-0d43aec0a768"})
MATCH (b:ObjectType {rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c1b26a20-5a66-4948-8566-0d43aec0a768"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ecc58650-b4e7-40c7-b2e2-fd77e53bd7b1"})
MATCH (b:ObjectType {rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ecc58650-b4e7-40c7-b2e2-fd77e53bd7b1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b38d5835-ed1c-4017-be1f-b9b8d6d65985"})
MATCH (b:ObjectType {rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b38d5835-ed1c-4017-be1f-b9b8d6d65985"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.01333da0-9769-4ec8-9df8-20bdb62bd021"})
MATCH (b:ObjectType {rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.01333da0-9769-4ec8-9df8-20bdb62bd021"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3bfdb747-d1e7-4695-9a21-5fdff8a7bc2f"})
MATCH (b:ObjectType {rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3bfdb747-d1e7-4695-9a21-5fdff8a7bc2f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.32bdca96-67a0-4e19-aa9f-5732a1197667"})
MATCH (b:ObjectType {rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.32bdca96-67a0-4e19-aa9f-5732a1197667"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8b27e2fd-a570-4c8d-9f36-038e289713fb"})
MATCH (b:ObjectType {rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8b27e2fd-a570-4c8d-9f36-038e289713fb"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bb23a053-d84a-44ae-9d33-ff4a6ef897d3"})
MATCH (b:ObjectType {rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bb23a053-d84a-44ae-9d33-ff4a6ef897d3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7e1bcbe6-0b6d-44ab-b409-4af6a2e7bd37"})
MATCH (b:ObjectType {rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7e1bcbe6-0b6d-44ab-b409-4af6a2e7bd37"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.568e83a4-ebbe-4f03-aa1c-a75223b902a8"})
MATCH (b:ObjectType {rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.568e83a4-ebbe-4f03-aa1c-a75223b902a8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5a77d697-daac-4a6d-b832-d48989694f8e"})
MATCH (b:ObjectType {rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5a77d697-daac-4a6d-b832-d48989694f8e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6cabf015-1300-453b-a25a-c561ece05b50"})
MATCH (b:ObjectType {rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6cabf015-1300-453b-a25a-c561ece05b50"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1d200dfb-6721-4f45-885c-85c27f701d2b"})
MATCH (b:ObjectType {rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1d200dfb-6721-4f45-885c-85c27f701d2b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b73b11a5-3643-45ba-83c2-230c09440cc1"})
MATCH (b:ObjectType {rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b73b11a5-3643-45ba-83c2-230c09440cc1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d4032213-fe76-4b54-870e-b0498eb08b65"})
MATCH (b:ObjectType {rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d4032213-fe76-4b54-870e-b0498eb08b65"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.af17aad6-662e-42c2-b19d-95e5de93ec50"})
MATCH (b:ObjectType {rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.af17aad6-662e-42c2-b19d-95e5de93ec50"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6e59cb6f-27f0-439c-a19f-e8f215a5c102"})
MATCH (b:ObjectType {rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6e59cb6f-27f0-439c-a19f-e8f215a5c102"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8ac716d8-39c5-4204-a7a5-50e7f96d96e5"})
MATCH (b:ObjectType {rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8ac716d8-39c5-4204-a7a5-50e7f96d96e5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2ba410ea-d308-4b83-9440-0bcdcf5863e9"})
MATCH (b:ObjectType {rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2ba410ea-d308-4b83-9440-0bcdcf5863e9"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bc14b6e7-1f00-4b47-990b-beb1f3d72032"})
MATCH (b:ObjectType {rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bc14b6e7-1f00-4b47-990b-beb1f3d72032"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3a462a95-728a-444b-9684-bb9a5936a58d"})
MATCH (b:ObjectType {rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3a462a95-728a-444b-9684-bb9a5936a58d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9276e406-2269-4512-b736-0efb51584b00"})
MATCH (b:ObjectType {rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9276e406-2269-4512-b736-0efb51584b00"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.86d1a4a4-70e9-4493-a5cf-2fbc85db0e71"})
MATCH (b:ObjectType {rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.86d1a4a4-70e9-4493-a5cf-2fbc85db0e71"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.04ef62fb-a26d-462f-88c2-ed6144172f7a"})
MATCH (b:ObjectType {rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.04ef62fb-a26d-462f-88c2-ed6144172f7a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cb78331f-392f-4c54-affb-804a68ed36f4"})
MATCH (b:ObjectType {rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cb78331f-392f-4c54-affb-804a68ed36f4"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0f5fc889-1084-42ca-a09d-8a7f751a390e"})
MATCH (b:ObjectType {rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0f5fc889-1084-42ca-a09d-8a7f751a390e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.444cee45-9a40-4625-98c5-ebef60690224"})
MATCH (b:ObjectType {rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.444cee45-9a40-4625-98c5-ebef60690224"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.59014a34-5f60-46c5-92a7-74c47848dea2"})
MATCH (b:ObjectType {rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.59014a34-5f60-46c5-92a7-74c47848dea2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:REQUIRES]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:REQUIRES]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:EXTENDS]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:REQUIRES]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:REQUIRES]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:REQUIRES]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:REQUIRES]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:REQUIRES]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:REQUIRES]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:REQUIRES]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:REQUIRES]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:REQUIRES]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.52e53e5c-9bb4-4558-8d52-ce11cdf1a5fc"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:EXTENDS]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.52e53e5c-9bb4-4558-8d52-ce11cdf1a5fc"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.78e7e192-dcb1-4bd8-9f80-d5274e0d1b59"})
MERGE (a)-[r:REQUIRES]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.4e406e03-6c7b-41c7-b08d-9d0f50b0ee02"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:EXTENDS]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.4e406e03-6c7b-41c7-b08d-9d0f50b0ee02"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.85fc9d92-0476-452a-b1b9-752305265e05"})
MERGE (a)-[r:REQUIRES]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.4e406e03-6c7b-41c7-b08d-9d0f50b0ee02"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b64ab3e5-5605-4e05-ad15-3e48ebcec617"})
MERGE (a)-[r:REQUIRES]->(b);

MATCH (a:InterfaceType {rid: "ri.iface.4e406e03-6c7b-41c7-b08d-9d0f50b0ee02"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.4ed3a458-a659-4bb5-b93e-55342ef61253"})
MERGE (a)-[r:REQUIRES]->(b);

MATCH (a:ObjectType {rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.bfa31954-d4a8-4700-af9b-3ddba9db518e"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.0e950168-f338-472d-a9f0-3f5e0adfb7a1"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.be399c91-8ae1-4568-aacc-3134b22ac30b"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.4b36f4d7-79ce-4b4a-bbb7-ce3a72a4f387"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.de503faf-1bd2-4f4d-bb5b-1705623ad048"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.7e30af75-a8d8-4136-9057-6c81704adc82"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MATCH (b:InterfaceType {rid: "ri.iface.52e53e5c-9bb4-4558-8d52-ce11cdf1a5fc"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.8edff8ad-8602-4e2b-b1d7-9738e8d25445"})
MATCH (b:InterfaceType {rid: "ri.iface.4e406e03-6c7b-41c7-b08d-9d0f50b0ee02"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.883b0185-6878-4eaf-94d7-5f8c6b828d51"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.c8618df7-a753-4a00-aeb0-9f7032398a59"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.a3c03f30-d592-4572-a276-862543eed262"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.eade1ef9-4948-4b64-b731-23aae667e7a4"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.6dff04e1-d350-4030-8a2c-8847685a0b36"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.8f429b33-e799-41cc-981b-feb7198e33fe"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.dd24c073-663d-4ef3-8809-8547960e19d0"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.a0983a13-c932-4336-9ccd-286ef5d83529"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.bbeeb9fb-5b1b-4e69-8438-f4a74bda73ed"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.ee4e9a0b-3f48-4c61-b964-f4af087be67d"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.fecb0cb7-cce2-49a0-b80a-e318d2203ca3"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.deef646e-37cf-47eb-995b-0b23382406cc"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.97a77081-46a3-4729-8a14-58148aceaac1"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.7947f88a-5153-44ef-a7ea-3d50c8687dac"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.b02ca34a-ca3f-4fd8-aaea-7813600abeff"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.c35812fb-918c-471d-9de9-be4a4fe814f4"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.c00838a0-2a7f-41be-a17e-48e0042beb8b"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.2c00795c-84dd-4706-9832-1a8eb3e60feb"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.86b2c31c-632c-4d35-8d67-af2fa37f1637"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.3ff8b099-5870-4e78-8fed-6d0d0af2cc05"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.0aed1e65-b0af-4dc8-a880-b1218e3b26ee"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.92b3ff30-cd81-48c3-8034-02df33e8fe3c"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.70438a59-2d4d-4419-8fdc-7467f9b98fdd"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.ecc31ae8-a25a-4d91-8c38-73ae65ab126e"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.31eaeec4-1b6c-47f0-abd2-c7ae420e3ca2"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.c7fa4916-90c7-4d7c-b29d-e8ce353d47a6"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.9375bb7f-8a33-47a4-ad0d-4dda43feaac6"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.dece017c-2c06-4955-92cb-5ea4c93906da"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.3a56555e-fd9f-4d2d-a0ab-d6988b1edd4e"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.6ead4e71-1499-417b-b3ef-818e8229212b"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.3e55f16e-ada7-4108-93d9-81e2e04a8447"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.83f649a5-e434-40bf-acbb-4ce6186d0ab4"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.b7a75eea-76bd-4cfa-a454-3f2d4b1ffc5d"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.f51e8135-b1d2-4a32-837e-26bacff26599"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.0c1f9bfa-6f4e-4443-ad4e-42f21aa321b4"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.3edde82f-07a0-425c-b214-545fb7bb3981"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.fbd8df61-a675-4ff8-b8ff-675c3bbe11f7"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.1b2942f4-de32-475c-a4d2-e7309362fe4f"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.3e888003-94be-44f6-abb8-563596112cae"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.b77b5912-b534-4a12-96ad-7439faf611e2"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.81d70934-789e-47fa-99f7-8a3b79516c31"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.559b1f29-62ae-4ec2-982a-ae12a31d9e73"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.f05713df-6714-48b1-9708-88b46cc59f0c"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.69475ed3-6090-4e1f-9114-9f50dc09d195"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.744b6b2d-e90d-40e4-9830-3aa66c66bfb5"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.c95bd872-e08e-4129-908e-d24058bf6f4e"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);
