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

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9580158c-71f2-5988-8f3c-d3704cc714b8"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.9580158c-71f2-5988-8f3c-d3704cc714b8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5d2e5025-3810-588d-8e0c-35fe63c05f07"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.5d2e5025-3810-588d-8e0c-35fe63c05f07"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.26417eb9-30f2-5924-b86e-1c6a2a4e0060"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.26417eb9-30f2-5924-b86e-1c6a2a4e0060"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.fc11c500-06c3-5cc5-ad69-f2ad67ca25fe"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.fc11c500-06c3-5cc5-ad69-f2ad67ca25fe"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.859f2f93-5ade-593e-9125-cd3959420ee0"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.859f2f93-5ade-593e-9125-cd3959420ee0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e4ef787e-a1bc-5af6-a496-0e1401483918"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.e4ef787e-a1bc-5af6-a496-0e1401483918"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.dab216dc-8fa9-57c7-8161-083bc3b2ba97"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.dab216dc-8fa9-57c7-8161-083bc3b2ba97"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.83271202-1159-55dc-8bef-ea04dfb7c7a2"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.83271202-1159-55dc-8bef-ea04dfb7c7a2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b147a40a-7bd3-5096-8615-6c2eea0016b6"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.b147a40a-7bd3-5096-8615-6c2eea0016b6"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1e7974f2-8430-5aa3-98af-88178f42cf53"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.1e7974f2-8430-5aa3-98af-88178f42cf53"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4b0f991e-21aa-5369-a14b-6e5778276581"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.4b0f991e-21aa-5369-a14b-6e5778276581"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.58dc4823-ed0d-5df7-925e-e7284d587a8e"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.58dc4823-ed0d-5df7-925e-e7284d587a8e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.90817ca9-6ba6-5566-ac2a-43a8356e3b1d"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.90817ca9-6ba6-5566-ac2a-43a8356e3b1d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c3d04300-cc65-549b-abeb-0ac9dac7e354"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.c3d04300-cc65-549b-abeb-0ac9dac7e354"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6e1e5e80-f18d-58cc-9082-d3ad7613d5d5"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.6e1e5e80-f18d-58cc-9082-d3ad7613d5d5"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ff03b920-8921-553b-9e65-43b47d6e5f2f"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.ff03b920-8921-553b-9e65-43b47d6e5f2f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8ad745e0-11de-52bc-b0e7-7d9c44a65fbd"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.8ad745e0-11de-52bc-b0e7-7d9c44a65fbd"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4ea9ef97-9b46-57f7-b380-19ba14417512"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.4ea9ef97-9b46-57f7-b380-19ba14417512"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e67ef576-a9ee-590c-aed7-55bbfb07a90e"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.e67ef576-a9ee-590c-aed7-55bbfb07a90e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e38fd4a8-8844-5f7f-881d-c03719a360f1"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.e38fd4a8-8844-5f7f-881d-c03719a360f1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2774c648-bec7-5f4e-b84c-8b27d1dbcb17"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.2774c648-bec7-5f4e-b84c-8b27d1dbcb17"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ed556902-6cfa-5cc0-95ec-dc331b071715"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.ed556902-6cfa-5cc0-95ec-dc331b071715"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.aee2846f-76c0-5dfe-8a45-063ca69ca014"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.aee2846f-76c0-5dfe-8a45-063ca69ca014"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.dae8c100-5521-5e5d-8f89-67a2aecc3ed8"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.dae8c100-5521-5e5d-8f89-67a2aecc3ed8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b91f4758-ca31-5c6c-9108-13a5185e19e8"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.b91f4758-ca31-5c6c-9108-13a5185e19e8"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9f4797d1-8d27-5c14-b4fc-a8be99951dda"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.9f4797d1-8d27-5c14-b4fc-a8be99951dda"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.41ea891d-5750-537e-ad82-b4e2f13cf156"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.41ea891d-5750-537e-ad82-b4e2f13cf156"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ccf5ac78-127d-5b57-ab07-17303ef34474"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.ccf5ac78-127d-5b57-ab07-17303ef34474"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.0aa13243-6e12-5369-99fe-2fec2ff37705"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.0aa13243-6e12-5369-99fe-2fec2ff37705"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.fc25adfb-eff5-5bdd-b7c2-5b95c1d220be"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.fc25adfb-eff5-5bdd-b7c2-5b95c1d220be"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.decd193a-cc46-5680-be9f-febb09228a99"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.decd193a-cc46-5680-be9f-febb09228a99"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.821438a5-7331-545e-9aeb-64fdb2562d66"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.821438a5-7331-545e-9aeb-64fdb2562d66"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8e4c98df-4840-5974-af04-c3ef2b9a31cf"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.8e4c98df-4840-5974-af04-c3ef2b9a31cf"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f0b6a3d5-259e-542e-8870-6466b2bec6a1"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.f0b6a3d5-259e-542e-8870-6466b2bec6a1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.93350fb9-1740-523f-9813-c0960330365c"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.93350fb9-1740-523f-9813-c0960330365c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7df13def-087c-540e-bcda-ceaecfd32bb9"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.7df13def-087c-540e-bcda-ceaecfd32bb9"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.98751059-d53c-59f1-8607-cc4cf17fe185"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.98751059-d53c-59f1-8607-cc4cf17fe185"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f953f02d-1aa6-54c2-b312-f4e94d63f921"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.f953f02d-1aa6-54c2-b312-f4e94d63f921"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f73bf366-40dd-5372-8086-7e8156441910"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.f73bf366-40dd-5372-8086-7e8156441910"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ec6ee0ef-532d-5088-8709-f397a57c7406"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.ec6ee0ef-532d-5088-8709-f397a57c7406"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.336dd752-04b6-5c2d-8ffe-bef63cdca05f"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.336dd752-04b6-5c2d-8ffe-bef63cdca05f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e565e8cf-748e-562c-b97d-49e3e2520ee0"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.e565e8cf-748e-562c-b97d-49e3e2520ee0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.941b13e6-f5af-58d7-bb63-7544ec4518c6"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.941b13e6-f5af-58d7-bb63-7544ec4518c6"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8fb72429-b246-5a4b-9545-a5db346d083b"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.8fb72429-b246-5a4b-9545-a5db346d083b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6295b622-ed85-5fcc-bd7a-5f1f8268ec92"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.6295b622-ed85-5fcc-bd7a-5f1f8268ec92"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e4d707fc-1e00-5e93-bbe4-20082ae65764"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.e4d707fc-1e00-5e93-bbe4-20082ae65764"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.57ec2d42-df03-5e35-843f-93d632c23d8e"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.57ec2d42-df03-5e35-843f-93d632c23d8e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b52cd7bc-9bb8-54d9-9289-4fdf9e010ad9"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.b52cd7bc-9bb8-54d9-9289-4fdf9e010ad9"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f064de01-0a8e-5a2c-9d27-34131e82257c"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.f064de01-0a8e-5a2c-9d27-34131e82257c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2bef3d05-c2a1-5cc7-bdf6-cb8b6880bbe0"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.2bef3d05-c2a1-5cc7-bdf6-cb8b6880bbe0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f3ced9f5-749b-5f6b-bd5c-ba566cecaf91"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.f3ced9f5-749b-5f6b-bd5c-ba566cecaf91"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4d4a7ecb-ee91-5e07-995e-97d9f6b3b671"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.4d4a7ecb-ee91-5e07-995e-97d9f6b3b671"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f54d3308-5399-5c60-af79-b85b71be1854"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.f54d3308-5399-5c60-af79-b85b71be1854"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.cd659056-e7ec-5104-97ea-e2cd57b42c7a"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.cd659056-e7ec-5104-97ea-e2cd57b42c7a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.5d77cb6b-023a-5ed5-9136-831e82b76222"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.5d77cb6b-023a-5ed5-9136-831e82b76222"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.886092ec-408a-5f52-a997-83634fa22930"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.886092ec-408a-5f52-a997-83634fa22930"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d5688a52-1c68-59b7-b679-fb7817823378"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.d5688a52-1c68-59b7-b679-fb7817823378"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.23d8e9d5-106a-5535-b5ee-62bc95833d90"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.23d8e9d5-106a-5535-b5ee-62bc95833d90"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8cd5b0de-8f52-58e4-b1b4-202930f1b617"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.8cd5b0de-8f52-58e4-b1b4-202930f1b617"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.53ee5557-cb47-5699-acc6-22ee050ef9b1"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.53ee5557-cb47-5699-acc6-22ee050ef9b1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.089c94a3-feee-5f09-a953-2a63dfabfa7c"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.089c94a3-feee-5f09-a953-2a63dfabfa7c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6eeb8d18-c624-5c17-804a-3008919cab6a"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.6eeb8d18-c624-5c17-804a-3008919cab6a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a63ad6ad-9c9b-5fc7-a623-427668248822"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.a63ad6ad-9c9b-5fc7-a623-427668248822"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a1c6e86b-792d-51bc-94be-eefbf6f0c859"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.a1c6e86b-792d-51bc-94be-eefbf6f0c859"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b925391a-f6b5-559f-9620-b49a8d8c6df1"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.b925391a-f6b5-559f-9620-b49a8d8c6df1"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.7648ef3b-d6d2-5c20-bc0d-f46204559c25"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.7648ef3b-d6d2-5c20-bc0d-f46204559c25"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.58bf643d-f074-597f-891b-9ba72f4e5135"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.58bf643d-f074-597f-891b-9ba72f4e5135"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.c711faeb-0463-5f78-8b07-9aa652256ff9"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.c711faeb-0463-5f78-8b07-9aa652256ff9"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1130dc2a-874b-510e-8e77-0ebf3513938e"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.1130dc2a-874b-510e-8e77-0ebf3513938e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a463b602-c8d9-565e-be87-40c58e97a422"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.a463b602-c8d9-565e-be87-40c58e97a422"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.bf542483-0a8d-50d9-8d3f-e83e1f70d93e"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.bf542483-0a8d-50d9-8d3f-e83e1f70d93e"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.55c9543d-be89-5f3c-9663-5c460c9d7cb9"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.55c9543d-be89-5f3c-9663-5c460c9d7cb9"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f2da10d2-8111-5888-a2eb-62521b9d1793"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.f2da10d2-8111-5888-a2eb-62521b9d1793"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9ab1c690-6027-5516-a426-d4e759ada357"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.9ab1c690-6027-5516-a426-d4e759ada357"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.3384f0aa-15f6-5f34-a349-9a056f45e273"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.3384f0aa-15f6-5f34-a349-9a056f45e273"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4ce87d95-7da9-5b91-b5a9-e5b3bac9e88a"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.4ce87d95-7da9-5b91-b5a9-e5b3bac9e88a"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d9c55e72-36e0-5d40-80a8-688f82968060"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.d9c55e72-36e0-5d40-80a8-688f82968060"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f6d00ca4-45d8-5170-860d-610c581b8c90"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.f6d00ca4-45d8-5170-860d-610c581b8c90"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.4811071b-f31d-587a-8046-f30f3b34c2a0"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.4811071b-f31d-587a-8046-f30f3b34c2a0"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6fce9844-0936-50ff-9a15-62166f60200f"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.6fce9844-0936-50ff-9a15-62166f60200f"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2fda8d93-fb6a-5a70-a58f-67fd6062e934"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.2fda8d93-fb6a-5a70-a58f-67fd6062e934"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.1d20aafe-4a75-5351-a374-f6c29b94e038"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.1d20aafe-4a75-5351-a374-f6c29b94e038"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.22c08ad4-843c-5f08-84a9-d2198386b704"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.22c08ad4-843c-5f08-84a9-d2198386b704"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.2a160501-5422-54e2-b05b-f795b85a49b2"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.2a160501-5422-54e2-b05b-f795b85a49b2"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.ae2dbee9-56bf-5bc9-ad44-b045669e94e3"})
SET n += {api_name: "instance_id", data_type: "DT_STRING", display_name: "实例身份证号", lifecycle_status: "ACTIVE", rid: "ri.prop.ae2dbee9-56bf-5bc9-ad44-b045669e94e3"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.8b0c12e2-57a6-5e42-930b-a19c3b29dd1c"})
SET n += {api_name: "asset_id", data_type: "DT_STRING", display_name: "资产唯一码 (GLB)", lifecycle_status: "ACTIVE", rid: "ri.prop.8b0c12e2-57a6-5e42-930b-a19c3b29dd1c"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.84300c22-a035-5ca4-be8f-0e6809aa0a7b"})
SET n += {api_name: "is_visible", data_type: "DT_BOOLEAN", display_name: "是否渲染", lifecycle_status: "ACTIVE", rid: "ri.prop.84300c22-a035-5ca4-be8f-0e6809aa0a7b"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.d8717031-f6b8-551c-96f7-dc92a1a549d9"})
SET n += {api_name: "translation_x", data_type: "DT_DOUBLE", display_name: "位置 X (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.d8717031-f6b8-551c-96f7-dc92a1a549d9"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e40a6e29-ce3b-5990-9be1-c475bbdc009d"})
SET n += {api_name: "translation_y", data_type: "DT_DOUBLE", display_name: "位置 Y (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.e40a6e29-ce3b-5990-9be1-c475bbdc009d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.6926dc82-8694-529e-ba1a-53cdf0aae68d"})
SET n += {api_name: "translation_z", data_type: "DT_DOUBLE", display_name: "位置 Z (cm)", lifecycle_status: "ACTIVE", rid: "ri.prop.6926dc82-8694-529e-ba1a-53cdf0aae68d"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.f39cd6e4-6e8f-55fb-819d-97c6a34fc716"})
SET n += {api_name: "rotation_x", data_type: "DT_DOUBLE", display_name: "旋转 X (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.f39cd6e4-6e8f-55fb-819d-97c6a34fc716"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.689acb68-4fe6-5f00-952e-691628e32194"})
SET n += {api_name: "rotation_y", data_type: "DT_DOUBLE", display_name: "旋转 Y (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.689acb68-4fe6-5f00-952e-691628e32194"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.e4d78cf5-635b-5f5e-b81d-bae8d0a560cb"})
SET n += {api_name: "rotation_z", data_type: "DT_DOUBLE", display_name: "旋转 Z (°)", lifecycle_status: "ACTIVE", rid: "ri.prop.e4d78cf5-635b-5f5e-b81d-bae8d0a560cb"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.b6df9d8c-a74c-5936-81f1-50c78545dc35"})
SET n += {api_name: "scale_x", data_type: "DT_DOUBLE", display_name: "缩放 X", lifecycle_status: "ACTIVE", rid: "ri.prop.b6df9d8c-a74c-5936-81f1-50c78545dc35"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.9acede8a-22ff-53de-996c-8367724eb533"})
SET n += {api_name: "scale_y", data_type: "DT_DOUBLE", display_name: "缩放 Y", lifecycle_status: "ACTIVE", rid: "ri.prop.9acede8a-22ff-53de-996c-8367724eb533"};

MERGE (n:PropertyType:OntologyEntity {rid: "ri.prop.a8afde92-44e2-512e-b83d-744e3d7e7176"})
SET n += {api_name: "scale_z", data_type: "DT_DOUBLE", display_name: "缩放 Z", lifecycle_status: "ACTIVE", rid: "ri.prop.a8afde92-44e2-512e-b83d-744e3d7e7176"};

MERGE (n:InterfaceType:OntologyEntity {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
SET n += {api_name: "i3d_representable", category: "OBJECT_INTERFACE", description: "声明该对象具备在三维场景中存在的能力，是所有子接口的前提。", display_name: "三维存在接口", lifecycle_status: "ACTIVE", rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"};

MERGE (n:InterfaceType:OntologyEntity {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
SET n += {api_name: "i3d_spatial", category: "OBJECT_INTERFACE", description: "赋予对象在三维空间中定位、旋转、缩放的能力（坐标单位：cm，现实 1:1）。", display_name: "空间变换接口", lifecycle_status: "ACTIVE", rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
SET n += {api_name: "zhhz_fixed_wing_aircraft", description: "ZHHZ UE 历史场景设备迁移类型（zhhz.fixed_wing_aircraft）；人工验收前保持 EXPERIMENTAL。", display_name: "固定翼航空器", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.9580158c-71f2-5988-8f3c-d3704cc714b8"], rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
SET n += {api_name: "zhhz_rotorcraft", description: "ZHHZ UE 历史场景设备迁移类型（zhhz.rotorcraft）；人工验收前保持 EXPERIMENTAL。", display_name: "旋翼航空器", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.90817ca9-6ba6-5566-ac2a-43a8356e3b1d"], rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
SET n += {api_name: "zhhz_unmanned_new_aircraft", description: "ZHHZ UE 历史场景设备迁移类型（zhhz.unmanned_new_aircraft）；人工验收前保持 EXPERIMENTAL。", display_name: "无人/新型航空器", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.b91f4758-ca31-5c6c-9108-13a5185e19e8"], rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
SET n += {api_name: "zhhz_aviation_weapon", description: "ZHHZ UE 历史场景设备迁移类型（zhhz.aviation_weapon）；人工验收前保持 EXPERIMENTAL。", display_name: "航空武器/弹药", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.98751059-d53c-59f1-8607-cc4cf17fe185"], rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
SET n += {api_name: "zhhz_avionics_sensor", description: "ZHHZ UE 历史场景设备迁移类型（zhhz.avionics_sensor）；人工验收前保持 EXPERIMENTAL。", display_name: "航电/传感器/对抗设备", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.f064de01-0a8e-5a2c-9d27-34131e82257c"], rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
SET n += {api_name: "zhhz_cockpit_simulator", description: "ZHHZ UE 历史场景设备迁移类型（zhhz.cockpit_simulator）；人工验收前保持 EXPERIMENTAL。", display_name: "座舱/模拟训练系统", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.089c94a3-feee-5f09-a953-2a63dfabfa7c"], rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
SET n += {api_name: "zhhz_display_control_terminal", description: "ZHHZ UE 历史场景设备迁移类型（zhhz.display_control_terminal）；人工验收前保持 EXPERIMENTAL。", display_name: "触控与操作终端", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.f2da10d2-8111-5888-a2eb-62521b9d1793"], rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"};

MERGE (n:ObjectType:OntologyEntity {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
SET n += {api_name: "zhhz_aircraft_component", description: "ZHHZ UE 历史场景设备迁移类型（zhhz.aircraft_component）；人工验收前保持 EXPERIMENTAL。", display_name: "航空部件/子系统", lifecycle_status: "EXPERIMENTAL", primary_key_property_type_rids: ["ri.prop.ae2dbee9-56bf-5bc9-ad44-b045669e94e3"], rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"};

// Relationships
MATCH (a:PropertyType {rid: "ri.prop.9580158c-71f2-5988-8f3c-d3704cc714b8"})
MATCH (b:ObjectType {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9580158c-71f2-5988-8f3c-d3704cc714b8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5d2e5025-3810-588d-8e0c-35fe63c05f07"})
MATCH (b:ObjectType {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5d2e5025-3810-588d-8e0c-35fe63c05f07"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.26417eb9-30f2-5924-b86e-1c6a2a4e0060"})
MATCH (b:ObjectType {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.26417eb9-30f2-5924-b86e-1c6a2a4e0060"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fc11c500-06c3-5cc5-ad69-f2ad67ca25fe"})
MATCH (b:ObjectType {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fc11c500-06c3-5cc5-ad69-f2ad67ca25fe"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.859f2f93-5ade-593e-9125-cd3959420ee0"})
MATCH (b:ObjectType {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.859f2f93-5ade-593e-9125-cd3959420ee0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e4ef787e-a1bc-5af6-a496-0e1401483918"})
MATCH (b:ObjectType {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e4ef787e-a1bc-5af6-a496-0e1401483918"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dab216dc-8fa9-57c7-8161-083bc3b2ba97"})
MATCH (b:ObjectType {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dab216dc-8fa9-57c7-8161-083bc3b2ba97"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.83271202-1159-55dc-8bef-ea04dfb7c7a2"})
MATCH (b:ObjectType {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.83271202-1159-55dc-8bef-ea04dfb7c7a2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b147a40a-7bd3-5096-8615-6c2eea0016b6"})
MATCH (b:ObjectType {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b147a40a-7bd3-5096-8615-6c2eea0016b6"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1e7974f2-8430-5aa3-98af-88178f42cf53"})
MATCH (b:ObjectType {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1e7974f2-8430-5aa3-98af-88178f42cf53"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4b0f991e-21aa-5369-a14b-6e5778276581"})
MATCH (b:ObjectType {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4b0f991e-21aa-5369-a14b-6e5778276581"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.58dc4823-ed0d-5df7-925e-e7284d587a8e"})
MATCH (b:ObjectType {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.58dc4823-ed0d-5df7-925e-e7284d587a8e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.90817ca9-6ba6-5566-ac2a-43a8356e3b1d"})
MATCH (b:ObjectType {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.90817ca9-6ba6-5566-ac2a-43a8356e3b1d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c3d04300-cc65-549b-abeb-0ac9dac7e354"})
MATCH (b:ObjectType {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c3d04300-cc65-549b-abeb-0ac9dac7e354"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6e1e5e80-f18d-58cc-9082-d3ad7613d5d5"})
MATCH (b:ObjectType {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6e1e5e80-f18d-58cc-9082-d3ad7613d5d5"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ff03b920-8921-553b-9e65-43b47d6e5f2f"})
MATCH (b:ObjectType {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ff03b920-8921-553b-9e65-43b47d6e5f2f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8ad745e0-11de-52bc-b0e7-7d9c44a65fbd"})
MATCH (b:ObjectType {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8ad745e0-11de-52bc-b0e7-7d9c44a65fbd"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4ea9ef97-9b46-57f7-b380-19ba14417512"})
MATCH (b:ObjectType {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4ea9ef97-9b46-57f7-b380-19ba14417512"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e67ef576-a9ee-590c-aed7-55bbfb07a90e"})
MATCH (b:ObjectType {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e67ef576-a9ee-590c-aed7-55bbfb07a90e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e38fd4a8-8844-5f7f-881d-c03719a360f1"})
MATCH (b:ObjectType {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e38fd4a8-8844-5f7f-881d-c03719a360f1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2774c648-bec7-5f4e-b84c-8b27d1dbcb17"})
MATCH (b:ObjectType {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2774c648-bec7-5f4e-b84c-8b27d1dbcb17"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ed556902-6cfa-5cc0-95ec-dc331b071715"})
MATCH (b:ObjectType {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ed556902-6cfa-5cc0-95ec-dc331b071715"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.aee2846f-76c0-5dfe-8a45-063ca69ca014"})
MATCH (b:ObjectType {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.aee2846f-76c0-5dfe-8a45-063ca69ca014"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dae8c100-5521-5e5d-8f89-67a2aecc3ed8"})
MATCH (b:ObjectType {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.dae8c100-5521-5e5d-8f89-67a2aecc3ed8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b91f4758-ca31-5c6c-9108-13a5185e19e8"})
MATCH (b:ObjectType {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b91f4758-ca31-5c6c-9108-13a5185e19e8"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9f4797d1-8d27-5c14-b4fc-a8be99951dda"})
MATCH (b:ObjectType {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9f4797d1-8d27-5c14-b4fc-a8be99951dda"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.41ea891d-5750-537e-ad82-b4e2f13cf156"})
MATCH (b:ObjectType {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.41ea891d-5750-537e-ad82-b4e2f13cf156"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ccf5ac78-127d-5b57-ab07-17303ef34474"})
MATCH (b:ObjectType {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ccf5ac78-127d-5b57-ab07-17303ef34474"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0aa13243-6e12-5369-99fe-2fec2ff37705"})
MATCH (b:ObjectType {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.0aa13243-6e12-5369-99fe-2fec2ff37705"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fc25adfb-eff5-5bdd-b7c2-5b95c1d220be"})
MATCH (b:ObjectType {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.fc25adfb-eff5-5bdd-b7c2-5b95c1d220be"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.decd193a-cc46-5680-be9f-febb09228a99"})
MATCH (b:ObjectType {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.decd193a-cc46-5680-be9f-febb09228a99"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.821438a5-7331-545e-9aeb-64fdb2562d66"})
MATCH (b:ObjectType {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.821438a5-7331-545e-9aeb-64fdb2562d66"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8e4c98df-4840-5974-af04-c3ef2b9a31cf"})
MATCH (b:ObjectType {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8e4c98df-4840-5974-af04-c3ef2b9a31cf"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f0b6a3d5-259e-542e-8870-6466b2bec6a1"})
MATCH (b:ObjectType {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f0b6a3d5-259e-542e-8870-6466b2bec6a1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.93350fb9-1740-523f-9813-c0960330365c"})
MATCH (b:ObjectType {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.93350fb9-1740-523f-9813-c0960330365c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7df13def-087c-540e-bcda-ceaecfd32bb9"})
MATCH (b:ObjectType {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7df13def-087c-540e-bcda-ceaecfd32bb9"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.98751059-d53c-59f1-8607-cc4cf17fe185"})
MATCH (b:ObjectType {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.98751059-d53c-59f1-8607-cc4cf17fe185"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f953f02d-1aa6-54c2-b312-f4e94d63f921"})
MATCH (b:ObjectType {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f953f02d-1aa6-54c2-b312-f4e94d63f921"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f73bf366-40dd-5372-8086-7e8156441910"})
MATCH (b:ObjectType {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f73bf366-40dd-5372-8086-7e8156441910"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ec6ee0ef-532d-5088-8709-f397a57c7406"})
MATCH (b:ObjectType {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ec6ee0ef-532d-5088-8709-f397a57c7406"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.336dd752-04b6-5c2d-8ffe-bef63cdca05f"})
MATCH (b:ObjectType {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.336dd752-04b6-5c2d-8ffe-bef63cdca05f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e565e8cf-748e-562c-b97d-49e3e2520ee0"})
MATCH (b:ObjectType {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e565e8cf-748e-562c-b97d-49e3e2520ee0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.941b13e6-f5af-58d7-bb63-7544ec4518c6"})
MATCH (b:ObjectType {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.941b13e6-f5af-58d7-bb63-7544ec4518c6"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8fb72429-b246-5a4b-9545-a5db346d083b"})
MATCH (b:ObjectType {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8fb72429-b246-5a4b-9545-a5db346d083b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6295b622-ed85-5fcc-bd7a-5f1f8268ec92"})
MATCH (b:ObjectType {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6295b622-ed85-5fcc-bd7a-5f1f8268ec92"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e4d707fc-1e00-5e93-bbe4-20082ae65764"})
MATCH (b:ObjectType {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e4d707fc-1e00-5e93-bbe4-20082ae65764"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.57ec2d42-df03-5e35-843f-93d632c23d8e"})
MATCH (b:ObjectType {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.57ec2d42-df03-5e35-843f-93d632c23d8e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b52cd7bc-9bb8-54d9-9289-4fdf9e010ad9"})
MATCH (b:ObjectType {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b52cd7bc-9bb8-54d9-9289-4fdf9e010ad9"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f064de01-0a8e-5a2c-9d27-34131e82257c"})
MATCH (b:ObjectType {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f064de01-0a8e-5a2c-9d27-34131e82257c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2bef3d05-c2a1-5cc7-bdf6-cb8b6880bbe0"})
MATCH (b:ObjectType {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2bef3d05-c2a1-5cc7-bdf6-cb8b6880bbe0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f3ced9f5-749b-5f6b-bd5c-ba566cecaf91"})
MATCH (b:ObjectType {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f3ced9f5-749b-5f6b-bd5c-ba566cecaf91"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4d4a7ecb-ee91-5e07-995e-97d9f6b3b671"})
MATCH (b:ObjectType {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4d4a7ecb-ee91-5e07-995e-97d9f6b3b671"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f54d3308-5399-5c60-af79-b85b71be1854"})
MATCH (b:ObjectType {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f54d3308-5399-5c60-af79-b85b71be1854"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cd659056-e7ec-5104-97ea-e2cd57b42c7a"})
MATCH (b:ObjectType {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.cd659056-e7ec-5104-97ea-e2cd57b42c7a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5d77cb6b-023a-5ed5-9136-831e82b76222"})
MATCH (b:ObjectType {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.5d77cb6b-023a-5ed5-9136-831e82b76222"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.886092ec-408a-5f52-a997-83634fa22930"})
MATCH (b:ObjectType {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.886092ec-408a-5f52-a997-83634fa22930"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d5688a52-1c68-59b7-b679-fb7817823378"})
MATCH (b:ObjectType {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d5688a52-1c68-59b7-b679-fb7817823378"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.23d8e9d5-106a-5535-b5ee-62bc95833d90"})
MATCH (b:ObjectType {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.23d8e9d5-106a-5535-b5ee-62bc95833d90"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8cd5b0de-8f52-58e4-b1b4-202930f1b617"})
MATCH (b:ObjectType {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8cd5b0de-8f52-58e4-b1b4-202930f1b617"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.53ee5557-cb47-5699-acc6-22ee050ef9b1"})
MATCH (b:ObjectType {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.53ee5557-cb47-5699-acc6-22ee050ef9b1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.089c94a3-feee-5f09-a953-2a63dfabfa7c"})
MATCH (b:ObjectType {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.089c94a3-feee-5f09-a953-2a63dfabfa7c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6eeb8d18-c624-5c17-804a-3008919cab6a"})
MATCH (b:ObjectType {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6eeb8d18-c624-5c17-804a-3008919cab6a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a63ad6ad-9c9b-5fc7-a623-427668248822"})
MATCH (b:ObjectType {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a63ad6ad-9c9b-5fc7-a623-427668248822"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a1c6e86b-792d-51bc-94be-eefbf6f0c859"})
MATCH (b:ObjectType {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a1c6e86b-792d-51bc-94be-eefbf6f0c859"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b925391a-f6b5-559f-9620-b49a8d8c6df1"})
MATCH (b:ObjectType {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b925391a-f6b5-559f-9620-b49a8d8c6df1"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7648ef3b-d6d2-5c20-bc0d-f46204559c25"})
MATCH (b:ObjectType {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.7648ef3b-d6d2-5c20-bc0d-f46204559c25"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.58bf643d-f074-597f-891b-9ba72f4e5135"})
MATCH (b:ObjectType {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.58bf643d-f074-597f-891b-9ba72f4e5135"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c711faeb-0463-5f78-8b07-9aa652256ff9"})
MATCH (b:ObjectType {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.c711faeb-0463-5f78-8b07-9aa652256ff9"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1130dc2a-874b-510e-8e77-0ebf3513938e"})
MATCH (b:ObjectType {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1130dc2a-874b-510e-8e77-0ebf3513938e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a463b602-c8d9-565e-be87-40c58e97a422"})
MATCH (b:ObjectType {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a463b602-c8d9-565e-be87-40c58e97a422"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bf542483-0a8d-50d9-8d3f-e83e1f70d93e"})
MATCH (b:ObjectType {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.bf542483-0a8d-50d9-8d3f-e83e1f70d93e"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.55c9543d-be89-5f3c-9663-5c460c9d7cb9"})
MATCH (b:ObjectType {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.55c9543d-be89-5f3c-9663-5c460c9d7cb9"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f2da10d2-8111-5888-a2eb-62521b9d1793"})
MATCH (b:ObjectType {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f2da10d2-8111-5888-a2eb-62521b9d1793"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9ab1c690-6027-5516-a426-d4e759ada357"})
MATCH (b:ObjectType {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9ab1c690-6027-5516-a426-d4e759ada357"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3384f0aa-15f6-5f34-a349-9a056f45e273"})
MATCH (b:ObjectType {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.3384f0aa-15f6-5f34-a349-9a056f45e273"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4ce87d95-7da9-5b91-b5a9-e5b3bac9e88a"})
MATCH (b:ObjectType {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4ce87d95-7da9-5b91-b5a9-e5b3bac9e88a"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d9c55e72-36e0-5d40-80a8-688f82968060"})
MATCH (b:ObjectType {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d9c55e72-36e0-5d40-80a8-688f82968060"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f6d00ca4-45d8-5170-860d-610c581b8c90"})
MATCH (b:ObjectType {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f6d00ca4-45d8-5170-860d-610c581b8c90"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4811071b-f31d-587a-8046-f30f3b34c2a0"})
MATCH (b:ObjectType {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.4811071b-f31d-587a-8046-f30f3b34c2a0"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6fce9844-0936-50ff-9a15-62166f60200f"})
MATCH (b:ObjectType {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6fce9844-0936-50ff-9a15-62166f60200f"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2fda8d93-fb6a-5a70-a58f-67fd6062e934"})
MATCH (b:ObjectType {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2fda8d93-fb6a-5a70-a58f-67fd6062e934"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1d20aafe-4a75-5351-a374-f6c29b94e038"})
MATCH (b:ObjectType {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.1d20aafe-4a75-5351-a374-f6c29b94e038"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.22c08ad4-843c-5f08-84a9-d2198386b704"})
MATCH (b:ObjectType {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.22c08ad4-843c-5f08-84a9-d2198386b704"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2a160501-5422-54e2-b05b-f795b85a49b2"})
MATCH (b:ObjectType {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.2a160501-5422-54e2-b05b-f795b85a49b2"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.1a8dd20c-6782-4e6c-801b-c17d7e1c5b9f"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ae2dbee9-56bf-5bc9-ad44-b045669e94e3"})
MATCH (b:ObjectType {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.ae2dbee9-56bf-5bc9-ad44-b045669e94e3"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.641e8145-15a2-43a9-a583-cc165037ddff"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8b0c12e2-57a6-5e42-930b-a19c3b29dd1c"})
MATCH (b:ObjectType {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.8b0c12e2-57a6-5e42-930b-a19c3b29dd1c"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.57a65fd9-4953-4696-8da5-54a16126d448"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.84300c22-a035-5ca4-be8f-0e6809aa0a7b"})
MATCH (b:ObjectType {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.84300c22-a035-5ca4-be8f-0e6809aa0a7b"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.bfe25aa3-a020-4de3-a5bc-19e2cc6a97ed"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d8717031-f6b8-551c-96f7-dc92a1a549d9"})
MATCH (b:ObjectType {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.d8717031-f6b8-551c-96f7-dc92a1a549d9"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.6169a1e2-a57a-4e5e-b1cb-975aae6ee524"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e40a6e29-ce3b-5990-9be1-c475bbdc009d"})
MATCH (b:ObjectType {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e40a6e29-ce3b-5990-9be1-c475bbdc009d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.c0241bdb-3adc-4002-a026-0f1ef40aa5c2"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6926dc82-8694-529e-ba1a-53cdf0aae68d"})
MATCH (b:ObjectType {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.6926dc82-8694-529e-ba1a-53cdf0aae68d"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.0a17a4c3-5eff-4d74-a5fc-4bd7c4bc49a7"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f39cd6e4-6e8f-55fb-819d-97c6a34fc716"})
MATCH (b:ObjectType {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.f39cd6e4-6e8f-55fb-819d-97c6a34fc716"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.b56510d1-bf31-4257-b994-c180ef108f6c"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.689acb68-4fe6-5f00-952e-691628e32194"})
MATCH (b:ObjectType {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.689acb68-4fe6-5f00-952e-691628e32194"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.ede11c68-d17b-4a2c-9118-2c8560f4dce3"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e4d78cf5-635b-5f5e-b81d-bae8d0a560cb"})
MATCH (b:ObjectType {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.e4d78cf5-635b-5f5e-b81d-bae8d0a560cb"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.517bca9f-27a2-42a7-8e8d-b43f5715b960"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b6df9d8c-a74c-5936-81f1-50c78545dc35"})
MATCH (b:ObjectType {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.b6df9d8c-a74c-5936-81f1-50c78545dc35"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.fc680db5-94ca-4c38-bd22-160eed32c494"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9acede8a-22ff-53de-996c-8367724eb533"})
MATCH (b:ObjectType {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.9acede8a-22ff-53de-996c-8367724eb533"})
MATCH (b:SharedPropertyType {rid: "ri.shprop.729d3343-3a86-4b1e-a785-b206e9f0b9d1"})
MERGE (a)-[r:BASED_ON]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a8afde92-44e2-512e-b83d-744e3d7e7176"})
MATCH (b:ObjectType {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
MERGE (a)-[r:BELONGS_TO]->(b);

MATCH (a:PropertyType {rid: "ri.prop.a8afde92-44e2-512e-b83d-744e3d7e7176"})
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

MATCH (a:ObjectType {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
MATCH (b:InterfaceType {rid: "ri.iface.0e8105d4-c1c0-494c-bb77-572615eae82d"})
MERGE (a)-[r:IMPLEMENTS]->(b);

MATCH (a:ObjectType {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
MATCH (b:InterfaceType {rid: "ri.iface.ed3c7676-0088-496f-8c4f-3bd7f5bdf517"})
MERGE (a)-[r:IMPLEMENTS]->(b);
