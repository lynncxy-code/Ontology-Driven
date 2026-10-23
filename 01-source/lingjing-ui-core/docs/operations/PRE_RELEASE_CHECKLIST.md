# 发版前检查清单（Phase 1）

> 说明：本文档仅作为后续若发版时的轻量检查清单，不代表当前已正式发版。

---

## 1. 版本与真值源同步

- [ ] `SKILL.md` frontmatter `metadata.version` 为目标版本
- [ ] `package.json.version`、`skill_version.json.version` 与主版本一致
- [ ] `TRUTH_SOURCES.md`、`docs/DOCS_STATUS_SUMMARY.md` 的版本说明未漂移

## 2. 主线回归与验证

- [ ] 运行 `npm run audit:phase1-regression`
- [ ] 13 个样例全部执行完成
- [ ] 正例全部 PASS、反例按预期 FAIL
- [ ] runner 最终汇总为“all samples matched expected PASS/FAIL state”
- [ ] 已复核 `docs/PHASE1_USABILITY_VALIDATION.md`，确认主线在代表性真实任务下的可用度结论仍成立
- [ ] 已复核 `docs/PHASE1_GENERATION_PLAYBACK.md`，确认代表性生成回放样本的审计结果与当前回归状态一致
- [ ] 已复核 `docs/PHASE2_GENERATION_STRESSCHECK.md`，确认更大样本生成压测未暴露新的主线结构性问题


## 3. 规则与解释层一致性

- [ ] `scene_coverage_matrix.yml`、`skill_version.json`、`data/task_router.json`、`data/template_router.json` 之间无分级/路由漂移
- [ ] `examples/README.md` 中默认 canonical、limited、demo、blacklist、anti_pattern 的口径一致
- [ ] `docs/STABILITY_STATUS.md` 仍仅作为跳转说明；正式状态表仍唯一指向 `TRUTH_SOURCES.md §6`

## 4. 交付文档完整性

- [ ] `docs/PHASE1_REGRESSION_BASELINES.md` 为当前回归基线
- [ ] `docs/PHASE1_VALIDATION_REPORT.md` 为当前正式验证记录
- [ ] `docs/PHASE1_USABILITY_VALIDATION.md` 为当前真实任务可用度验证记录
- [ ] `docs/PHASE1_GENERATION_PLAYBACK.md` 为当前代表性生成回放记录
- [ ] `docs/PHASE2_GENERATION_STRESSCHECK.md` 为当前更大样本生成压测记录
- [ ] `docs/RELEASE_READINESS_SUMMARY.md` 已根据上述文档与最新主线状态更新
- [ ] `docs/DOCS_STATUS_SUMMARY.md` 已将上述文档挂入导航，路径与状态说明一致
- [ ] `docs/PRE_RELEASE_CHECKLIST.md` 内容与当前仓库状态一致


## 5. 发布阻断条件

以下任一项不满足时，不建议进入发版动作：

- [ ] 回归 runner 未完整跑完 13 个样例
- [ ] 任一样例结果与预期 PASS/FAIL 不一致
- [ ] 真值源与解释层存在明显冲突
- [ ] 稳定度状态表正式入口出现双份维护
