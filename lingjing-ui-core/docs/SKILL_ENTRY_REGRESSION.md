# SKILL.md 主入口回归检查

> 范围：仅检查 `SKILL.md` 在瘦身后的入口职责、阅读顺序、跳转链路与引用稳定性；不重写规则，不改 `scene_coverage_matrix.yml` / router / guard / 模板。
> 检查日期：2026-04-06

---

## 1. 回归结论

本轮回归结果：**通过**。

`SKILL.md` 已基本回到“AI 第一入口”的角色：
- 主文档仍保留全局铁律、核心执行规约、Level 1/2/3 判断框架、黑名单 / fallback、质量检查清单；
- `ue5_overlay` 与 `b_system` 已收缩为“关键原则 + 继续深读路径”；
- `0.1 按任务阅读顺序` 已能指导 AI 先读主规则，再按场景深读；
- 普通任务不再需要默认全量读取重场景正文与验证留档层。

---

## 2. 检查项摘要

### 2.1 主入口职责
- 通过：主文档主体集中在 `5 条铁律`、`0.0`、`0.1`、`1.1~1.4`、`3.0`、`5.0`、`6.0`。
- 通过：未再把 `b_system` / `ue5_overlay` 的布局细则完整堆回主文档。

### 2.2 入口 + 跳转
- 通过：`1.2` 可继续跳转到 `docs/operations/ue5-overlay-layout-playbook.md`、`docs/reference/ue5-template-map.md` 与对应 `examples/ue5-overlay/*.html`。
- 通过：`1.3` 可继续跳转到 `docs/operations/b-system-layout-playbook.md`、`docs/reference/system-template-map.md`、`docs/reference/b-system-composition-recipes.md`。
- 通过：路径已复核，无“主文档删薄后无处继续读”的断链。

### 2.3 按任务阅读顺序
- 通过：所有任务先读 `SKILL.md`、`scene_coverage_matrix.yml`、调用方项目结构，再按场景继续深读。
- 通过：`website` / `presentation` / `ai_assistant` 已明确为轻读策略，不默认全量通读 playbook / validation。
- 通过：何时需要读 `validation` / `EXTENSION_GUARD` / `TEMPLATE_ASSET_REFERENCE_MAP` 已写明。

### 2.4 锚点与引用稳定性
- 通过：主链引用已从碎片小锚点转为 `§0.0 / §0.1 / §1.2 / §1.3 / §3.0 / §5.0`。
- 已修正：`docs/reference/b-system-composition-recipes.md` 中旧 canonical 路径已改回真实路径。
- 已修正：`scripts/skill-audit.js` 中残留旧锚点提示已改为稳定章节引用。

---

## 3. 是否建议继续扩张

不建议在本轮继续扩张。

当前残余问题已降到很小：主入口职责、阅读顺序、跳转链路、锚点稳定性都已达成本轮目标；后续若继续优化，应另开独立任务，而不是在本轮回归检查中继续扩写。

---

## 4. 一句话判断

**这轮优化后，`SKILL.md` 已更像“AI 第一入口”，而不是“全文总集”。**
