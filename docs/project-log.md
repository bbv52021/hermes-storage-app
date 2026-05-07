# Hermes 物品收纳助手 - 项目记录

## 项目简介
群晖 Docker 部署的 Web 物品管理系统，支持房屋/房间/位置三级管理。

## 核心功能
- ✅ 物品增删改查（名称、描述、图片）
- ✅ 三级目录：房屋 → 房间 → 位置
- ✅ 目录重命名/删除/封面图管理
- ✅ 物品取出/销毁/转移记录
- ✅ 全局搜索
- ✅ 操作日志写入索引文件

## 技术栈
- 后端：Python + FastAPI
- 前端：原生 HTML/JS
- 部署：Docker + GitHub Actions

## 镜像地址
```
ghcr.io/bbv52021/hermes-storage-app:latest
```

## 部署命令
```bash
docker pull ghcr.io/bbv52021/hermes-storage-app:latest
docker run -d --name hermes-storage -p 8900:8000 \
  -v /volume1/群晖共享文件夹01/物品存储:/data/物品存储 \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  ghcr.io/bbv52021/hermes-storage-app:latest
```

## 待办事项
- [ ] 数据备份功能
- [ ] 多用户权限
- [ ] 扫码快速录入

## 关键设计决策
1. 封面图命名固定为目录名（如 `长兴爱侣公司.jpg`）
2. 过滤群晖系统目录（`@eaDir` 等）
3. 操作日志追加到 `物品总索引清单.txt`
4. 少于2张物品图片时不显示缩略图条

## 更新历史
- 2025-05-07: 完成目录层级操作功能（重命名/删除/封面图）
- 2025-05-07: 修复群晖系统目录显示问题
- 2025-05-07: 修复封面图显示为卡片问题
