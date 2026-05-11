# Hermes 物品收纳管理系统 - 项目更新日志

---

## v1.2.5 (2026-05-11 22:58) — 新增修改信息、统计卡片点击、索引记录 ✅

### 新增功能
- **物品详情页添加修改信息入口**: 可修改物品名称、描述、添加新图片
- **首页统计卡片点击进入列表页**:
  - 房屋数 → 所有房屋列表
  - 房间数 → 所有房间列表
  - 位置数 → 所有位置列表
  - 物品数 → 所有物品列表
- **索引记录卡片**: 点击打开物品总索引清单文本记录

### 修改文件
- `lib/screens/items_screen.dart` — 添加修改信息按钮和编辑弹窗
- `lib/screens/home_screen.dart` — 统计卡片可点击，添加索引记录卡片
- `lib/services/api_service.dart` — 添加 updateItem 和 getGlobalIndex API
- `lib/providers/app_provider.dart` — 添加 updateItem 方法
- `pubspec.yaml` — 版本号 1.2.4+4 → 1.2.5+5

### 构建信息
- **构建时间**: 2026-05-11 22:58
- **构建耗时**: 1m 26s
- **APK 大小**: 50.9 MB
- **签名验证**: ✅ v2 签名通过
- **APK 文件**: `hermes_storage_v1.2.5.apk`

---

## v1.2.4 (2026-05-11 22:41) — 修复无封面图点击问题 ✅

### 问题描述
- 房屋卡片无封面图时，点击占位区域会进入错误的图片全屏画面
- Docker Web 版行为：点击空白区域应进入下一级目录

### 修复内容
- **_CoverImage 组件重构**：从 StatelessWidget 改为 StatefulWidget
- **无图片时**：点击占位区域不再拦截事件，让点击冒泡到父级 InkWell（进入下一级）
- **有图片时**：点击封面图可全屏查看
- **图片加载失败时**：自动切换为占位图，点击同样冒泡到父级

### 修改文件
- `lib/screens/home_screen.dart` — _CoverImage 组件重构
- `pubspec.yaml` — 版本号 1.2.3+3 → 1.2.4+4

### 构建信息
- **构建时间**: 2026-05-11 22:41
- **构建方式**: Gradle assembleRelease
- **APK 大小**: 50.86 MB
- **签名验证**: ✅ v2 签名通过
- **APK 文件**: `hermes_storage_v1.2.4.apk`

---

## v1.2.3 (2026-05-11 22:27) — 搜索功能完善 ✅

### 更新内容
- **搜索页图片显示**: 从搜索结果中读取 `images` 字段，显示第一张图片缩略图
- **图片加载容错**: 无图或加载失败时显示占位图
- **多字段名兼容**: 支持中英文键名（物品名称/item_name、所属房屋/house 等）
- **搜索结果点击进入详情**: 点击搜索结果直接打开物品详情弹窗
- **详情页完整功能**: 基本信息、描述、变更历史、图片网格、操作按钮（取出/销毁/转移/删除）
- **版本号更新**: pubspec.yaml 更新为 `1.2.3+3`

### 修改文件
- `lib/screens/search_screen.dart` — 完整重写
- `pubspec.yaml` — 版本号 1.0.0+1 → 1.2.3+3

### 构建信息
- **构建时间**: 2026-05-11 22:27
- **构建方式**: Gradle assembleRelease（SOLO MTC 终端直接构建）
- **APK 大小**: 50.86 MB
- **签名验证**: ✅ v2 签名通过
- **APK 文件**: `hermes_storage_v1.2.3.apk`

---

## v1.2.2 (2026-05-11) — APK 正式构建完成 ✅

### 构建信息
- **构建时间**: 2026-05-11 21:48
- **APK 文件**: `hermes_storage_v1.2.0.apk`
- **文件大小**: 50.64 MB
- **构建方式**: 通过 `build_release_apk.bat` 脚本完整构建
- **签名验证**: ✅ v2 签名通过

### 验签结果
```
Verifies
Verified using v2 scheme (APK Signature Scheme v2): true
Number of signers: 1
```

### 文件位置
```
C:\Users\djw\Desktop\trae\
├── hermes_storage_v1.2.0.apk          ← 最新版本 APK（推荐使用）
├── hermes_storage.apk                  ← 同步拷贝
├── CHANGELOG.md                        ← 本文件
└── hermes_app/
    └── android/app/build/outputs/apk/release/app-release.apk  ← 构建源文件
```

### 包含功能（v1.2.0 代码完全生效）
| 功能 | 状态 | 说明 |
|------|------|------|
| 全局新增物品按钮 | ✅ | 首页 AppBar + 底部 FAB 双入口 |
| 房屋卡片式展示 | ✅ | 带封面图、房间数、物品数统计 |
| 封面图全屏查看 | ✅ | 点击房屋封面图可放大查看 |
| 物品卡片展示 | ✅ | 带图片、名称、位置、描述 |
| 物品详情图片网格 | ✅ | 3列网格展示，点击全屏查看 |
| 变更历史记录 | ✅ | 显示物品所有操作记录 |
| 空状态提示 | ✅ | 无数据时显示引导界面 |

### 代码更新文件
- `lib/screens/home_screen.dart` — 首页卡片式展示 + 全局新增物品入口 + 封面图预览
- `lib/screens/items_screen.dart` — 物品卡片 + 详情页图片网格 + 变更历史记录

### 构建环境
- **Flutter**: C:\flutter
- **Java**: jdk-17.0.14+7
- **Android SDK**: android-sdk
- **构建脚本**: `build_release_apk.bat`

---

## v1.2.1 (2026-05-11) — APK 预构建（已废弃）

> 注：此版本为临时复制，未包含最新代码。请使用 v1.2.2 版本。

---

## v1.0.0 (2025-05-07) — Docker Web 版首次发布

### 技术架构
- **后端**: Python FastAPI + 文件系统存储（无需数据库）
- **前端**: 纯 HTML/CSS/JS（响应式设计，手机/电脑均可使用）
- **部署**: Docker 容器化 + GitHub Actions 自动构建
- **数据存储**: 群晖共享文件夹（txt 台账 + 图片文件）
- **GitHub 仓库**: https://github.com/bbv52021/hermes-storage-app
- **容器镜像**: `ghcr.io/bbv52021/hermes-storage-app:latest`

### 已完成功能

#### 核心数据结构
- 四级目录结构：房屋(House) → 房间(Room) → 位置(Location) → 物品(Item)
- 纯文件系统存储，以 txt 台账 + 图片文件管理数据
- 全局索引文件（物品总索引清单.txt）

#### 后端 API（main.py）
- `GET /api/tree` — 获取完整目录树形结构
- `GET /api/stats` — 获取统计数据（房屋/房间/位置/物品数量）
- `GET /api/index` — 获取全局物品索引
- `POST /api/index/refresh` — 刷新全局索引（扫描所有台账重建）
- `GET /api/search?keyword=xx` — 搜索物品（含图片信息）
- `POST /api/items` — 新增物品入库
- `GET /api/items/{house}/{room}/{location}/{item}` — 获取物品详情（台账+图片列表）
- `PUT /api/items/{house}/{room}/{location}/{item}` — 更新物品信息
- `DELETE /api/items/{house}/{room}/{location}/{item}` — 删除物品
- `POST /api/items/.../images` — 上传物品图片
- `GET /api/items/.../images/{img}` — 获取物品图片
- `POST /api/items/.../checkout` — 记录取出
- `POST /api/items/.../destroy` — 标记销毁
- `POST /api/items/.../transfer` — 转移位置
- `PUT/DELETE /api/houses/{house}` — 重命名/删除房屋
- `PUT/DELETE /api/houses/{house}/rooms/{room}` — 重命名/删除房间
- `PUT/DELETE /api/houses/{house}/rooms/{room}/locations/{loc}` — 重命名/删除位置
- `GET/POST/DELETE /api/houses/{house}/image` — 房屋封面图管理
- `GET/POST/DELETE /api/houses/{house}/rooms/{room}/image` — 房间封面图管理
- `GET/POST/DELETE /api/houses/{house}/rooms/{room}/locations/{loc}/image` — 位置封面图管理

#### 前端界面（index.html）
- 顶部导航栏（品牌 Logo + 搜索框 + 新增物品按钮 + 刷新索引按钮）
- 统计卡片（房屋/房间/物品总数/索引记录）
- 面包屑导航（全部物品 > 房屋 > 房间 > 位置）
- 工具栏（网格/列表视图切换 + 刷新按钮）
- 房屋卡片网格展示（封面图 + 名称 + 房间数/物品数 + 缩略图预览条）
- 房间卡片网格展示（封面图 + 名称 + 位置数/物品数 + 缩略图预览条）
- 位置卡片网格展示（封面图 + 名称 + 物品数 + 缩略图预览条）
- 物品卡片网格展示（封面图 + 名称 + 位置 + 描述 + 更新时间 + 图片数量角标）
- 物品列表表格展示（缩略图 + 名称 + 位置 + 描述 + 图片数 + 更新时间 + 操作按钮）
- 新增物品模态框（房屋/房间/位置/名称/描述 + 多图片上传 + 拖拽上传 + 图片预览）
- 物品详情模态框（台账信息 + 物品描述 + 变更历史记录 + 图片网格 + 操作按钮）
- 图片全屏查看器（点击放大，ESC 关闭）
- 搜索功能（顶部搜索框实时搜索 + 回车展示完整搜索结果页）
- Toast 通知（成功/失败/信息三种样式）
- 空状态提示（无物品时引导用户新增）
- 目录操作（重命名/删除/上传封面图/替换封面图/删除封面图）
- 物品操作（记录取出/标记销毁/转移位置/删除）

#### Docker 部署
- Dockerfile 配置
- docker-compose.yml 配置
- GitHub Actions 自动构建（`.github/workflows/docker-build.yml`）
- 推送到 GHCR (GitHub Container Registry)
- 群晖 NAS 部署脚本

### 已修复问题
| 问题 | 修复方案 |
|------|----------|
| index.html 重复追加导致 10MB+ 文件 | 从 GitHub 历史恢复正确版本 |
| 群晖 `@eaDir` 系统文件夹显示 | 后端 API 过滤 `@eaDir` 目录 |
| Emoji 按钮乱码 | 改用 SVG 图标 |
| 封面图在子目录显示 | 过滤与父目录同名的图片文件 |
| 单张缩略图排版问题 | 少于 2 张时不显示缩略图条 |

---

## v1.1.0 (2026-05-07) — Flutter APP 版首次构建

### 技术架构
- **框架**: Flutter 3.41.9 / Dart (>=3.0.0 <4.0.0)
- **状态管理**: Provider (ChangeNotifier)
- **网络请求**: http 包 + 自建 ApiService
- **本地存储**: SharedPreferences（缓存服务器地址）
- **UI 设计**: Material 3 设计规范，支持亮色/暗色主题
- **包名**: `com.example.hermes_storage`

### 已完成功能
- 首页：分类导航，统计展示（房屋/房间/位置/物品数量）
- 房间管理：列表展示，重命名/删除/上传封面图/删除封面图
- 位置管理：列表展示，重命名/删除/上传封面图/删除封面图
- 物品管理：列表展示，新增（名称+描述+多图），查看详情
- 物品操作：记录取出、标记销毁、转移位置、删除物品
- 全局搜索：关键词搜索物品
- 设置页面：服务器地址配置 + 连接测试
- 数据同步：通过 API 与后端实时交互
- Release 签名配置（hermes-release.jks）

### 已临时禁用的功能（需 NDK 原生编译）
- camera: ^0.10.5+9 — 相机拍照
- barcode_scan2: ^4.3.3 — 条码扫描
- speech_to_text: ^6.6.0 — 语音输入

### 构建状态
| 项目 | 状态 |
|------|------|
| Dart 代码编译 | ✅ 通过 |
| Kotlin 代码编译 | ✅ 通过 |
| APK 打包 | ✅ 通过（49.3MB） |
| Release 签名 | ✅ 已配置 |
| 真机安装测试 | ❌ 未完成（MIUI 安全扫描阻止） |

### 已知问题
- MIUI 安装被阻止（红米 K50 至尊版）
- Kotlin 编译守护进程临时文件创建受限（沙箱环境）
- Flutter 插件路径硬编码问题

---

## v1.2.0 (2026-05-11) — Flutter APP 功能补全（对齐 Docker Web 版）

### 修改文件
- `lib/screens/home_screen.dart` — 首页全面重构
- `lib/screens/items_screen.dart` — 物品列表页全面重构

### 新增功能

#### 首页 (home_screen.dart)
- ✅ **全局新增物品入口**：AppBar 新增「+」按钮 + 底部 FloatingActionButton，任意页面可快速录入物品
- ✅ **新增物品弹窗**：完整表单（房屋/房间/位置/名称/描述），支持从相册选择多图 + 拍照
- ✅ **自动补全输入**：房屋和房间输入框支持 Autocomplete，自动提示已有名称
- ✅ **图片预览**：新增物品时可预览已选图片，支持删除单张
- ✅ **必填项校验**：空字段提示，操作成功/失败 SnackBar 反馈
- ✅ **房屋卡片式展示**：从纯文字 ListTile 升级为带封面图的卡片（与 Docker Web 版对齐）
- ✅ **封面图预览**：房屋卡片顶部显示封面图，点击可全屏查看
- ✅ **封面图全屏查看**：InteractiveViewer 支持缩放查看
- ✅ **封面图错误处理**：图片加载失败时显示默认占位图标
- ✅ **空状态页面**：无数据时显示引导界面 + 新增按钮
- ✅ **加载失败页面**：网络异常时显示错误信息 + 重试按钮
- ✅ **统计卡片升级**：带彩色图标背景的统计展示
- ✅ **删除确认弹窗**：删除房屋/封面图时增加二次确认
- ✅ **_CoverImage 组件**：封装封面图加载逻辑，支持默认占位和错误处理

#### 物品列表页 (items_screen.dart)
- ✅ **物品卡片式展示**：从纯文字 ListTile 升级为带封面图的卡片（与 Docker Web 版对齐）
- ✅ **物品封面图**：卡片顶部显示物品第一张图片，无图片时显示占位
- ✅ **物品信息展示**：名称 + 位置路径 + 描述（最多2行截断）
- ✅ **物品详情全面升级**：
  - 台账信息网格（所属房屋/房间/位置/入库时间/最后更新/图片数量）
  - 物品描述展示
  - **变更历史记录**（与 Docker Web 版对齐，带时间线样式）
  - **图片网格展示**（3列网格，点击全屏查看）
  - 操作按钮（记录取出/标记销毁/转移位置/删除物品）
- ✅ **图片全屏查看**：InteractiveViewer 支持缩放
- ✅ **空状态页面**：无物品时显示引导界面
- ✅ **新增物品预填路径**：弹窗中显示当前路径（房屋/房间/位置）
- ✅ **新增物品支持拍照**：除相册选择外增加拍照入口
- ✅ **DraggableScrollableSheet**：详情页可拖拽调整高度
- ✅ **_ItemFirstImage 组件**：通过 API 获取图片列表后显示第一张

### 功能对比（v1.2.0 vs Docker Web 版）

| 功能 | Docker Web | APP v1.1.0 | APP v1.2.0 |
|------|-----------|------------|------------|
| 全局新增物品按钮 | ✅ | ❌ | ✅ |
| 新增物品完整表单 | ✅ | ❌ 仅物品列表页 | ✅ 任意页面 |
| 房屋/房间自动补全 | ❌ 手动输入 | ❌ | ✅ |
| 物品卡片展示（带封面图） | ✅ | ❌ 纯文字列表 | ✅ |
| 物品图片网格展示 | ✅ | ❌ | ✅ |
| 图片全屏查看 | ✅ | ❌ | ✅ |
| 封面图预览 | ✅ | ❌ 仅图标 | ✅ |
| 变更历史记录 | ✅ | ❌ | ✅ |
| 空状态提示 | ✅ | ❌ | ✅ |
| 加载失败提示 | ✅ | ✅ 简单文字 | ✅ 图标+重试 |
| 网格/列表视图切换 | ✅ | ❌ | ❌ 待后续 |
| 面包屑导航 | ✅ | ❌ | ❌ 待后续 |
| 缩略图预览条 | ✅ | ❌ | ❌ 待后续 |
| 搜索结果带图片 | ✅ | ❌ | ❌ 待后续 |
| 拖拽上传 | ✅ | N/A | N/A（移动端不支持） |

### 待后续迭代功能
- [ ] 网格/列表视图切换
- [ ] 面包屑导航
- [ ] 搜索结果卡片式展示（带图片）
- [ ] 缩略图预览条
- [ ] 新增房屋/房间/位置的入口（目前只能通过后端或 AI 助手创建）
- [ ] 恢复相机拍照功能（需 NDK 原生编译环境）
- [ ] 恢复条码扫描功能
- [ ] 恢复语音输入功能
- [ ] 离线缓存（sqflite 已引入但未使用）
- [ ] 真机安装测试（解决 MIUI 安全扫描问题）

---

*最后更新: 2026-05-11*
