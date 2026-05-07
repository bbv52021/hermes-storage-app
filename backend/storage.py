# Hermes 收纳助手 - 文件系统操作核心模块
"""
负责所有与群晖文件系统交互的操作：
- 目录创建/读取（房屋/房间/位置/物品 层级）
- 台账读写（物品名称.txt）
- 全局索引维护（物品总索引清单.txt）
- 图片保存（追加，不覆盖）
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import (
    STORAGE_ROOT, INDEX_FILE, LEDGER_FILE_TEMPLATE,
    ALLOWED_IMAGE_EXTENSIONS, FORBIDDEN_CHARS,
    DATETIME_FORMAT, IMAGE_NAME_TEMPLATE
)


def sanitize_name(name: str) -> str:
    """清理文件/文件夹名称，仅移除文件系统禁止的字符"""
    cleaned = name.strip()
    for char in FORBIDDEN_CHARS:
        cleaned = cleaned.replace(char, "")
    # 移除emoji，但保留常见符号（+、#、&、(、)等）
    cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned)
    cleaned = cleaned.strip()
    if not cleaned:
        raise ValueError(f"名称 '{name}' 清理后为空，请提供有效名称")
    if len(cleaned) > 100:
        cleaned = cleaned[:100]
    return cleaned


def get_item_path(house: str, room: str, location: str, item_name: str) -> Path:
    """获取物品的完整目录路径"""
    house = sanitize_name(house)
    room = sanitize_name(room)
    location = sanitize_name(location)
    item_name = sanitize_name(item_name)
    return Path(STORAGE_ROOT) / house / room / location / item_name


def get_ledger_path(item_dir: Path) -> Path:
    """获取物品台账文件路径"""
    item_name = item_dir.name
    return item_dir / LEDGER_FILE_TEMPLATE.format(item_name=item_name)


def get_index_path() -> Path:
    """获取全局索引文件路径"""
    return Path(STORAGE_ROOT) / INDEX_FILE


def ensure_dir(path: Path) -> Path:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_ledger(item_dir: Path) -> Optional[dict]:
    """读取物品台账，返回结构化字典"""
    ledger_path = get_ledger_path(item_dir)
    if not ledger_path.exists():
        return None

    content = ledger_path.read_text(encoding="utf-8")
    ledger = {}
    current_key = None
    current_lines = []

    for line in content.split("\n"):
        if line.startswith("【") and line.endswith("】"):
            if current_key:
                ledger[current_key] = "\n".join(current_lines).strip()
            current_key = line[1:-1]
            current_lines = []
        else:
            current_lines.append(line)

    if current_key:
        ledger[current_key] = "\n".join(current_lines).strip()

    return ledger if ledger else None


def write_ledger(item_dir: Path, data: dict):
    """写入物品台账"""
    ledger_path = get_ledger_path(item_dir)
    ensure_dir(item_dir)

    lines = []
    field_order = [
        "物品名称", "所属房屋", "所属房间", "具体存放位置",
        "首次入库时间", "最后更新时间", "物品描述/备注",
        "配套图片数量", "历次变更记录"
    ]

    for field in field_order:
        if field in data and data[field]:
            lines.append(f"【{field}】")
            lines.append(str(data[field]))
            lines.append("")

    # 写入额外字段
    for key, value in data.items():
        if key not in field_order and value:
            lines.append(f"【{key}】")
            lines.append(str(value))
            lines.append("")

    ledger_path.write_text("\n".join(lines), encoding="utf-8")


def update_ledger(item_dir: Path, updates: dict) -> dict:
    """更新物品台账（增量更新）"""
    existing = read_ledger(item_dir) or {}
    now = datetime.now().strftime(DATETIME_FORMAT)

    # 合并更新
    for key, value in updates.items():
        if key == "历次变更记录" and "历次变更记录" in existing and existing["历次变更记录"]:
            updates[key] = existing["历次变更记录"] + "\n" + value
        existing[key] = value

    existing["最后更新时间"] = now
    write_ledger(item_dir, existing)
    return existing


def read_global_index() -> list[dict]:
    """读取全局物品索引（仅基本索引部分），返回物品列表"""
    index_path = get_index_path()
    if not index_path.exists():
        return []

    content = index_path.read_text(encoding="utf-8")
    items = []
    in_log = False
    for line in content.strip().split("\n"):
        if not line.strip():
            continue
        # 遇到日志分隔线后停止解析基本索引
        if line.strip() == "========== 操作日志 ==========":
            in_log = True
            continue
        if in_log:
            continue
        parts = line.split("｜")
        if len(parts) >= 6:
            items.append({
                "物品名称": parts[0].strip(),
                "所属房屋": parts[1].strip(),
                "所属房间": parts[2].strip(),
                "具体存放位置": parts[3].strip(),
                "首次入库时间": parts[4].strip(),
                "最后更新时间": parts[5].strip(),
            })
    return items


def read_index_log() -> list[str]:
    """读取索引文件中的操作日志部分"""
    index_path = get_index_path()
    if not index_path.exists():
        return []
    content = index_path.read_text(encoding="utf-8")
    logs = []
    in_log = False
    for line in content.split("\n"):
        if line.strip() == "========== 操作日志 ==========":
            in_log = True
            continue
        if in_log and line.strip():
            logs.append(line.strip())
    return logs


def write_global_index(items: list[dict], preserve_log: bool = True):
    """写入全局物品索引（保留操作日志）"""
    index_path = get_index_path()
    ensure_dir(index_path.parent)

    lines = []
    for item in items:
        line = "｜".join([
            item.get("物品名称", ""),
            item.get("所属房屋", ""),
            item.get("所属房间", ""),
            item.get("具体存放位置", ""),
            item.get("首次入库时间", ""),
            item.get("最后更新时间", ""),
        ])
        lines.append(line)

    # 保留已有的操作日志
    if preserve_log:
        existing_logs = read_index_log()
        if existing_logs:
            lines.append("")
            lines.append("========== 操作日志 ==========")
            lines.extend(existing_logs)

    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_index_log(log_text: str):
    """追加一条操作日志到索引文件（直接追加，不读取重写）"""
    index_path = get_index_path()
    ensure_dir(index_path.parent)

    # 检查是否需要添加日志分隔线
    need_separator = False
    if not index_path.exists():
        need_separator = True
    else:
        content = index_path.read_text(encoding="utf-8")
        if "========== 操作日志 ==========" not in content:
            need_separator = True

    # 以追加模式打开文件
    with open(index_path, "a", encoding="utf-8") as f:
        if need_separator:
            f.write("\n========== 操作日志 ==========\n")
        f.write(log_text + "\n")


def update_index_entry(item_name: str, house: str, room: str, location: str,
                       first_time: Optional[str] = None):
    """更新或新增全局索引中的单条记录"""
    items = read_global_index()
    now = datetime.now().strftime(DATETIME_FORMAT)
    full_location = f"{house}/{room}/{location}"

    # 查找是否已存在
    found = False
    for item in items:
        if item["物品名称"] == item_name and item["所属房屋"] == house and item["所属房间"] == room:
            item["具体存放位置"] = location
            item["最后更新时间"] = now
            found = True
            break

    if not found:
        items.append({
            "物品名称": item_name,
            "所属房屋": house,
            "所属房间": room,
            "具体存放位置": location,
            "首次入库时间": first_time or now,
            "最后更新时间": now,
        })

    write_global_index(items)


def remove_index_entry(item_name: str, house: str, room: str):
    """从全局索引中移除一条记录"""
    items = read_global_index()
    items = [i for i in items if not (
        i["物品名称"] == item_name and i["所属房屋"] == house and i["所属房间"] == room
    )]
    write_global_index(items)


def save_image(item_dir: Path, image_data: bytes, original_filename: str) -> str:
    """
    保存图片到物品目录，追加不覆盖
    返回保存后的文件名
    """
    ensure_dir(item_dir)
    item_name = item_dir.name
    now = datetime.now().strftime(DATETIME_FORMAT)

    # 确定扩展名
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        ext = ".jpg"

    # 查找当前最大序号
    existing_images = list(item_dir.glob(f"{item_name}_{now}_*{ext}"))
    seq = len(existing_images) + 1

    filename = IMAGE_NAME_TEMPLATE.format(
        item_name=item_name, datetime=now, seq=seq, ext=ext.lstrip(".")
    )
    filepath = item_dir / filename
    filepath.write_bytes(image_data)

    return filename


def get_item_images(item_dir: Path) -> list[str]:
    """获取物品目录下所有图片文件名"""
    if not item_dir.exists():
        return []
    images = []
    for ext in ALLOWED_IMAGE_EXTENSIONS:
        images.extend(f.name for f in item_dir.glob(f"*{ext}"))
    return sorted(images)


def get_directory_tree(root: Path = None, max_depth: int = 4) -> dict:
    """
    获取存储目录的树形结构
    返回: {"houses": [{"name": "xx", "rooms": [{"name": "xx", "locations": [{"name": "xx", "items": [...]}]}]}]}
    """
    root = root or Path(STORAGE_ROOT)
    if not root.exists():
        return {"houses": []}

    # 系统目录黑名单
    SYSTEM_DIRS = {"@eaDir", "#recycle", "@SynoResource", "@SynoEAStream"}
    
    houses = []
    for house_dir in sorted(root.iterdir()):
        if not house_dir.is_dir() or house_dir.name.startswith(".") or house_dir.name in SYSTEM_DIRS:
            continue
        house = {"name": house_dir.name, "rooms": []}
        for room_dir in sorted(house_dir.iterdir()):
            if not room_dir.is_dir() or room_dir.name.startswith(".") or room_dir.name in SYSTEM_DIRS:
                continue
            room = {"name": room_dir.name, "locations": []}
            for loc_dir in sorted(room_dir.iterdir()):
                if not loc_dir.is_dir() or loc_dir.name.startswith(".") or loc_dir.name in SYSTEM_DIRS:
                    continue
                location = {"name": loc_dir.name, "items": []}
                for item_dir in sorted(loc_dir.iterdir()):
                    if not item_dir.is_dir() or item_dir.name.startswith("."):
                        continue
                    ledger = read_ledger(item_dir)
                    images = get_item_images(item_dir)
                    location["items"].append({
                        "name": item_dir.name,
                        "description": ledger.get("物品描述/备注", "") if ledger else "",
                        "image_count": len(images),
                        "images": images,
                        "last_updated": ledger.get("最后更新时间", "") if ledger else "",
                    })
                room["locations"].append(location)
            house["rooms"].append(room)
        houses.append(house)

    return {"houses": houses}


def search_items(keyword: str) -> list[dict]:
    """
    搜索物品（在索引和台账中搜索）
    """
    results = []
    keyword_lower = keyword.lower()

    # 搜索全局索引
    items = read_global_index()
    for item in items:
        if (keyword_lower in item["物品名称"].lower() or
            keyword_lower in item["所属房屋"].lower() or
            keyword_lower in item["所属房间"].lower() or
            keyword_lower in item["具体存放位置"].lower()):
            results.append(item)

    # 搜索台账中的描述
    root = Path(STORAGE_ROOT)
    if root.exists():
        for house_dir in root.iterdir():
            if not house_dir.is_dir():
                continue
            for room_dir in house_dir.iterdir():
                if not room_dir.is_dir():
                    continue
                for loc_dir in room_dir.iterdir():
                    if not loc_dir.is_dir():
                        continue
                    for item_dir in loc_dir.iterdir():
                        if not item_dir.is_dir():
                            continue
                        ledger = read_ledger(item_dir)
                        if ledger and "物品描述/备注" in ledger:
                            if keyword_lower in ledger["物品描述/备注"].lower():
                                # 避免重复
                                if not any(
                                    r["物品名称"] == item_dir.name and
                                    r["所属房屋"] == house_dir.name and
                                    r["所属房间"] == room_dir.name
                                    for r in results
                                ):
                                    results.append({
                                        "物品名称": item_dir.name,
                                        "所属房屋": house_dir.name,
                                        "所属房间": room_dir.name,
                                        "具体存放位置": loc_dir.name,
                                        "首次入库时间": ledger.get("首次入库时间", ""),
                                        "最后更新时间": ledger.get("最后更新时间", ""),
                                    })

    return results


# ========== 目录层级操作（房屋/房间/位置）==========

def get_house_path(house: str) -> Path:
    """获取房屋目录路径"""
    house = sanitize_name(house)
    return Path(STORAGE_ROOT) / house


def get_room_path(house: str, room: str) -> Path:
    """获取房间目录路径"""
    house = sanitize_name(house)
    room = sanitize_name(room)
    return Path(STORAGE_ROOT) / house / room


def get_location_path(house: str, room: str, location: str) -> Path:
    """获取位置目录路径"""
    house = sanitize_name(house)
    room = sanitize_name(room)
    location = sanitize_name(location)
    return Path(STORAGE_ROOT) / house / room / location


def check_duplicate_name(parent_path: Path, new_name: str) -> bool:
    """检查同级是否有同名目录"""
    if not parent_path.exists():
        return False
    new_path = parent_path / sanitize_name(new_name)
    return new_path.exists()


def rename_house(old_name: str, new_name: str):
    """重命名房屋"""
    old_path = get_house_path(old_name)
    new_path = get_house_path(new_name)
    if not old_path.exists():
        raise ValueError(f"房屋 '{old_name}' 不存在")
    if new_path.exists():
        raise ValueError(f"房屋 '{new_name}' 已存在")
    shutil.move(str(old_path), str(new_path))
    return new_path


def rename_room(house: str, old_room: str, new_room: str):
    """重命名房间"""
    old_path = get_room_path(house, old_room)
    new_path = get_room_path(house, new_room)
    if not old_path.exists():
        raise ValueError(f"房间 '{old_room}' 不存在")
    if new_path.exists():
        raise ValueError(f"房间 '{new_room}' 已存在")
    shutil.move(str(old_path), str(new_path))
    return new_path


def rename_location(house: str, room: str, old_location: str, new_location: str):
    """重命名位置"""
    old_path = get_location_path(house, room, old_location)
    new_path = get_location_path(house, room, new_location)
    if not old_path.exists():
        raise ValueError(f"位置 '{old_location}' 不存在")
    if new_path.exists():
        raise ValueError(f"位置 '{new_location}' 已存在")
    shutil.move(str(old_path), str(new_path))
    return new_path


def delete_house(house: str):
    """删除房屋（及其下所有内容）"""
    house_path = get_house_path(house)
    if not house_path.exists():
        raise ValueError(f"房屋 '{house}' 不存在")
    shutil.rmtree(str(house_path))


def delete_room(house: str, room: str):
    """删除房间（及其下所有内容）"""
    room_path = get_room_path(house, room)
    if not room_path.exists():
        raise ValueError(f"房间 '{room}' 不存在")
    shutil.rmtree(str(room_path))


def delete_location(house: str, room: str, location: str):
    """删除位置（及其下所有内容）"""
    loc_path = get_location_path(house, room, location)
    if not loc_path.exists():
        raise ValueError(f"位置 '{location}' 不存在")
    shutil.rmtree(str(loc_path))


# ========== 目录图片管理 ===========

def save_folder_image(folder_path: Path, image_data: bytes, original_filename: str) -> str:
    """
    保存图片到目录（房屋/房间/位置），图片名固定为目录名
    返回保存后的文件名
    """
    ensure_dir(folder_path)
    folder_name = folder_path.name
    
    # 确定扩展名
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        ext = ".jpg"
    
    # 固定命名：目录名.jpg
    filename = f"{folder_name}{ext}"
    filepath = folder_path / filename
    filepath.write_bytes(image_data)
    
    return filename


def get_folder_image(folder_path: Path) -> Optional[str]:
    """
    获取目录的图片文件名（固定为目录名.*）
    返回文件名或None
    """
    if not folder_path.exists():
        return None
    folder_name = folder_path.name
    for ext in ALLOWED_IMAGE_EXTENSIONS:
        img_path = folder_path / f"{folder_name}{ext}"
        if img_path.exists():
            return img_path.name
    return None


def delete_folder_image(folder_path: Path) -> bool:
    """删除目录的图片"""
    if not folder_path.exists():
        return False
    folder_name = folder_path.name
    deleted = False
    for ext in ALLOWED_IMAGE_EXTENSIONS:
        img_path = folder_path / f"{folder_name}{ext}"
        if img_path.exists():
            img_path.unlink()
            deleted = True
    return deleted
