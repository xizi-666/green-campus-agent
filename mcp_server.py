"""
绿电管家 · 本地 MCP 服务器（FastMCP，stdio 传输）
====================================================

服务器名：green-campus
提供 3 个工具：
- list_buildings         楼栋 / 房间清单
- building_power_ranking  任意周全校用电排名（按间均降序）
- search_energy_policy    制度关键词检索，每条带来源

由 agent.py 按 mcp_servers.json 中的配置自动启动，
通过标准输入输出与 Agent 通信。

单独调试：
    npx @modelcontextprotocol/inspector python mcp_server.py
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("green-campus", log_level="WARNING")

DATA_DIR = Path(__file__).resolve().parent / "dataset"


def _load_power_data() -> dict:
    path = DATA_DIR / "power_data.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_policy_data() -> list:
    path = DATA_DIR / "energy_policy.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


@mcp.tool()
def list_buildings() -> dict:
    """列出全部宿舍楼栋及每栋楼的房间清单。回答与"有哪些楼栋""某栋有哪些房间"有关的问题时使用。"""
    data = _load_power_data()
    rooms_map = data.get("rooms", {})
    result = {}
    for bld in data.get("buildings", []):
        result[bld] = {
            "room_count": len(rooms_map.get(bld, [])),
            "rooms": rooms_map.get(bld, []),
        }
    return result


@mcp.tool()
def building_power_ranking(week: int = 0) -> str:
    """统计某一周全校各楼栋的用电排名（按间均用电量降序）。

    Args:
        week: 周数（1-8），例如 8 表示第 8 周。不传或传 0 时默认返回最新一周（第 8 周）。
    """
    data = _load_power_data()
    power_map = data.get("data", {})
    rooms_map = data.get("rooms", {})

    # 找最新一周的周数
    max_week = 0
    for bld, rooms in power_map.items():
        for room, records in rooms.items():
            if len(records) > max_week:
                max_week = len(records)
    if week <= 0 or week > max_week:
        week = max_week
    week_label = "最新" if week == max_week else f"第 {week}"
    week_for_records = week

    rankings = []
    for bld in data.get("buildings", []):
        total = 0
        count = 0
        for room, records in power_map.get(bld, {}).items():
            if week <= len(records):
                total += records[week - 1]
                count += 1
        avg = round(total / count, 1) if count > 0 else 0
        rankings.append({
            "building": bld,
            "total_kwh": round(total, 1),
            "room_count": count,
            "avg_kwh_per_room": avg,
        })

    rankings.sort(key=lambda x: x["avg_kwh_per_room"], reverse=True)

    lines = [f"第 {week} 周全校宿舍楼栋用电排名（按间均降序）："]
    for i, r in enumerate(rankings, 1):
        lines.append(f"  {i}. {r['building']} — 间均 {r['avg_kwh_per_room']} 度，总计 {r['total_kwh']} 度（{r['room_count']} 间）")
    return "\n".join(lines)


@mcp.tool()
def search_energy_policy(keyword: str) -> str:
    """检索校园节能制度条目，每条带来源标注。

    Args:
        keyword: 检索关键词，例如 "空调"、"用电定额"
    """
    policies = _load_policy_data()
    if not policies:
        return "制度数据集未加载。"

    matched = []
    for p in policies:
        if keyword in p.get("keyword", "") or keyword in p.get("title", "") or keyword in p.get("content", ""):
            matched.append(p)

    if not matched:
        return f"未找到与「{keyword}」相关的制度条目。建议换关键词试试，如：空调、用电定额、节能宣传。"

    lines = [f"检索「{keyword}」命中 {len(matched)} 条制度条目："]
    for p in matched:
        lines.append(f"")
        lines.append(f"【{p['title']}】")
        lines.append(f"内容：{p['content']}")
        lines.append(f"来源：{p['source']}")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")