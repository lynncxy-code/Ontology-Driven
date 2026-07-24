// OntoTwin ZHHZ UE 迁移扩展属性（x_ 前缀）；官方生成器重灌不会覆盖

MATCH (n:ObjectType {rid: "ri.obj.a34b5519-371b-5015-a77e-6942c9c6d8c2"})
SET n.x_block_name = "zhhz.fixed_wing_aircraft", n.x_source = "ue_migration:ZHHZ", n.x_origin = "ontotwin";

MATCH (n:ObjectType {rid: "ri.obj.94519b0e-bc7e-5593-b2d9-dc9bfb73f4b7"})
SET n.x_block_name = "zhhz.rotorcraft", n.x_source = "ue_migration:ZHHZ", n.x_origin = "ontotwin";

MATCH (n:ObjectType {rid: "ri.obj.b9131966-967c-5b35-85f9-3f2dee043859"})
SET n.x_block_name = "zhhz.unmanned_new_aircraft", n.x_source = "ue_migration:ZHHZ", n.x_origin = "ontotwin";

MATCH (n:ObjectType {rid: "ri.obj.4d134bc7-50f2-59bf-ae3a-a2cc37f46314"})
SET n.x_block_name = "zhhz.aviation_weapon", n.x_source = "ue_migration:ZHHZ", n.x_origin = "ontotwin";

MATCH (n:ObjectType {rid: "ri.obj.df871a52-4714-5f8b-b094-453283d3238c"})
SET n.x_block_name = "zhhz.avionics_sensor", n.x_source = "ue_migration:ZHHZ", n.x_origin = "ontotwin";

MATCH (n:ObjectType {rid: "ri.obj.9da63d32-130c-565d-8011-508487e132b8"})
SET n.x_block_name = "zhhz.cockpit_simulator", n.x_source = "ue_migration:ZHHZ", n.x_origin = "ontotwin";

MATCH (n:ObjectType {rid: "ri.obj.96f556ed-25fc-5ed9-8a48-9543e2757665"})
SET n.x_block_name = "zhhz.display_control_terminal", n.x_source = "ue_migration:ZHHZ", n.x_origin = "ontotwin";

MATCH (n:ObjectType {rid: "ri.obj.663385f4-f703-59e9-a7f2-f6b2aee96fc5"})
SET n.x_block_name = "zhhz.aircraft_component", n.x_source = "ue_migration:ZHHZ", n.x_origin = "ontotwin";
