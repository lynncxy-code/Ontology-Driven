const assert=require('node:assert/strict');
const {buildFolders,filterAssets}=require('../ue_asset_picker.js');
const assets=[
  {object_path:'/Game/Models/Machine/SM_A.SM_A',asset_kind:'StaticMesh',display_name:'控制柜'},
  {object_path:'/Game/Models/Machine/Parts/SK_A.SK_A',asset_kind:'SkeletalMesh',display_name:'机械臂'},
  {object_path:'/Game/Models/Machine2/BP_A.BP_A',asset_kind:'Blueprint',display_name:'自动门'},
];
const catalog={assets,roots:['/Game/Models'],available_folders:['/Game/Empty']};
const tree=buildFolders(catalog);
assert.equal(tree.roots[0].label,'Content');
assert.equal(tree.nodes.get('/Game').count,3);
assert.equal(tree.nodes.get('/Game/Models/Machine').count,2);
assert.equal(tree.nodes.get('/Game/Empty').count,0);
assert.deepEqual(tree.nodes.get('/Game/Models').children.map(n=>n.path),['/Game/Models/Machine','/Game/Models/Machine2']);
assert.equal(filterAssets(assets,'/Game/Models',false,'','').length,0);
assert.equal(filterAssets(assets,'/Game/Models/Machine',false,'','').length,1);
assert.equal(filterAssets(assets,'/Game/Models/Machine',true,'','').length,2);
assert.equal(filterAssets(assets,'/Game/Models',true,'SkeletalMesh','机械')[0].object_path,assets[1].object_path);
assert.equal(filterAssets(assets,'/Game/Models/Machine',true,'Blueprint','').length,0);
assert.equal(filterAssets(assets,'/Game/Models',true,'','Machine2').length,1);
assert.equal(buildFolders({}).roots.length,0);
console.log('PASS: folder hierarchy, ancestors, counts, direct/recursive scope, sibling isolation, category and search');
