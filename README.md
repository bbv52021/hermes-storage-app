# Hermes 收纳助手 - 部署指南

## 项目简介
Hermes 收纳助手是一个家庭物品收纳管理Web应用，以群晖共享文件夹作为数据库，支持物品入库、取出、查看、搜索等功能。

## 技术架构
- **后端**: Python FastAPI
- **前端**: 纯HTML/CSS/JS（响应式设计，手机/电脑均可使用）
- **存储**: 群晖文件系统（txt台账 + 图片文件）
- **部署**: Docker / Docker Compose

## 目录结构
```
hermes-storage-app/
├── backend/
│   ├── main.py          # FastAPI 主程序
│   ├── config.py        # 配置文件
│   ├── storage.py       # 文件系统操作核心
│   └── requirements.txt # Python 依赖
├── frontend/
│   └── index.html       # Web前端页面
├── Dockerfile           # Docker 镜像构建
├── docker-compose.yml   # Docker Compose 配置
└── README.md            # 本文件
```

## 群晖 Docker 部署步骤

### 方式一：通过 Docker Compose 部署（推荐）

1. **上传项目到群晖**
   将整个 `hermes-storage-app` 文件夹上传到群晖的某个目录中（如 `/volume1/docker/hermes-storage-app/`）

2. **修改挂载路径**
   编辑 `docker-compose.yml`，确认 volumes 中的宿主机路径正确：
   ```yaml
   volumes:
     - /volume1/群晖共享文件夹01/物品存储:/data/物品存储
   ```
   > 如果您的群晖共享文件夹路径不同，请修改左侧路径

3. **SSH 登录群晖执行部署**
   ```bash
   cd /volume1/docker/hermes-storage-app
   docker-compose up -d --build
   ```

4. **访问应用**
   浏览器打开 `http://群晖IP:8900`

### 方式二：通过群晖 Container Manager (Docker GUI) 部署

1. **构建镜像**
   SSH 登录群晖：
   ```bash
   cd /volume1/docker/hermes-storage-app
   docker build -t hermes-storage-app .
   ```

2. **在 Container Manager 中创建容器**
   - 镜像：选择 `hermes-storage-app`
   - 端口：容器端口 `8000` → 本地端口 `8900`
   - 存储空间挂载：
     - 文件/文件夹：`/volume1/群晖共享文件夹01/物品存储`
     - 装载路径：`/data/物品存储`
   - 环境变量：`TZ=Asia/Shanghai`

3. **启动容器**，访问 `http://群晖IP:8900`

## 配置说明

### 环境变量
| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `STORAGE_ROOT` | `/data/物品存储` | 物品存储根目录 |
| `TZ` | `Asia/Shanghai` | 时区 |

### 端口
- 默认映射：`8900:8000`
- 可在 docker-compose.yml 中修改左侧端口号

## 功能说明

### 物品入库
1. 点击右上角「新增物品」
2. 填写房屋、房间、位置、物品名称
3. 可选填写描述和上传图片
4. 系统自动创建目录结构、生成台账、更新索引

### 物品查看
- 按层级浏览：房屋 → 房间 → 位置 → 物品
- 支持网格视图和列表视图切换
- 点击物品卡片查看详情（含图片、台账、变更记录）

### 物品搜索
- 顶部搜索框支持实时搜索
- 可按物品名称、房屋、房间、位置、描述搜索

### 物品取出
- 在物品详情中点击「记录取出」
- 可填写取出备注

### 刷新索引
- 点击「刷新索引」重建全局索引
- 系统会扫描所有台账文件

## 与 Hermes AI 助手的兼容性

本应用与您现有的 Hermes 收纳助手规则完全兼容：
- 共用同一套文件目录结构（房屋/房间/位置/物品）
- 共用同一套台账格式（物品名称.txt）
- 共用同一个全局索引（物品总索引清单.txt）
- AI 助手和 Web APP 操作的数据互相可见
- 多个 Hermes 实例和 Web APP 可同时使用

## API 接口文档

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查 |
| GET | /api/tree | 获取目录树 |
| GET | /api/index | 获取全局索引 |
| POST | /api/index/refresh | 刷新索引 |
| POST | /api/items | 新增物品 |
| GET | /api/items/{house}/{room}/{loc}/{name} | 获取物品详情 |
| PUT | /api/items/{house}/{room}/{loc}/{name} | 更新物品 |
| DELETE | /api/items/{house}/{room}/{loc}/{name} | 删除物品 |
| POST | /api/items/{...}/images | 上传图片 |
| GET | /api/items/{...}/images/{img} | 获取图片 |
| POST | /api/items/{...}/checkout | 记录取出 |
| GET | /api/search?keyword=xx | 搜索物品 |
| GET | /api/stats | 获取统计 |
