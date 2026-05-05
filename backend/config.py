# Hermes 收纳助手 - 后端配置
import os

# 群晖共享文件夹01/物品存储 的根路径
# Docker部署时通过环境变量或挂载卷配置
STORAGE_ROOT = os.getenv("STORAGE_ROOT", "/data/物品存储")

# 全局索引文件名
INDEX_FILE = "物品总索引清单.txt"

# 台账文件名
LEDGER_FILE_TEMPLATE = "{item_name}.txt"

# 图片命名格式
IMAGE_NAME_TEMPLATE = "{item_name}_{datetime}_{seq}.{ext}"

# 允许的图片扩展名
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# 禁止的文件名字符
FORBIDDEN_CHARS = r'\/:*?"<>|'

# 最大图片大小 (10MB)
MAX_IMAGE_SIZE = 10 * 1024 * 1024

# 日期时间格式
DATETIME_FORMAT = "%Y%m%d%H%M%S"
