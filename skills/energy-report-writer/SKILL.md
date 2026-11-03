---
name: energy-report-writer
description: 生成宿舍用电节能周报或节能倡议书。附带模板 template.md，约束"数字只能来自工具返回 + calculator 计算 + critic 审稿"。
---

# Skill: energy-report-writer

## 适用场景
用户要求"生成节能周报""写用电报告""节能倡议书"时触发。

## 工作步骤
1. 用 `get_current_time` 获取当前日期和学期周数
2. 用 `building_power_ranking`（MCP 工具）获取全校最新一周排名
3. 用 `query_dorm_power` 抽查 2-3 栋典型楼栋的用电趋势
4. 读取 `template.md` 模板，把工具返回的真实数字填入
5. 用 `write_file` 把报告写到 `/workspace/节能周报-第N周.md`
6. 委派 `critic` 子代理审稿，根据反馈修正

## 约束
- 所有数字（用电量、排名、合计）只能来自工具返回或 calculator 计算
- 不得凭记忆编造任何数据
- 制度类建议注明「以学校正式发文为准」
