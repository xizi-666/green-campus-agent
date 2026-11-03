"""
自定义工具
==========

绿电管家 · 绿色校园节能助手的 4 个自定义工具：
- query_dorm_power      查宿舍近 N 周用电（含合计 / 周均 / 环比）
- waste_sorting_lookup   查垃圾分类（含模糊匹配与换词提示，拒绝瞎猜）
- calculator             AST 安全求值的精确计算
- get_current_time       日期星期，写报告落款用

函数名 = 工具名，docstring = 工具说明，类型注解 = 参数 schema。
模型依靠 docstring 判断何时调用，所以 docstring 要写清楚。
"""

import ast
import json
import operator
from datetime import datetime
from pathlib import Path

# 数据集目录
DATA_DIR = Path(__file__).resolve().parent / "dataset"


def _load_power_data() -> dict:
    """加载用电数据集"""
    path = DATA_DIR / "power_data.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_waste_data() -> dict:
    """加载垃圾分类数据集"""
    path = DATA_DIR / "waste_sorting.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_current_time() -> str:
    """获取当前的本地日期、时间和星期，并标注本学期周数。回答与"今天/现在/几号/星期几/上周/本周"有关的问题时使用，写报告落款时也用。学期从 2026-09-01 开始，每周一起算，用于定位"上周/本周"对应的用电数据周数。"""
    now = datetime.now()
    weekday = "一二三四五六日"[now.weekday()]
    term_start = datetime(2026, 9, 1)
    week_num = (now - term_start).days // 7 + 1
    return now.strftime("%Y-%m-%d %H:%M:%S") + f" 星期{weekday}" + f" ｜ 本学期第 {week_num} 周"


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval(node):
    """只允许数字和算术运算的安全求值，避免直接 eval 带来的代码执行风险。"""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("只支持数字和 + - * / // % ** 运算")


def calculator(expression: str) -> str:
    """精确计算数学表达式，例如 "(3 + 5) * 2 ** 10"。涉及数值计算时务必使用，不要心算。

    Args:
        expression: 只包含数字、括号和 + - * / // % ** 的表达式
    """
    try:
        return str(_eval(ast.parse(expression, mode="eval").body))
    except Exception as exc:  # noqa: BLE001
        return f"计算失败：{exc}"


def query_dorm_power(building: str, room: str, weeks: int = 4) -> str:
    """查询某栋宿舍楼某间宿舍最近 N 周的每周用电量，并自动计算合计、周均和环比变化。

    Args:
        building: 楼栋名称，例如 "玉兰苑1号楼"
        room: 房间号，例如 "302"
        weeks: 查询最近几周的数据，默认 4 周（数据集共 8 周）
    """
    data = _load_power_data()
    rooms_map = data.get("rooms", {})
    power_map = data.get("data", {})

    if building not in rooms_map:
        avail = "、".join(rooms_map.keys())
        return f"未找到楼栋「{building}」，可选：{avail}"

    if room not in rooms_map[building]:
        avail = "、".join(rooms_map[building])
        return f"楼栋「{building}」没有房间「{room}」，可选：{avail}"

    records = power_map.get(building, {}).get(room, [])
    if not records:
        return f"楼栋「{building}」房间「{room}」暂无用电数据。"

    total_weeks = len(records)
    n = min(weeks, total_weeks)
    recent = records[-n:]

    total = sum(recent)
    avg = round(total / n, 1)

    if n >= 2:
        change = round(recent[-1] - recent[-2], 1)
        pct = round(change / recent[-2] * 100, 1) if recent[-2] != 0 else 0
        trend = f"↑{change}度（+{pct}%）" if change > 0 else (f"↓{abs(change)}度（{pct}%）" if change < 0 else "持平")
    else:
        trend = "数据不足，无法计算环比"

    week_labels = [f"第{total_weeks - n + i + 1}周" for i in range(n)]
    lines = [f"楼栋「{building}」房间「{room}」最近 {n} 周用电："]
    for label, val in zip(week_labels, recent):
        lines.append(f"  {label}：{val} 度")
    lines.append(f"合计：{round(total, 1)} 度")
    lines.append(f"周均：{avg} 度")
    lines.append(f"环比：{trend}")
    return "\n".join(lines)


def waste_sorting_lookup(item: str) -> str:
    """查询某种生活垃圾的分类类别和投放提示。查不到时返回相近物品引导换词，绝不编造。

    Args:
        item: 物品名称，例如 "外卖餐盒"、"废旧电池"
    """
    data = _load_waste_data()
    items = data.get("items", {})

    if item in items:
        info = items[item]
        return f"「{item}」→ 分类：{info['category']}\n投放提示：{info['tip']}"

    candidates = []
    for key in items:
        if item in key or key in item:
            candidates.append(key)

    if candidates:
        sugg = "、".join(candidates[:5])
        return f"未精确找到「{item}」，你是不是想查：{sugg}？请换一个词再试。"
    else:
        sample = "、".join(list(items.keys())[:8])
        return f"未找到「{item}」的分类信息，我不确定所以不瞎猜。常见可查物品包括：{sample}等。请换个说法再试。"


CUSTOM_TOOLS = [get_current_time, calculator, query_dorm_power, waste_sorting_lookup]