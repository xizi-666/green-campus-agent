# 绿电管家：LangChain Deep Agents 绿色校园节能助手（智谱 GLM + Skills + MCP）

本项目用 [LangChain Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) 搭建一个「绿色校园节能助手」智能体。
模型通过智谱开放平台的 OpenAI 兼容接口调用（GLM-4-Air），并接入了 Skills（技能）、MCP（模型上下文协议）、子代理、长期记忆和文件系统。

提供两种界面：网页版 `web.py` 和命令行版 `app.py`，两者共用同一个 Agent。

命令行运行效果：

```
正在初始化 Agent（加载 MCP 服务器、Skills、Memory）……
模型       glm-4-air
自定义工具 get_current_time, calculator, query_dorm_power, waste_sorting_lookup
MCP 工具   list_buildings, building_power_ranking, search_energy_policy
Skills     energy-report-writer, sorting-advisor
子代理     data-analyst, critic, general-purpose

你：查一下玉兰苑1号楼302最近四周的用电量，算算总共多少度
[主Agent] 调用工具 query_dorm_power {"building":"玉兰苑1号楼","room":"302","weeks":4}
助教：玉兰苑1号楼302最近四周的用电量总共为167.6度……
```

---

## 一、项目简介

**绿电管家**是一个面向住校学生和宿管后勤的 AI 节能助手，核心能力：

| 能力 | 说明 |
|---|---|
| 查宿舍用电 | 查某栋某间最近 N 周的用电量，含合计、周均、环比 |
| 全校用电排名 | 按间均用电量降序排列全校楼栋，定位高耗能楼栋 |
| 垃圾分类查询 | 30 种常见物品的分类和投放提示，查不到不编造 |
| 节能制度检索 | 检索空调温度、用电定额等校园节能制度条目 |
| 节能周报生成 | 自动取数 + 模板填充 + 审稿，生成 Markdown 周报 |

所有数字（用电量、排名、合计）一律来自工具返回或 calculator 计算，**不凭记忆编造**。

---

## 二、目录结构

```
green-campus-agent/
├── web.py               # 网页界面（Streamlit）
├── app.py               # 命令行界面
├── agent.py             # 组装 Deep Agent，系统提示词和子代理定义
├── history.py           # 会话历史存储（SQLite）
├── tools.py             # 4 个自定义工具（查用电/垃圾分类/计算器/日期）
├── mcp_server.py        # 本地 MCP 服务器，3 个工具（楼栋/排名/制度）
├── mcp_servers.json     # MCP 服务器配置
├── AGENTS.md            # 长期记忆，每次对话加载
├── skills/              # 技能目录
│   ├── energy-report-writer/
│   │   ├── SKILL.md     # 节能周报技能（带 YAML 头）
│   │   └── template.md  # 周报模板
│   └── sorting-advisor/
│       └── SKILL.md     # 垃圾分类讲解技能
├── dataset/             # 数据集
│   ├── power_data.json       # 4 栋楼 × 10 间 × 8 周用电数据
│   ├── waste_sorting.json    # 30 种垃圾分类数据
│   └── energy_policy.json    # 8 条校园节能制度
├── workspace/           # Agent 唯一可写的目录，生成的周报都在这里
├── data/                # 运行后自动生成：checkpoints.db、sessions.db
├── requirements.txt
├── .env.example         # 环境变量模板
└── .env                 # 真实密钥（已被 .gitignore 忽略）
```

---

## 三、启动指南

### 1. 准备环境

需要 Python 3.10 及以上，推荐 3.12。

```bash
cd green-campus-agent
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 2. 配置 API Key

本项目使用**智谱开放平台**的 GLM 系列模型（注册地址 https://bigmodel.cn/ ，GLM-4-Flash 长期免费）。

```bash
cp .env.example .env      # Windows CMD 用：copy .env.example .env
```

打开 `.env`，填入你的智谱 API Key：

| 变量 | 说明 | 默认值 |
|---|---|---|
| `DASHSCOPE_API_KEY` | 智谱 API Key（格式 `xxxxx.yyyyy`） | 必填 |
| `LLM_BASE_URL` | OpenAI 兼容接口地址 | `https://open.bigmodel.cn/api/paas/v4` |
| `LLM_MODEL` | 主 Agent 模型 | `glm-4-air`（推荐，0.001元/千token） |
| `SUBAGENT_MODEL` | 子代理模型，留空则同主模型 | 空 |
| `LLM_TEMPERATURE` | 采样温度 | `0.3` |

> **注意**：`.env` 已被 `.gitignore` 忽略，不会提交到 Git。

### 3. 运行网页版（推荐）

```bash
streamlit run web.py
# 未激活虚拟环境时：.venv\Scripts\python.exe -m streamlit run web.py
```

浏览器自动打开 http://localhost:8501 ，页面包括：

| 区域 | 内容 |
|---|---|
| 主区域 | 对话窗口，回答逐字流式输出；首页有 5 个示例问题按钮 |
| 执行过程 | 每条回答上方可展开，实时显示工具调用和返回结果 |
| 侧边栏·历史会话 | 列出所有保存过的会话，点击即可切换并继续追问 |
| 侧边栏·工具与能力 | 当前模型、自定义工具、MCP 工具、Skills、子代理 |
| 侧边栏·任务清单 | Agent 用 `write_todos` 列出的计划及完成状态 |
| 侧边栏·产出文件 | `workspace/` 中的文件，可预览并下载 |

### 4. 推荐体验的问题

| 问题 | 会用到的能力 |
|---|---|
| 查一下玉兰苑1号楼302最近四周的用电量，算算总共多少度 | query_dorm_power + calculator |
| 上周哪栋楼用电最多？给我一份全校用电排名 | MCP 工具 building_power_ranking |
| 外卖餐盒、废旧电池和快递纸箱分别是什么垃圾？ | waste_sorting_lookup + Skill 汇总 |
| 空调开多少度有什么规定？ | MCP 工具 search_energy_policy |
| 帮我生成本周的宿舍用电节能周报 | Skill + 待办规划 + 子代理 + 写文件 |

---

## 四、演示话术

现场演示时依次输入以上 5 个问题，每个回答上方展开「执行过程」面板，可以看到工具名、参数和返回值——这是项目最大的亮点：**所有数字都来自工具，不是模型编造的**。

---

## 五、技术架构

```
web.py / app.py ──> agent.build_agent()
                      │
                      ├─ build_model()          ChatOpenAI(base_url=智谱开放平台)
                      ├─ load_mcp_tools()       读取 mcp_servers.json，启动 MCP 服务器
                      ├─ build_subagents()      data-analyst / critic
                      ├─ build_checkpointer()   AsyncSqliteSaver
                      ├─ FilesystemBackend      把项目目录映射为 Agent 眼中的 "/"
                      └─ create_deep_agent(model, tools, system_prompt, subagents,
                                           skills=["/skills/"], memory=["/AGENTS.md"],
                                           backend, permissions, checkpointer)
```

| 组件 | 本项目配置 |
|---|---|
| 模型 | 智谱 GLM-4-Air（兼容 OpenAI 接口） |
| 自定义工具 | get_current_time, calculator, query_dorm_power, waste_sorting_lookup |
| MCP 工具 | list_buildings, building_power_ranking, search_energy_policy |
| Skills | energy-report-writer（节能周报）, sorting-advisor（垃圾分类讲解） |
| 子代理 | data-analyst（数据分析）, critic（审稿）, general-purpose（通用） |
| 记忆 | AGENTS.md（绿电管家身份和场景规则） |
| 文件系统 | Agent 只能写 `/workspace/`，不能修改源码 |

---

## 六、常见问题

| 现象 | 原因与解决 |
|---|---|
| `401` 或 `令牌已过期` | Key 填错，到智谱控制台重新复制完整 Key（格式 `xxxxx.yyyyy`） |
| `model not found` | 模型名拼写错误，可用 `glm-4-air` / `glm-4-flash` / `glm-4` |
| 网页端口被占用 | `streamlit run web.py --server.port 8502` |
| 改了 agent.py 网页没变化 | Agent 被缓存，按 Ctrl+C 停止后重新 `streamlit run` |
| 回答说"无法获取" | GLM-4-Flash 推理能力弱，换 `glm-4-air` 或 `glm-4` |

## 参考资料

- Deep Agents 文档：https://docs.langchain.com/oss/python/deepagents/overview
- Deep Agents 源码：https://github.com/langchain-ai/deepagents
- MCP 适配器：https://github.com/langchain-ai/langchain-mcp-adapters
- 智谱开放平台：https://bigmodel.cn/
- Agent Skills 规范：https://agentskills.io
