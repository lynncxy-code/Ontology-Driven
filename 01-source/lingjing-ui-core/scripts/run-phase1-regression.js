const path = require('path');
const { spawnSync } = require('child_process');

// Resolve project root and audit script path based on this file location
const projectRoot = path.resolve(__dirname, '..');
const auditScript = path.join(__dirname, 'skill-audit.js');

// Phase 1 regression cases: b_system list / advanced_list / detail + ue5_overlay Mode1/2/3/minimal
// NOTE: This runner is designed to always execute all samples.
// It only fails (exit code 1) when actual PASS/FAIL does not match the expected outcome.

const tests = [
  // b_system_list
  {
    id: 'b_system_list:top_filters',
    file: 'examples/b-system/b-system-task-list-top-filters.html',
    scene: 'b_system',
    task: null,
    expectedPass: true,
  },
  {
    id: 'b_system_list:left_filter_panel',
    file: 'examples/b-system/b-system-list-with-left-filter-panel.html',
    scene: 'b_system',
    task: null,
    expectedPass: false,
  },
  // b_system_advanced_list
  {
    id: 'b_system_advanced_list:with_shell',
    file: 'examples/b-system/b-system-advanced-list-with-left-filter-panel.html',
    scene: 'b_system',
    task: 'b_system_advanced_list',
    expectedPass: true,
  },
  {
    id: 'b_system_advanced_list:without_shell',
    file: 'examples/b-system/b-system-advanced-list-without-advanced-shell.html',
    scene: 'b_system',
    task: 'b_system_advanced_list',
    expectedPass: false,
  },
  // b_system_detail
  {
    id: 'b_system_detail:order',
    file: 'examples/b-system/b-system-detail-order.html',
    scene: 'b_system',
    task: 'b_system_detail',
    expectedPass: true,
  },
  {
    id: 'b_system_detail:with_dashboard_kpi',
    file: 'examples/b-system/b-system-detail-with-dashboard-kpi.html',
    scene: 'b_system',
    task: 'b_system_detail',
    expectedPass: false,
  },
  // ue5_overlay Mode 2
  {
    id: 'ue5_overlay_mode2:quality_tracking',
    file: 'examples/ue5-overlay/ue5_overlay_quality_tracking.html',
    scene: 'ue5_overlay',
    task: null,
    expectedPass: true,
  },
  {
    id: 'ue5_overlay_mode2:with_dock',
    file: 'examples/ue5-overlay/ue5_overlay_quality_tracking_mode2_with_dock.html',
    scene: 'ue5_overlay',
    task: null,
    expectedPass: false,
  },
  // ue5_overlay Mode 3
  {
    id: 'ue5_overlay_mode3:dashboard',
    file: 'examples/ue5-overlay/ue5_overlay_dashboard.html',
    scene: 'ue5_overlay',
    task: null,
    expectedPass: true,
  },
  {
    id: 'ue5_overlay_mode3:too_light',
    file: 'examples/ue5-overlay/ue5_overlay_dashboard_mode3_too_light.html',
    scene: 'ue5_overlay',
    task: null,
    expectedPass: false,
  },
  // ue5_overlay Mode 1
  {
    id: 'ue5_overlay_mode1:data_viz',
    file: 'examples/ue5-overlay/ue5_overlay_data_viz.html',
    scene: 'ue5_overlay',
    task: null,
    expectedPass: true,
  },
  {
    id: 'ue5_overlay_mode1:data_viz_no_hud',
    file: 'examples/ue5-overlay/ue5_overlay_data_viz_no_hud.html',
    scene: 'ue5_overlay',
    task: null,
    expectedPass: false,
  },
  // ue5_overlay minimal overlay
  {
    id: 'ue5_overlay_minimal:no_hud',
    file: 'examples/ue5-overlay/ue5_overlay_minimal_no_hud.html',
    scene: 'ue5_overlay',
    task: null,
    expectedPass: true,
  },
];

function runTest(test) {
  const filePath = path.join(projectRoot, test.file);
  const args = [auditScript, filePath, '--scene', test.scene];
  if (test.task) {
    args.push('--task', test.task);
  }

  console.log('\n============================================================');
  console.log(`Running: ${test.id}`);
  console.log(`  file   = ${filePath}`);
  console.log(`  scene  = ${test.scene}` + (test.task ? `, task = ${test.task}` : ''));
  console.log(`  expect = ${test.expectedPass ? 'PASS' : 'FAIL'}`);

  const result = spawnSync('node', args, { stdio: 'inherit' });

  const exitCode = typeof result.status === 'number' ? result.status : -1;
  const actualPass = exitCode === 0;
  const match = actualPass === test.expectedPass;

  console.log(`\n[RESULT] ${test.id}`);
  console.log(`  expected_pass = ${test.expectedPass}`);
  console.log(`  actual_pass   = ${actualPass}`);
  console.log(`  exit_code     = ${exitCode}`);
  console.log(`  match         = ${match ? 'YES' : 'NO'}`);

  return { ...test, filePath, exitCode, actualPass, match };
}

function main() {
  console.log('▶ Phase 1 regression runner — b_system + ue5_overlay');
  console.log('  project_root  =', projectRoot);
  console.log('  audit_script  =', auditScript);
  console.log('  total samples =', tests.length);

  const results = tests.map(runTest);

  console.log('\n============================================================');
  console.log('Summary (id | expected | actual | exit | match)');
  results.forEach(r => {
    const expected = r.expectedPass ? 'PASS' : 'FAIL';
    const actual = r.actualPass ? 'PASS' : 'FAIL';
    console.log(
      `- ${r.id} | expected=${expected} | actual=${actual} | exit=${r.exitCode} | match=${r.match ? 'YES' : 'NO'}`
    );
  });

  const allMatch = results.every(r => r.match);
  if (!allMatch) {
    console.error('\n❌ Phase 1 regression: some samples did NOT match expected PASS/FAIL state.');
    process.exit(1);
  }

  console.log('\n✅ Phase 1 regression: all samples matched expected PASS/FAIL state.');
  process.exit(0);
}

main();
