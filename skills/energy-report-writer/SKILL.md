# Skill: energy-report-writer

## 描述
生成宿舍用电节能周报或节能倡议书。附带模板 `template.md`，约束"数字只能来自工具返回 + calculator 计算 + critic 审稿"。

## 何时使用
当用户请求"生成本周节能周报""写一份节能倡议书""出一份用电分析报告"时使用本 Skill。

## 执行步骤
1. 用 `write_todos` 列出计划：
   - 取本周全校楼栋用电排名（MCP 工具 `building_power_ranking`）
   - 取代表性宿舍近 4 周用电对比（工具 `query_dorm_power`）
   - 用 `calculator` 复核合计、均值、环比
   - 读取本模板 `template.md`
   - 填写模板，所有数字必须来自工具返回或 calculator 计算
   - 用 `write_file` 写入 `/workspace/energy-report-{日期}.md`
   - 委派 `critic` 子代理审稿，重点校验数字一致性
   - 根据 critic 反馈修改后定稿

2. 数据约束：
   - **所有数字只能来自工具返回或 calculator 计算**，不要凭记忆编造任何用电量、排名、百分比。
   - 制度引用需注明「以学校正式发文为准」。

3. 文件命名：`energy-report-YYYY-MM-DD.md`（用 `get_current_time` 获取当前日期）

4. 写完后告诉用户文件路径，并在侧边栏可预览/下载。
