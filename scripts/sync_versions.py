"""刷新门户里被标记包住的子项目版本号与发布日期。

只动两类区间：

    <!-- @v:calendar -->v0.9.0<!-- @/v -->      版本号
    <!-- @d:calendar -->2026-10-16<!-- @/d -->  发布日期

区间外的任何文字一律不碰 —— 通路描述与功能口径是人的事，脚本不代劳。
取值来源（都只在云端可达，本地跑要显式代理）：

- ``calendar``：PyPI ``info.version`` 与 ``urls[0].upload_time``
- ``siyuan``：GitHub ``releases/latest`` 的 ``tag_name`` 与 ``published_at``
  （思源不发 PyPI，实测该包名在 PyPI 返回 404）

判据是 fail-closed：任一来源取不到、版本形如非法、或某个标记的关键字不认识，
两份文件都原样留在磁盘上（不会只改一半）、退出码 1。
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc

ROOT = Path(__file__).resolve().parent.parent
FILES = ("index.html", "README.md")
TIMEOUT = 30

#: 关键字 -> (接口, 取版本的指针, 取日期的指针)
SOURCES = {
    "calendar": {
        "url": "https://pypi.org/pypi/xjtu-timetable-calendar/json",
        "version": ("info", "version"),
        "date": ("urls", "0", "upload_time"),
    },
    "siyuan": {
        "url": "https://api.github.com/repos/XLJFZ/xjtu-siyuanxuetang-grab/releases/latest",
        "version": ("tag_name",),
        "date": ("published_at",),
    },
}

#: 只在同一行内配对。文档里会出现「@v 标记」这类说明文字，
#: 带 re.S 时一个没配对的开始标记会跨过整篇文档去抓后面的闭合标记，把无关段落当成待替换区间。
V_RE = re.compile(r"(<!--\s*@v:(\w+)\s*-->)([^<]*)(<!--\s*@/v\s*-->)")
D_RE = re.compile(r"(<!--\s*@d:(\w+)\s*-->)([^<]*)(<!--\s*@/d\s*-->)")
#: 允许 0.9.0 / v1.6.0 两种写法，不接受空串或任意文字
VERSION_OK = re.compile(r"^v?\d+\.\d+(\.\d+)?$")
DATE_OK = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class SyncError(RuntimeError):
    """任一取数或替换前提不成立 —— 于是不写盘。"""


#: PyPI 与 GitHub 给的时间都是 UTC，而本项目的发布日一律写北京日期。
#: 实测两次都跨了天：0.9.0 上传于 2026-10-15T18:48Z = 北京 10-16 02:48，
#: 0.9.1 上传于 2026-10-22T17:19Z = 北京 10-23 01:19。
#: 不换算的话脚本每天把 CHANGELOG 里那个正确的日期"改"回前一天，跟人对着干。
#: 中国不用夏令时，固定 +08:00 就够，也免得依赖 tzdata。
BEIJING = timezone(timedelta(hours=8))


def _to_beijing_date(raw: str, key: str) -> str:
    """把 ``2026-10-22T17:19:09`` 或带 Z 的同形串换成北京日期。"""
    text = raw.rstrip("Z")
    if len(text) < 19:
        raise SyncError(f"{key}: 时间戳 {raw!r} 太短，取不出日期")
    try:
        moment = datetime.strptime(text[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
    except ValueError as exc:
        raise SyncError(f"{key}: 时间戳 {raw!r} 解析失败（{exc}）") from exc
    return moment.astimezone(BEIJING).strftime("%Y-%m-%d")


def _dig(payload: object, path: tuple[str, ...], key: str) -> str:
    node = payload
    for step in path:
        if isinstance(node, list):
            if not node:
                raise SyncError(f"{key}: 列表在 {step!r} 处为空")
            node = node[int(step)]
        elif isinstance(node, dict):
            if step not in node:
                raise SyncError(f"{key}: 响应里没有 {step!r}")
            node = node[step]
        else:
            raise SyncError(f"{key}: 在 {step!r} 处遇到 {type(node).__name__}")
    if not isinstance(node, str) or not node.strip():
        raise SyncError(f"{key}: 取到的不是非空字符串（{node!r}）")
    return node.strip()


def fetch(key: str) -> tuple[str, str]:
    """返回该子项目的 (v 区间内容, d 区间内容)。"""
    source = SOURCES[key]
    request = urllib.request.Request(
        source["url"],
        # api.github.com 无 User-Agent 直接 403
        headers={"User-Agent": "xjtu-student-tools-portal-sync"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - 任何取数失败都只有一种处置：不改
        raise SyncError(f"{key}: 取数失败（{type(exc).__name__}: {exc}）") from exc

    version = _dig(payload, source["version"], key)
    date = _to_beijing_date(_dig(payload, source["date"], key), key)
    if not VERSION_OK.match(version):
        raise SyncError(f"{key}: 版本号 {version!r} 形状非法")
    if not DATE_OK.match(date):
        raise SyncError(f"{key}: 发布日期 {date!r} 形状非法")
    if not version.startswith("v"):
        version = f"v{version}"  # 门户两处文案都用 v 前缀
    return version, date


def _sub(
    regex: re.Pattern[str],
    text: str,
    values: dict[str, str],
    field: str,
    path: Path,
) -> tuple[str, int]:
    hits = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal hits
        key = match.group(2)
        if key not in values:
            raise SyncError(f"{path.name}: 不认识的关键字 @{field}:{key}")
        new = values[key]
        old = match.group(3)
        if not old.strip():
            raise SyncError(f"{path.name}: @{field}:{key} 的区间是空的，拒绝填")
        hits += 1
        return f"{match.group(1)}{new}{match.group(4)}"

    return regex.sub(replace, text), hits


def sync(dry_run: bool) -> int:
    values_v: dict[str, str] = {}
    values_d: dict[str, str] = {}
    for key in SOURCES:
        version, date = fetch(key)
        values_v[key], values_d[key] = version, date
        print(f"{key}: {version} / {date}")

    pending: list[tuple[Path, str]] = []
    counts: dict[str, int] = {}
    for name in FILES:
        path = ROOT / name
        original = path.read_text(encoding="utf-8")
        text, v_hits = _sub(V_RE, original, values_v, "v", path)
        text, d_hits = _sub(D_RE, text, values_d, "d", path)
        if v_hits + d_hits == 0:
            raise SyncError(f"{name}: 一个标记都没有，脚本与文件的约定已失效")
        counts[name] = v_hits + d_hits
        if text != original:
            pending.append((path, text))

    # 上面全部通过才写盘：任何一份文件出问题，另一份也不会被改一半
    changed = []
    for path, text in pending:
        if not dry_run:
            path.write_text(text, encoding="utf-8")
        changed.append(f"{path.name}（{counts[path.name]} 处）")

    if changed:
        print(("待改写：" if dry_run else "已改写：") + "、".join(changed))
    else:
        print("无变化")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(sync(dry_run="--check" in sys.argv[1:]))
    except SyncError as error:
        print(f"拒绝改动：{error}", file=sys.stderr)
        sys.exit(1)
