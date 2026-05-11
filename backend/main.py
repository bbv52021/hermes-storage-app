# Hermes 收纳助手 - FastAPI 后端主程序
"""
提供RESTful API接口：
- 目录浏览：获取房屋/房间/位置/物品的树形结构
- 物品管理：新增、查看、更新、迁移、删除物品
- 图片管理：上传、查看物品图片
- 搜索功能：关键词搜索物品
- 索引管理：读取/刷新全局索引
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from config import STORAGE_ROOT, DATETIME_FORMAT
import storage

app = FastAPI(title="Hermes 收纳助手", version="1.0.0")

# CORS配置 - 允许所有来源（家庭内网使用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保存储根目录存在
os.makedirs(STORAGE_ROOT, exist_ok=True)

# 挂载静态文件（前端页面）
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ========== 数据模型 ==========

class ItemCreate(BaseModel):
    """新增物品请求"""
    house: str
    room: str
    location: str
    item_name: str
    description: str = ""


class ItemUpdate(BaseModel):
    """更新物品请求"""
    description: Optional[str] = None
    new_house: Optional[str] = None
    new_room: Optional[str] = None
    new_location: Optional[str] = None


class ItemMigrate(BaseModel):
    """物品迁移请求"""
    new_house: str
    new_room: str
    new_location: str


# ========== API 路由 ==========

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "storage_root": STORAGE_ROOT}


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """提供前端页面"""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Hermes 收纳助手</h1><p>前端文件未找到，请确认 static 目录中有 index.html</p>")


@app.get("/api/tree")
async def get_directory_tree():
    """获取完整的目录树形结构"""
    try:
        tree = storage.get_directory_tree()
        return {"success": True, "data": tree}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/index")
async def get_global_index():
    """获取全局物品索引"""
    try:
        items = storage.read_global_index()
        return {"success": True, "data": items, "total": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/index/refresh")
async def refresh_index():
    """刷新全局索引（扫描所有台账文件重建索引）"""
    try:
        root = Path(STORAGE_ROOT)
        items = []
        if root.exists():
            for house_dir in root.iterdir():
                if not house_dir.is_dir() or house_dir.name.startswith("."):
                    continue
                for room_dir in house_dir.iterdir():
                    if not room_dir.is_dir() or room_dir.name.startswith("."):
                        continue
                    for loc_dir in room_dir.iterdir():
                        if not loc_dir.is_dir() or loc_dir.name.startswith("."):
                            continue
                        for item_dir in loc_dir.iterdir():
                            if not item_dir.is_dir() or item_dir.name.startswith("."):
                                continue
                            ledger = storage.read_ledger(item_dir)
                            if ledger:
                                items.append({
                                    "物品名称": ledger.get("物品名称", item_dir.name),
                                    "所属房屋": ledger.get("所属房屋", house_dir.name),
                                    "所属房间": ledger.get("所属房间", room_dir.name),
                                    "具体存放位置": ledger.get("具体存放位置", loc_dir.name),
                                    "首次入库时间": ledger.get("首次入库时间", ""),
                                    "最后更新时间": ledger.get("最后更新时间", ""),
                                })
        storage.write_global_index(items)
        return {"success": True, "message": f"索引已刷新，共 {len(items)} 条记录"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/items")
async def create_item(data: ItemCreate):
    """新增物品入库"""
    try:
        now = datetime.now().strftime(DATETIME_FORMAT)
        item_path = storage.get_item_path(data.house, data.room, data.location, data.item_name)

        if item_path.exists():
            raise HTTPException(status_code=409, detail=f"物品 '{data.item_name}' 已存在于该位置")

        # 创建目录和台账
        storage.ensure_dir(item_path)
        ledger_data = {
            "物品名称": data.item_name,
            "所属房屋": data.house,
            "所属房间": data.room,
            "具体存放位置": data.location,
            "首次入库时间": now,
            "最后更新时间": now,
            "物品描述/备注": data.description,
            "配套图片数量": "0",
            "历次变更记录": f"{now} 物品入库",
        }
        storage.write_ledger(item_path, ledger_data)

        # 更新全局索引
        storage.update_index_entry(data.item_name, data.house, data.room, data.location, now)

        # 追加操作日志到索引文件
        desc_text = f"，描述: {data.description}" if data.description else ""
        storage.append_index_log(
            f"[{now}] [新增入库] 物品名称: {data.item_name} ｜ "
            f"位置: {data.house}/{data.room}/{data.location}{desc_text}"
        )

        return {
            "success": True,
            "message": f"物品 '{data.item_name}' 已成功入库",
            "path": str(item_path.relative_to(STORAGE_ROOT)),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/items/{house}/{room}/{location}/{item_name}")
async def get_item(house: str, room: str, location: str, item_name: str):
    """获取物品详情（台账 + 图片列表）"""
    try:
        item_path = storage.get_item_path(house, room, location, item_name)
        if not item_path.exists():
            raise HTTPException(status_code=404, detail="物品不存在")

        ledger = storage.read_ledger(item_path)
        images = storage.get_item_images(item_path)

        return {
            "success": True,
            "data": {
                "ledger": ledger,
                "images": images,
                "image_count": len(images),
                "path": str(item_path.relative_to(STORAGE_ROOT)),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/items/{house}/{room}/{location}/{item_name}/images/{image_name}")
async def get_item_image(house: str, room: str, location: str, item_name: str, image_name: str):
    """获取物品图片"""
    try:
        item_path = storage.get_item_path(house, room, location, item_name)
        image_path = item_path / image_name
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="图片不存在")
        return FileResponse(str(image_path))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/items/{house}/{room}/{location}/{item_name}/images")
async def upload_item_images(
    house: str, room: str, location: str, item_name: str,
    files: list[UploadFile] = File(...)
):
    """上传物品图片（追加，不覆盖）"""
    try:
        item_path = storage.get_item_path(house, room, location, item_name)
        if not item_path.exists():
            raise HTTPException(status_code=404, detail="物品不存在，请先入库")

        saved_files = []
        for file in files:
            image_data = await file.read()
            filename = storage.save_image(item_path, image_data, file.filename or "image.jpg")
            saved_files.append(filename)

        # 更新台账中的图片数量
        images = storage.get_item_images(item_path)
        now = datetime.now().strftime(DATETIME_FORMAT)
        storage.update_ledger(item_path, {
            "配套图片数量": str(len(images)),
            "历次变更记录": f"{now} 新增 {len(saved_files)} 张图片: {', '.join(saved_files)}",
        })

        # 更新全局索引
        storage.update_index_entry(item_name, house, room, location)

        return {
            "success": True,
            "message": f"成功上传 {len(saved_files)} 张图片",
            "files": saved_files,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/items/{house}/{room}/{location}/{item_name}/images/{image_name}")
async def delete_item_image(house: str, room: str, location: str, item_name: str, image_name: str):
    """删除物品单张图片"""
    try:
        item_path = storage.get_item_path(house, room, location, item_name)
        image_path = item_path / image_name
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="图片不存在")

        image_path.unlink()

        # 追加日志
        now = datetime.now().strftime(DATETIME_FORMAT)
        storage.append_index_log(f"[{now}] [删除物品图片] '{house}/{room}/{location}/{item_name}' - {image_name}")

        return {"success": True, "message": f"图片 {image_name} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/items/{house}/{room}/{location}/{item_name}")
async def update_item(house: str, room: str, location: str, item_name: str, data: ItemUpdate):
    """更新物品信息"""
    try:
        item_path = storage.get_item_path(house, room, location, item_name)
        if not item_path.exists():
            raise HTTPException(status_code=404, detail="物品不存在")

        now = datetime.now().strftime(DATETIME_FORMAT)
        updates = {}
        change_desc = []

        if data.description is not None:
            updates["物品描述/备注"] = data.description
            change_desc.append("更新物品描述")

        if any([data.new_house, data.new_room, data.new_location]):
            # 这是迁移操作
            new_house = data.new_house or house
            new_room = data.new_room or room
            new_location = data.new_location or location

            new_path = storage.get_item_path(new_house, new_room, new_location, item_name)
            old_relative = f"{house}/{room}/{location}"
            new_relative = f"{new_house}/{new_room}/{new_location}"

            if old_relative != new_relative:
                # 执行迁移
                storage.ensure_dir(new_path.parent)
                shutil.move(str(item_path), str(new_path))

                # 在新位置更新台账
                updates["所属房屋"] = new_house
                updates["所属房间"] = new_room
                updates["具体存放位置"] = new_location
                updates["历次变更记录"] = f"{now} 物品迁移: {old_relative} → {new_relative}"

                storage.update_ledger(new_path, updates)

                # 更新全局索引
                storage.remove_index_entry(item_name, house, room)
                storage.update_index_entry(item_name, new_house, new_room, new_location)

                return {
                    "success": True,
                    "message": f"物品已从 {old_relative} 迁移至 {new_relative}",
                    "new_path": str(new_path.relative_to(STORAGE_ROOT)),
                }

        if change_desc:
            updates["历次变更记录"] = f"{now} {', '.join(change_desc)}"
            storage.update_ledger(item_path, updates)
            storage.update_index_entry(item_name, house, room, location)

        return {
            "success": True,
            "message": f"物品 '{item_name}' 已更新",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/items/{house}/{room}/{location}/{item_name}/checkout")
async def checkout_item(house: str, room: str, location: str, item_name: str, note: str = ""):
    """物品取出记录"""
    try:
        item_path = storage.get_item_path(house, room, location, item_name)
        if not item_path.exists():
            raise HTTPException(status_code=404, detail="物品不存在")

        now = datetime.now().strftime(DATETIME_FORMAT)
        note_text = f"，备注: {note}" if note else ""
        storage.update_ledger(item_path, {
            "历次变更记录": f"{now} 物品取出{note_text}",
        })
        storage.update_index_entry(item_name, house, room, location)

        # 追加操作日志到索引文件
        storage.append_index_log(
            f"[{now}] [取出] 物品名称: {item_name} ｜ "
            f"位置: {house}/{room}/{location}{note_text}"
        )

        return {
            "success": True,
            "message": f"物品 '{item_name}' 取出记录已保存",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/items/{house}/{room}/{location}/{item_name}/destroy")
async def destroy_item(house: str, room: str, location: str, item_name: str, note: str = ""):
    """物品销毁记录（标记为已销毁，不删除文件）"""
    try:
        item_path = storage.get_item_path(house, room, location, item_name)
        if not item_path.exists():
            raise HTTPException(status_code=404, detail="物品不存在")

        now = datetime.now().strftime(DATETIME_FORMAT)
        note_text = f"，备注: {note}" if note else ""
        storage.update_ledger(item_path, {
            "历次变更记录": f"{now} 物品已销毁{note_text}",
        })
        # 更新索引中的状态
        storage.update_index_entry(item_name, house, room, location)

        # 追加操作日志到索引文件
        storage.append_index_log(
            f"[{now}] [销毁] 物品名称: {item_name} ｜ "
            f"位置: {house}/{room}/{location}{note_text}"
        )

        return {
            "success": True,
            "message": f"物品 '{item_name}' 已标记为销毁",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/items/{house}/{room}/{location}/{item_name}/transfer")
async def transfer_item(house: str, room: str, location: str, item_name: str, data: ItemMigrate, note: str = ""):
    """物品转移位置"""
    try:
        item_path = storage.get_item_path(house, room, location, item_name)
        if not item_path.exists():
            raise HTTPException(status_code=404, detail="物品不存在")

        now = datetime.now().strftime(DATETIME_FORMAT)
        new_path = storage.get_item_path(data.new_house, data.new_room, data.new_location, item_name)

        old_relative = f"{house}/{room}/{location}"
        new_relative = f"{data.new_house}/{data.new_room}/{data.new_location}"

        if old_relative == new_relative:
            raise HTTPException(status_code=400, detail="新位置与当前位置相同")

        # 在原台账记录转移
        note_text = f"，备注: {note}" if note else ""
        storage.update_ledger(item_path, {
            "历次变更记录": f"{now} 物品已转移至: {new_relative}{note_text}",
        })

        # 执行物理迁移
        storage.ensure_dir(new_path.parent)
        shutil.move(str(item_path), str(new_path))

        # 更新新位置的台账
        storage.update_ledger(new_path, {
            "所属房屋": data.new_house,
            "所属房间": data.new_room,
            "具体存放位置": data.new_location,
        })

        # 更新全局索引：删除旧记录，添加新记录
        storage.remove_index_entry(item_name, house, room)
        storage.update_index_entry(item_name, data.new_house, data.new_room, data.new_location)

        # 追加操作日志到索引文件
        storage.append_index_log(
            f"[{now}] [转移] 物品名称: {item_name} ｜ "
            f"原位置: {old_relative} → 新位置: {new_relative}{note_text}"
        )

        return {
            "success": True,
            "message": f"物品 '{item_name}' 已从 {old_relative} 转移至 {new_relative}",
            "new_path": str(new_path.relative_to(STORAGE_ROOT)),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/items/{house}/{room}/{location}/{item_name}")
async def delete_item(house: str, room: str, location: str, item_name: str):
    """删除物品（整个目录）"""
    try:
        item_path = storage.get_item_path(house, room, location, item_name)
        if not item_path.exists():
            raise HTTPException(status_code=404, detail="物品不存在")

        shutil.rmtree(str(item_path))
        storage.remove_index_entry(item_name, house, room)

        # 追加操作日志到索引文件
        now = datetime.now().strftime(DATETIME_FORMAT)
        storage.append_index_log(
            f"[{now}] [删除] 物品名称: {item_name} ｜ "
            f"位置: {house}/{room}/{location} ｜ 警告: 该物品所有文件已被彻底删除"
        )

        return {
            "success": True,
            "message": f"物品 '{item_name}' 已删除",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 目录层级操作 API（房屋/房间/位置）==========

class RenameRequest(BaseModel):
    new_name: str


@app.get("/api/houses/{house}/check")
async def check_house_duplicate(house: str, new_name: str):
    """检查房屋新名称是否重复"""
    try:
        house_path = storage.get_house_path(house)
        is_dup = storage.check_duplicate_name(house_path.parent, new_name)
        return {"success": True, "duplicate": is_dup}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/houses/{house}")
async def rename_house_api(house: str, data: RenameRequest):
    """重命名房屋"""
    try:
        # 检查是否同名
        if storage.check_duplicate_name(Path(storage.STORAGE_ROOT), data.new_name):
            raise HTTPException(status_code=409, detail=f"房屋 '{data.new_name}' 已存在")
        
        storage.rename_house(house, data.new_name)
        
        # 更新索引中所有该房屋下的物品
        items = storage.read_global_index()
        for item in items:
            if item["所属房屋"] == house:
                item["所属房屋"] = data.new_name
        storage.write_global_index(items)
        
        # 追加日志
        now = datetime.now().strftime(DATETIME_FORMAT)
        storage.append_index_log(
            f"[{now}] [重命名房屋] '{house}' → '{data.new_name}'"
        )
        
        return {"success": True, "message": f"房屋 '{house}' 已重命名为 '{data.new_name}'"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/houses/{house}")
async def delete_house_api(house: str):
    """删除房屋（及其下所有内容）"""
    try:
        # 先删除索引中该房屋的所有物品
        items = storage.read_global_index()
        items = [i for i in items if i["所属房屋"] != house]
        storage.write_global_index(items)
        
        # 删除房屋目录
        storage.delete_house(house)
        
        # 追加日志
        now = datetime.now().strftime(DATETIME_FORMAT)
        storage.append_index_log(
            f"[{now}] [删除房屋] '{house}' 及其下所有物品"
        )
        
        return {"success": True, "message": f"房屋 '{house}' 已删除"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/houses/{house}/rooms/{room}/check")
async def check_room_duplicate(house: str, room: str, new_name: str):
    """检查房间新名称是否重复"""
    try:
        house_path = storage.get_house_path(house)
        is_dup = storage.check_duplicate_name(house_path, new_name)
        return {"success": True, "duplicate": is_dup}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/houses/{house}/rooms/{room}")
async def rename_room_api(house: str, room: str, data: RenameRequest):
    """重命名房间"""
    try:
        house_path = storage.get_house_path(house)
        # 检查是否同名
        if storage.check_duplicate_name(house_path, data.new_name):
            raise HTTPException(status_code=409, detail=f"房间 '{data.new_name}' 已存在")
        
        storage.rename_room(house, room, data.new_name)
        
        # 更新索引中所有该房间下的物品
        items = storage.read_global_index()
        for item in items:
            if item["所属房屋"] == house and item["所属房间"] == room:
                item["所属房间"] = data.new_name
        storage.write_global_index(items)
        
        # 追加日志
        now = datetime.now().strftime(DATETIME_FORMAT)
        storage.append_index_log(
            f"[{now}] [重命名房间] '{house}/{room}' → '{house}/{data.new_name}'"
        )
        
        return {"success": True, "message": f"房间 '{room}' 已重命名为 '{data.new_name}'"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/houses/{house}/rooms/{room}")
async def delete_room_api(house: str, room: str):
    """删除房间（及其下所有内容）"""
    try:
        # 先删除索引中该房间的所有物品
        items = storage.read_global_index()
        items = [i for i in items if not (i["所属房屋"] == house and i["所属房间"] == room)]
        storage.write_global_index(items)
        
        # 删除房间目录
        storage.delete_room(house, room)
        
        # 追加日志
        now = datetime.now().strftime(DATETIME_FORMAT)
        storage.append_index_log(
            f"[{now}] [删除房间] '{house}/{room}' 及其下所有物品"
        )
        
        return {"success": True, "message": f"房间 '{room}' 已删除"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/houses/{house}/rooms/{room}/locations/{location}/check")
async def check_location_duplicate(house: str, room: str, location: str, new_name: str):
    """检查位置新名称是否重复"""
    try:
        room_path = storage.get_room_path(house, room)
        is_dup = storage.check_duplicate_name(room_path, new_name)
        return {"success": True, "duplicate": is_dup}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/houses/{house}/rooms/{room}/locations/{location}")
async def rename_location_api(house: str, room: str, location: str, data: RenameRequest):
    """重命名位置"""
    try:
        room_path = storage.get_room_path(house, room)
        # 检查是否同名
        if storage.check_duplicate_name(room_path, data.new_name):
            raise HTTPException(status_code=409, detail=f"位置 '{data.new_name}' 已存在")
        
        storage.rename_location(house, room, location, data.new_name)
        
        # 更新索引中所有该位置下的物品
        items = storage.read_global_index()
        for item in items:
            if item["所属房屋"] == house and item["所属房间"] == room and item["具体存放位置"] == location:
                item["具体存放位置"] = data.new_name
        storage.write_global_index(items)
        
        # 追加日志
        now = datetime.now().strftime(DATETIME_FORMAT)
        storage.append_index_log(
            f"[{now}] [重命名位置] '{house}/{room}/{location}' → '{house}/{room}/{data.new_name}'"
        )
        
        return {"success": True, "message": f"位置 '{location}' 已重命名为 '{data.new_name}'"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/houses/{house}/rooms/{room}/locations/{location}")
async def delete_location_api(house: str, room: str, location: str):
    """删除位置（及其下所有内容）"""
    try:
        # 先删除索引中该位置的所有物品
        items = storage.read_global_index()
        items = [i for i in items if not (
            i["所属房屋"] == house and i["所属房间"] == room and i["具体存放位置"] == location
        )]
        storage.write_global_index(items)
        
        # 删除位置目录
        storage.delete_location(house, room, location)
        
        # 追加日志
        now = datetime.now().strftime(DATETIME_FORMAT)
        storage.append_index_log(
            f"[{now}] [删除位置] '{house}/{room}/{location}' 及其下所有物品"
        )
        
        return {"success": True, "message": f"位置 '{location}' 已删除"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 目录图片管理 API ==========

@app.get("/api/houses/{house}/image")
async def get_house_image(house: str):
    """获取房屋图片"""
    try:
        house_path = storage.get_house_path(house)
        img_name = storage.get_folder_image(house_path)
        if not img_name:
            raise HTTPException(status_code=404, detail="房屋没有图片")
        return FileResponse(str(house_path / img_name))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/houses/{house}/image")
async def upload_house_image(house: str, file: UploadFile = File(...)):
    """上传房屋图片（覆盖）"""
    try:
        house_path = storage.get_house_path(house)
        if not house_path.exists():
            raise HTTPException(status_code=404, detail="房屋不存在")
        
        image_data = await file.read()
        filename = storage.save_folder_image(house_path, image_data, file.filename or "image.jpg")
        
        # 追加日志
        now = datetime.now().strftime(DATETIME_FORMAT)
        storage.append_index_log(f"[{now}] [上传房屋图片] '{house}'")
        
        return {"success": True, "message": "图片已上传", "filename": filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/houses/{house}/image")
async def delete_house_image(house: str):
    """删除房屋图片"""
    try:
        house_path = storage.get_house_path(house)
        deleted = storage.delete_folder_image(house_path)
        if not deleted:
            raise HTTPException(status_code=404, detail="房屋没有图片")
        
        # 追加日志
        now = datetime.now().strftime(DATETIME_FORMAT)
        storage.append_index_log(f"[{now}] [删除房屋图片] '{house}'")
        
        return {"success": True, "message": "图片已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/houses/{house}/rooms/{room}/image")
async def get_room_image(house: str, room: str):
    """获取房间图片"""
    try:
        room_path = storage.get_room_path(house, room)
        img_name = storage.get_folder_image(room_path)
        if not img_name:
            raise HTTPException(status_code=404, detail="房间没有图片")
        return FileResponse(str(room_path / img_name))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/houses/{house}/rooms/{room}/image")
async def upload_room_image(house: str, room: str, file: UploadFile = File(...)):
    """上传房间图片（覆盖）"""
    try:
        room_path = storage.get_room_path(house, room)
        if not room_path.exists():
            raise HTTPException(status_code=404, detail="房间不存在")
        
        image_data = await file.read()
        filename = storage.save_folder_image(room_path, image_data, file.filename or "image.jpg")
        
        # 追加日志
        now = datetime.now().strftime(DATETIME_FORMAT)
        storage.append_index_log(f"[{now}] [上传房间图片] '{house}/{room}'")
        
        return {"success": True, "message": "图片已上传", "filename": filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/houses/{house}/rooms/{room}/image")
async def delete_room_image(house: str, room: str):
    """删除房间图片"""
    try:
        room_path = storage.get_room_path(house, room)
        deleted = storage.delete_folder_image(room_path)
        if not deleted:
            raise HTTPException(status_code=404, detail="房间没有图片")
        
        # 追加日志
        now = datetime.now().strftime(DATETIME_FORMAT)
        storage.append_index_log(f"[{now}] [删除房间图片] '{house}/{room}'")
        
        return {"success": True, "message": "图片已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/houses/{house}/rooms/{room}/locations/{location}/image")
async def get_location_image(house: str, room: str, location: str):
    """获取位置图片"""
    try:
        loc_path = storage.get_location_path(house, room, location)
        img_name = storage.get_folder_image(loc_path)
        if not img_name:
            raise HTTPException(status_code=404, detail="位置没有图片")
        return FileResponse(str(loc_path / img_name))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/houses/{house}/rooms/{room}/locations/{location}/image")
async def upload_location_image(house: str, room: str, location: str, file: UploadFile = File(...)):
    """上传位置图片（覆盖）"""
    try:
        loc_path = storage.get_location_path(house, room, location)
        if not loc_path.exists():
            raise HTTPException(status_code=404, detail="位置不存在")
        
        image_data = await file.read()
        filename = storage.save_folder_image(loc_path, image_data, file.filename or "image.jpg")
        
        # 追加日志
        now = datetime.now().strftime(DATETIME_FORMAT)
        storage.append_index_log(f"[{now}] [上传位置图片] '{house}/{room}/{location}'")
        
        return {"success": True, "message": "图片已上传", "filename": filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/houses/{house}/rooms/{room}/locations/{location}/image")
async def delete_location_image(house: str, room: str, location: str):
    """删除位置图片"""
    try:
        loc_path = storage.get_location_path(house, room, location)
        deleted = storage.delete_folder_image(loc_path)
        if not deleted:
            raise HTTPException(status_code=404, detail="位置没有图片")
        
        # 追加日志
        now = datetime.now().strftime(DATETIME_FORMAT)
        storage.append_index_log(f"[{now}] [删除位置图片] '{house}/{room}/{location}'")
        
        return {"success": True, "message": "图片已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def search_items(keyword: str = Query(..., min_length=1)):
    """搜索物品（含图片信息）"""
    try:
        results = storage.search_items(keyword)
        # 为每个结果附加图片列表
        for item in results:
            item_path = storage.get_item_path(
                item["所属房屋"], item["所属房间"],
                item["具体存放位置"], item["物品名称"]
            )
            item["images"] = storage.get_item_images(item_path)
            item["image_count"] = len(item["images"])
            # 读取台账获取描述
            ledger = storage.read_ledger(item_path)
            item["description"] = ledger.get("物品描述/备注", "") if ledger else ""
        return {"success": True, "data": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """获取统计数据"""
    try:
        tree = storage.get_directory_tree()
        total_items = 0
        total_houses = len(tree["houses"])
        total_rooms = 0
        total_locations = 0

        for house in tree["houses"]:
            total_rooms += len(house["rooms"])
            for room in house["rooms"]:
                total_locations += len(room["locations"])
                for loc in room["locations"]:
                    total_items += len(loc["items"])

        index_items = storage.read_global_index()

        return {
            "success": True,
            "data": {
                "total_houses": total_houses,
                "total_rooms": total_rooms,
                "total_locations": total_locations,
                "total_items": total_items,
                "index_count": len(index_items),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 启动 ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
