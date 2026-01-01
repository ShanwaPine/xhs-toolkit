# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

小红书(XHS)创作者自动化工具包,通过MCP协议与AI客户端集成,支持内容发布、数据采集和AI分析。

- **语言**: Python ≥3.10
- **版本**: v1.3.0
- **核心技术**: Selenium浏览器自动化 + FastMCP协议

## 常用命令

### 依赖管理
```bash
# 推荐: 使用uv(更快)
uv sync                           # 安装依赖
uv run python xhs_toolkit.py      # 运行命令

# 传统: 使用pip
pip install -r requirements.txt   # 安装依赖
python xhs_toolkit.py             # 运行命令
```

### 启动工具
```bash
./xhs                            # 交互式菜单(Mac/Linux)
xhs.bat                          # 交互式菜单(Windows)
python xhs_toolkit.py --help     # 查看所有命令
```

### Cookie管理
```bash
python xhs_toolkit.py cookie save      # 获取并保存Cookie
python xhs_toolkit.py cookie validate  # 验证Cookie有效性
```

### MCP服务器
```bash
# stdio模式(Claude Desktop)
python -m src.server.mcp_server --stdio

# SSE模式(Cherry Studio/n8n)
python xhs_toolkit.py server start
python xhs_toolkit.py server status
```

### 手动操作
```bash
python xhs_toolkit.py manual collect --type all      # 采集所有数据
python xhs_toolkit.py manual browser --page publish  # 打开发布页面
python xhs_toolkit.py manual export --format excel   # 导出Excel
python xhs_toolkit.py manual analyze                 # 分析数据趋势
```

### 开发工具
```bash
# 代码格式化
black .

# 测试(如需添加测试)
pytest tests/
```

## 架构设计

### 分层架构

```
用户交互层 (CLI/AI客户端)
    ↓
服务层 (MCP服务器/任务管理)
    ↓
业务逻辑层 (XHSClient/功能组件)
    ↓
核心支撑层 (浏览器/配置/存储)
```

### 核心模块结构

```
src/
├── auth/                    # 认证模块
│   ├── cookie_manager.py   # Cookie生命周期管理
│   └── smart_auth_server.py # MCP智能认证
│
├── core/                    # 核心模块
│   ├── browser.py          # ChromeDriver管理(启动/配置/远程连接)
│   ├── config.py           # 配置管理(环境变量/跨平台路径)
│   └── exceptions.py       # 统一异常处理
│
├── xiaohongshu/            # 小红书业务逻辑
│   ├── client.py           # 主客户端(发布/采集入口)
│   ├── models.py           # 数据模型(XHSNote)
│   ├── components/         # 功能组件(模块化设计)
│   │   ├── content_filler.py    # 内容填充
│   │   ├── file_uploader.py     # 文件上传(图片/视频)
│   │   ├── publisher.py         # 发布器
│   │   └── topic_automation.py  # 话题自动化(v1.3.0核心功能)
│   └── data_collector/     # 数据采集器
│       ├── dashboard.py    # 仪表板数据
│       ├── content_analysis.py # 内容分析
│       └── fans.py         # 粉丝数据
│
├── server/                 # MCP服务器
│   └── mcp_server.py      # FastMCP实现/工具注册/任务管理
│
├── data/                   # 数据管理
│   ├── scheduler.py       # 定时任务(APScheduler + cron)
│   ├── storage_manager.py # 存储管理器(统一接口)
│   └── storage/           # 存储实现
│       ├── base.py        # 抽象基类
│       └── csv_storage.py # CSV存储(中文表头)
│
├── utils/                  # 工具函数
│   ├── image_processor.py # 图片处理(本地/网络URL)
│   ├── logger.py          # 日志管理(loguru)
│   └── text_utils.py      # 文本处理/路径解析
│
└── cli/                    # 命令行接口
    └── manual_commands.py  # 手动操作命令
```

### 关键入口文件

- **xhs_toolkit.py**: CLI主入口,命令行参数解析
- **xhs_toolkit_interactive.py**: 交互式菜单入口
- **src/server/mcp_server.py**: MCP服务器入口

## 核心技术实现

### 1. 话题自动化(v1.3.0核心功能)

**位置**: `src/xiaohongshu/components/topic_automation.py`

**关键技术点**:
- 使用`ActionChains`逐字符输入模拟真实用户操作(直接send_keys无法触发下拉菜单)
- 等待并选择话题下拉菜单项
- 验证DOM元素`data-topic`属性确保话题转换成功
- 多重备用方案(JavaScript事件模拟)提高成功率

### 2. 智能路径解析

**位置**: `src/utils/text_utils.py` → `smart_parse_file_paths()`

**支持格式**:
- 逗号分隔: `"a.jpg,b.jpg"`
- JSON数组: `'["a.jpg","b.jpg"]'`
- Python字面量: `"[a.jpg,b.jpg]"`
- 真实数组: `["a.jpg", "b.jpg"]`
- 网络URL: `"https://example.com/image.jpg"`
- 混合格式

### 3. 异步任务管理

**位置**: `src/server/mcp_server.py` → `TaskManager`

**任务状态机**: `pending → uploading → filling → publishing → completed/failed`

- 后台异步执行避免MCP调用超时
- 支持任务状态查询(`check_task_status`)和结果获取(`get_task_result`)

### 4. 浏览器管理

**位置**: `src/core/browser.py` → `ChromeDriverManager`

**支持模式**:
- **本地模式**: 启动本地Chrome实例
- **远程模式**: 连接Docker容器中的Selenium服务器
- **无头模式**: HEADLESS=true配置

**关键配置**: `.env`文件中的`CHROME_PATH`, `WEBDRIVER_CHROME_DRIVER`, `ENABLE_REMOTE_BROWSER`

### 5. 数据采集与存储

**采集流程**: 定时任务(cron) → XHSClient → 数据采集器 → StorageManager → CSV文件

**存储特点**:
- 使用中文表头便于AI理解
- 默认CSV存储(data/creator_db/)
- 可扩展其他存储类型(继承BaseStorage)

## 开发指南

### 添加新的MCP工具

在`src/server/mcp_server.py`中:

```python
@self.mcp.tool()
def your_new_tool(param: str) -> dict:
    """工具描述"""
    # 实现逻辑
    return {"status": "success"}
```

### 添加新的功能组件

1. 在`src/xiaohongshu/components/`创建新组件
2. 在`XHSClient`中集成组件方法
3. (可选)在MCP服务器中注册为工具

### 添加新的数据采集器

1. 在`src/xiaohongshu/data_collector/`创建采集器
2. 在`XHSClient`中添加采集方法
3. 在`StorageManager`中保存数据

### 扩展存储类型

1. 继承`src/data/storage/base.py`中的`BaseStorage`
2. 实现`save()`和`load()`方法
3. 在`StorageManager`中注册新存储类型

## 配置管理

### 必需配置(.env文件)

```bash
# Chrome配置(必须)
CHROME_PATH=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
WEBDRIVER_CHROME_DRIVER=/usr/local/bin/chromedriver

# Cookie文件
COOKIES_FILE=xhs_cookies.json

# 浏览器选项
HEADLESS=false              # 无头模式
DISABLE_IMAGES=false        # 禁用图片加载

# 远程浏览器(Docker部署)
ENABLE_REMOTE_BROWSER=false
REMOTE_BROWSER_HOST=localhost
REMOTE_BROWSER_PORT=4444

# 定时采集
ENABLE_AUTO_COLLECTION=true
COLLECTION_SCHEDULE=0 1 * * *  # cron表达式
```

### 环境检测

配置类`XHSConfig`会自动检测:
- 操作系统平台(macOS/Windows/Linux)
- Chrome浏览器路径
- ChromeDriver路径

## 设计模式

### 组件化设计

每个功能组件遵循单一职责原则:
- `ContentFiller`: 仅负责内容填充
- `FileUploader`: 仅负责文件上传
- `TopicAutomation`: 仅负责话题自动化

### 依赖注入

```python
class XHSClient:
    def __init__(self, config: XHSConfig):
        self.config = config
        self.browser_manager = ChromeDriverManager(config)
```

### 接口抽象

所有存储实现继承`BaseStorage`,便于扩展新存储类型。

## 注意事项

### ChromeDriver版本匹配

确保ChromeDriver版本与Chrome浏览器版本完全一致,这是最常见的问题来源。

### Cookie有效期

Cookie需要定期更新,登录失败时使用`python xhs_toolkit.py cookie save`重新获取。

### 远程浏览器权限

使用Docker部署时,确保`./chrome-data`目录有正确的读写权限。

### 视频上传超时

视频上传默认超时2分钟,大文件可能需要调整超时设置。

## 日志调试

- **日志文件**: `xhs_toolkit.log`
- **日志级别**: 通过`.env`中的`LOG_LEVEL`配置
- **DEBUG模式**: `DEBUG_MODE=true`启用详细日志

查看日志:
```bash
tail -f xhs_toolkit.log
```

## 文档参考

- **README.md**: 用户使用指南、功能清单、安装说明
- **docs/ARCHITECTURE.md**: 完整架构文档(1600+行)
- **docs/小红书话题标签自动化实现方案.md**: 话题自动化技术细节
- **docs/smart_path_parsing.md**: 路径解析实现细节
