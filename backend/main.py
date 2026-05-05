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
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
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

        return {
            "success": True,
            "message": f"物品 '{item_name}' 取出记录已保存",
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

        return {
            "success": True,
            "message": f"物品 '{item_name}' 已删除",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def search_items(keyword: str = Query(..., min_length=1)):
    """搜索物品"""
    try:
        results = storage.search_items(keyword)
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
