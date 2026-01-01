# 小红书工具包 (xhs-toolkit) 架构文档

## 目录

- [项目概述](#项目概述)
- [核心架构](#核心架构)
- [模块详解](#模块详解)
- [数据流分析](#数据流分析)
- [技术栈](#技术栈)
- [设计模式与原则](#设计模式与原则)
- [关键实现细节](#关键实现细节)
- [扩展指南](#扩展指南)

---

## 项目概述

### 项目简介

**xhs-toolkit** 是一个基于 MCP 协议的小红书自动化工具包，支持通过 AI 对话完成内容发布、数据采集和分析。项目采用 Python 开发，使用 Selenium 进行浏览器自动化，通过 FastMCP 实现与 AI 客户端的集成。

### 核心特性

- **MCP 协议集成**：支持 Claude Desktop、Cherry Studio 等 AI 客户端
- **智能发布**：支持图文、视频笔记发布，带话题标签功能
- **数据采集**：自动采集创作者数据，支持定时任务
- **AI 分析**：中文表头数据，便于 AI 直接分析
- **跨平台支持**：macOS、Windows、Linux 自动适配
- **远程浏览器**：支持 Docker 容器化部署

### 项目统计

- **代码量**：约 10,906 行 Python 代码
- **版本**：v1.3.0
- **Python 要求**：≥3.10
- **开源协议**：MIT

---

## 核心架构

### 分层架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户交互层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ AI 客户端     │  │ 命令行界面    │  │ 交互式菜单    │      │
│  │ (Claude等)    │  │ (xhs_toolkit) │  │ (interactive) │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          │ MCP Protocol     │ CLI Commands     │ Menu
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      服务层                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              MCP 服务器 (MCPServer)                  │   │
│  │  - 工具注册 (smart_publish_note, login, etc.)        │   │
│  │  - 任务管理 (TaskManager)                           │   │
│  │  - 异步调度                                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                      业务逻辑层                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          小红书客户端 (XHSClient)                     │  │
│  │  - publish_note()      - collect_creator_data()      │  │
│  │  - collect_dashboard() - collect_content_analysis()  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  功能组件模块     │  │  数据采集模块     │               │
│  │  - ContentFiller │  │  - Dashboard     │               │
│  │  - FileUploader  │  │  - ContentAnalysis│              │
│  │  - Publisher     │  │  - Fans          │               │
│  │  - TopicAutomation│ │                  │               │
│  └──────────────────┘  └──────────────────┘               │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                      核心支撑层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ 浏览器管理    │  │ 认证管理      │  │ 配置管理      │     │
│  │ ChromeDriver │  │ CookieManager │  │ XHSConfig    │     │
│  │ Manager      │  │ SmartAuth     │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ 数据存储      │  │ 任务调度      │  │ 工具函数      │     │
│  │ StorageManager│ │ Scheduler     │  │ ImageProcessor│    │
│  │ CSVStorage   │  │ APScheduler   │  │ Logger       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 目录结构

```
xhs-toolkit/
├── src/                          # 源代码主目录
│   ├── __init__.py              # 包初始化
│   ├── auth/                     # 认证模块
│   │   ├── cookie_manager.py    # Cookie 生命周期管理
│   │   └── smart_auth_server.py # MCP 智能认证
│   ├── cli/                      # 命令行接口
│   │   └── manual_commands.py   # 手动操作命令
│   ├── core/                     # 核心模块
│   │   ├── browser.py           # 浏览器驱动管理
│   │   ├── config.py            # 配置管理
│   │   └── exceptions.py        # 异常定义
│   ├── data/                     # 数据管理模块
│   │   ├── scheduler.py         # 定时任务调度器
│   │   ├── storage_manager.py   # 存储管理器
│   │   └── storage/             # 存储实现
│   │       ├── base.py          # 存储接口
│   │       └── csv_storage.py   # CSV 存储
│   ├── server/                   # 服务器模块
│   │   └── mcp_server.py        # MCP 服务器
│   ├── tools/                    # 工具模块
│   │   └── manual_tools.py      # 手动操作工具
│   ├── utils/                    # 工具函数
│   │   ├── image_processor.py   # 图片处理
│   │   ├── logger.py            # 日志管理
│   │   └── text_utils.py        # 文本处理
│   └── xiaohongshu/             # 小红书核心功能
│       ├── client.py            # 客户端
│       ├── models.py            # 数据模型
│       ├── constants.py         # 常量定义
│       ├── interfaces.py        # 接口定义
│       ├── components/          # 功能组件
│       │   ├── content_filler.py    # 内容填充
│       │   ├── file_uploader.py     # 文件上传
│       │   ├── publisher.py         # 发布器
│       │   └── topic_automation.py  # 话题自动化
│       └── data_collector/      # 数据采集
│           ├── dashboard.py     # 仪表板数据
│           ├── content_analysis.py  # 内容分析
│           └── fans.py          # 粉丝数据
├── docs/                         # 文档目录
├── data/                         # 数据存储
├── xhs_toolkit.py               # CLI 主入口
├── xhs_toolkit_interactive.py   # 交互式菜单入口
└── install_deps.py              # 依赖安装向导
```

---

## 模块详解

### 1. 核心模块 (src/core/)

#### 1.1 配置管理 (config.py)

**核心类：XHSConfig**

```python
class XHSConfig:
    """配置管理中心"""
    - 环境变量加载与管理
    - Chrome/ChromeDriver 路径自动检测
    - 跨平台路径适配
    - 远程浏览器配置支持
```

**关键配置项：**

```bash
# Chrome 配置
CHROME_PATH=/Applications/Google Chrome.app
WEBDRIVER_CHROME_DRIVER=/usr/local/bin/chromedriver

# 远程浏览器
ENABLE_REMOTE_BROWSER=true
REMOTE_BROWSER_HOST=localhost
REMOTE_BROWSER_PORT=9222

# 浏览器选项
HEADLESS=false
DISABLE_IMAGES=false
```

**设计亮点：**
- 自动检测系统平台并适配路径
- 支持远程浏览器连接（Docker 部署场景）
- 配置验证机制确保参数有效性

#### 1.2 浏览器管理 (browser.py)

**核心类：ChromeDriverManager**

```python
class ChromeDriverManager:
    """Selenium WebDriver 生命周期管理"""

    主要方法：
    - __init__(): 初始化配置
    - _setup_chrome_options(): 配置 Chrome 选项
    - _setup_remote_browser(): 远程浏览器连接
    - start(): 启动浏览器
    - load_cookies(): 加载 Cookie
    - quit(): 关闭浏览器
```

**关键实现：**

1. **Chrome 选项配置**
   ```python
   # 无头模式
   --headless=new
   --headless

   # 性能优化
   --disable-images
   --disable-gpu
   --no-sandbox
   --disable-dev-shm-usage
   ```

2. **远程浏览器连接**
   ```python
   from selenium.webdriver.remote.webdriver import WebDriver

   driver = WebDriver(
       command_executor=f"http://{host}:{port}",
       options=chrome_options
   )
   ```

#### 1.3 异常处理 (exceptions.py)

**异常层次结构：**

```python
XHSBaseException
├── BrowserError
├── NetworkError
├── PublishError
├── AuthenticationError
└── DataCollectionError
```

**统一异常处理装饰器：**

```python
@handle_exception
def risky_operation():
    # 自动捕获并格式化异常
    pass
```

---

### 2. 认证模块 (src/auth/)

#### 2.1 Cookie 管理器 (cookie_manager.py)

**核心类：CookieManager**

```python
class CookieManager:
    """Cookie 生命周期管理"""

    主要功能：
    - save_cookies_interactive(): 交互式获取 Cookie
    - save_cookies_auto(): 自动化获取 Cookie
    - load_cookies(): 加载并验证 Cookie
    - _check_required_cookies(): 验证必需 Cookie
```

**关键 Cookie 字段：**
- `web_session`: 会话标识
- `a1`: 认证令牌
- `gid`: 设备标识
- `webId`: Web 端标识

**Cookie 获取流程：**

```
1. 启动浏览器
2. 导航到创作者中心
3. 等待用户登录
4. 提取 Cookie
5. 验证关键字段
6. 保存到 xhs_cookies.json
```

#### 2.2 智能认证服务器 (smart_auth_server.py)

**核心类：SmartAuthServer**

```python
class SmartAuthServer:
    """MCP 模式下的智能认证"""

    四重检测机制：
    1. URL 状态检测
    2. 页面元素检测
    3. 身份验证检测
    4. 错误状态检测
```

**登录检测流程：**

```python
def _check_login_status(driver):
    """智能检测登录状态"""
    # 检查 URL
    if "creator.xiaohongshu.com" in driver.current_url:
        # 检查关键元素
        if element_exists(".profile-info"):
            return True
    return False
```

---

### 3. 小红书业务模块 (src/xiaohongshu/)

#### 3.1 客户端 (client.py)

**核心类：XHSClient**

```python
class XHSClient:
    """小红书操作客户端"""

    发布功能：
    - publish_note(): 发布笔记

    数据采集：
    - collect_creator_data(): 采集创作者数据
    - collect_dashboard_data(): 采集仪表板数据
    - collect_content_analysis_data(): 采集内容分析
    - collect_fans_data(): 采集粉丝数据
```

**发布流程：**

```python
async def publish_note(note: XHSNote):
    # 1. 验证登录
    # 2. 初始化浏览器
    # 3. 导航到发布页面
    # 4. 切换发布模式（图文/视频）
    # 5. 上传文件
    # 6. 填写内容
    # 7. 添加话题标签
    # 8. 点击发布
    # 9. 返回结果
```

#### 3.2 数据模型 (models.py)

**核心模型：XHSNote**

```python
from pydantic import BaseModel

class XHSNote(BaseModel):
    """笔记数据模型"""
    title: str              # 标题（≤50字）
    content: str            # 内容（≤1000字）
    images: list[str] = []  # 图片路径（≤9张）
    videos: list[str] = []  # 视频路径（1个）
    topics: list[str] = []  # 话题标签

    # 智能创建方法
    @classmethod
    def smart_create(cls, **kwargs):
        """支持多种输入格式的智能创建"""
        pass

    @classmethod
    async def async_smart_create(cls, **kwargs):
        """异步版本智能创建"""
        pass
```

**智能路径解析：**

支持的输入格式：
```python
# 1. 逗号分隔
"a.jpg,b.jpg,c.jpg"

# 2. 数组字符串
"[a.jpg,b.jpg,c.jpg]"

# 3. JSON 数组
'["a.jpg","b.jpg","c.jpg"]'

# 4. 真实数组
["a.jpg", "b.jpg", "c.jpg"]

# 5. 网络 URL
"https://example.com/image.jpg"

# 6. 混合格式
["local.jpg", "https://example.com/remote.jpg"]
```

#### 3.3 功能组件 (components/)

##### 3.3.1 内容填充器 (content_filler.py)

```python
class XHSContentFiller:
    """内容填充组件"""

    def fill_title(self, title: str):
        """填写标题"""

    def fill_content(self, content: str):
        """填写正文（保留换行）"""

    def fill_topics(self, topics: list[str]):
        """填写话题标签"""
```

##### 3.3.2 话题自动化 (topic_automation.py)

**v1.3.0 核心功能**

```python
class XHSTopicAutomation:
    """话题标签自动化"""

    基于实测验证的完整实现：
    - 使用 Actions 类逐字符输入
    - JavaScript 事件模拟
    - 完整 DOM 验证（data-topic 属性）
    - 多重备用方案
```

**实现细节：**

```python
def add_topic(driver, topic_text: str):
    """添加单个话题"""

    # 1. 定位输入框
    input_box = driver.find_element(By.CSS_SELECTOR, "#post-textarea")

    # 2. 逐字符输入（触发下拉菜单）
    actions = ActionChains(driver)
    for char in f"#{topic_text}":
        actions.send_keys(char)
        time.sleep(0.05)
    actions.perform()

    # 3. 等待下拉菜单
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".topic-item"))
    )

    # 4. 选择话题
    topic_item = driver.find_element(By.CSS_SELECTOR, ".topic-item")
    topic_item.click()

    # 5. 验证话题转换（检查 data-topic 属性）
    time.sleep(0.5)
    topic_spans = driver.find_elements(By.CSS_SELECTOR, "span[data-topic]")
    assert len(topic_spans) > 0, "话题未成功添加"
```

##### 3.3.3 文件上传器 (file_uploader.py)

```python
class XHSFileUploader:
    """文件上传组件"""

    def upload_images(self, image_paths: list[str]):
        """上传图片（快速上传）"""

    def upload_video(self, video_path: str):
        """上传视频（轮询等待）"""
        # 轮询检测上传进度
        # 等待"上传成功"标识
        # 最长等待 2 分钟
```

**视频上传等待机制：**

```python
def wait_for_video_upload(driver, timeout=120):
    """等待视频上传完成"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        # 检查上传进度
        if "上传成功" in driver.page_source:
            return True
        time.sleep(2)  # 每 2 秒检查一次

    raise TimeoutError("视频上传超时")
```

##### 3.3.4 发布器 (publisher.py)

```python
class XHSPublisher:
    """发布器组件"""

    def publish(self):
        """点击发布按钮"""

    def wait_for_publish_complete(self):
        """等待发布完成"""
```

#### 3.4 数据采集器 (data_collector/)

##### 3.4.1 仪表板数据 (dashboard.py)

```python
def collect_dashboard_data(driver):
    """采集仪表板数据"""
    return {
        "采集时间": datetime.now(),
        "粉丝数": extract_fans_count(),
        "获赞与收藏": extract_likes_count(),
        "浏览量": extract_views_count(),
        # ... 更多指标
    }
```

##### 3.4.2 内容分析数据 (content_analysis.py)

```python
def collect_content_analysis_data(driver, days=7):
    """采集内容分析数据"""
    # 导航到内容分析页面
    # 选择时间范围
    # 提取笔记表现数据
    return [
        {
            "笔记标题": "...",
            "浏览量": 1234,
            "点赞数": 56,
            "评论数": 12,
            # ...
        }
    ]
```

##### 3.4.3 粉丝数据 (fans.py)

```python
def collect_fans_data(driver):
    """采集粉丝数据"""
    return {
        "粉丝总数": 1000,
        "新增粉丝": 50,
        "粉丝增长率": 5.2,
        # ...
    }
```

**数据存储格式：**

所有数据使用 **中文表头** CSV 格式存储，便于 AI 直接分析：

```csv
采集时间,粉丝数,获赞与收藏,浏览量
2025-01-01 10:00:00,1000,5000,10000
2025-01-01 16:00:00,1050,5200,10500
```

---

### 4. MCP 服务器模块 (src/server/)

#### 4.1 MCP 服务器 (mcp_server.py)

**核心类：MCPServer**

```python
from fastmcp import FastMCP

class MCPServer:
    """基于 FastMCP 的 MCP 服务器"""

    def __init__(self):
        self.mcp = FastMCP("xhs-toolkit")
        self.task_manager = TaskManager()
        self._setup_tools()

    def _setup_tools(self):
        """注册 MCP 工具"""
        # 注册所有工具
```

**注册的 MCP 工具：**

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| `test_connection` | 测试连接 | 无 |
| `smart_publish_note` | 发布笔记 | title, content, images, videos, topics |
| `check_task_status` | 查询任务状态 | task_id |
| `get_task_result` | 获取任务结果 | task_id |
| `login_xiaohongshu` | 智能登录 | force_relogin, quick_mode |
| `get_creator_data_analysis` | 获取数据分析 | 无 |

#### 4.2 任务管理器

**核心类：TaskManager**

```python
class TaskManager:
    """异步任务管理"""

    def __init__(self):
        self.tasks = {}  # task_id -> PublishTask

    def create_task(self, note: XHSNote) -> str:
        """创建发布任务"""
        task = PublishTask(note)
        task_id = uuid.uuid4().hex
        self.tasks[task_id] = task

        # 在后台执行任务
        asyncio.create_task(self._execute_task(task_id))

        return task_id

    async def _execute_task(self, task_id: str):
        """后台执行任务"""
        task = self.tasks[task_id]

        try:
            task.status = "uploading"
            # 上传文件

            task.status = "filling"
            # 填写内容

            task.status = "publishing"
            # 发布

            task.status = "completed"
            task.result = "发布成功"

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
```

**任务状态机：**

```
pending → uploading → filling → publishing → completed
                                           ↘ failed
```

#### 4.3 运行模式

**stdio 模式（Claude Desktop）：**

```bash
python -m src.server.mcp_server --stdio
```

**SSE 模式（Cherry Studio、n8n）：**

```bash
python xhs_toolkit.py server start
# 启动 HTTP 服务器，支持 SSE
```

---

### 5. 数据管理模块 (src/data/)

#### 5.1 任务调度器 (scheduler.py)

**核心类：DataCollectionScheduler**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class DataCollectionScheduler:
    """基于 APScheduler 的定时任务调度"""

    def __init__(self, config: XHSConfig):
        self.scheduler = AsyncIOScheduler()
        self.config = config

    def start(self, immediate_collection=True):
        """启动调度器"""
        # 添加 cron 任务
        self.scheduler.add_job(
            self.collect_data,
            CronTrigger.from_crontab(
                self.config.collection_schedule
            )
        )

        # 立即执行一次
        if immediate_collection:
            asyncio.create_task(self.collect_data())

        self.scheduler.start()

    async def collect_data(self):
        """数据采集任务"""
        client = XHSClient(self.config)
        await client.collect_creator_data()
```

**Cron 表达式示例：**

```bash
# 每 6 小时采集一次
COLLECTION_SCHEDULE=0 */6 * * *

# 工作日上午 9 点采集
COLLECTION_SCHEDULE=0 9 * * 1-5

# 每天凌晨 2 点采集
COLLECTION_SCHEDULE=0 2 * * *
```

#### 5.2 存储管理器 (storage_manager.py)

**核心类：StorageManager**

```python
class StorageManager:
    """统一存储接口"""

    def __init__(self, storage_type: str = "csv"):
        if storage_type == "csv":
            self.storage = CSVStorage()
        elif storage_type == "postgresql":
            self.storage = PostgreSQLStorage()

    def save(self, data, data_type: str):
        """保存数据"""
        self.storage.save(data, data_type)

    def load(self, data_type: str):
        """加载数据"""
        return self.storage.load(data_type)
```

**存储接口：**

```python
from abc import ABC, abstractmethod

class BaseStorage(ABC):
    """存储基类"""

    @abstractmethod
    def save(self, data, data_type: str):
        pass

    @abstractmethod
    def load(self, data_type: str):
        pass
```

**CSV 存储实现：**

```python
import pandas as pd

class CSVStorage(BaseStorage):
    """CSV 存储"""

    def save(self, data, data_type: str):
        df = pd.DataFrame(data)
        df.to_csv(f"data/{data_type}.csv",
                  index=False,
                  encoding="utf-8-sig")  # 支持中文

    def load(self, data_type: str):
        return pd.read_csv(f"data/{data_type}.csv")
```

---

### 6. 工具模块 (src/utils/)

#### 6.1 图片处理器 (image_processor.py)

**核心类：ImageProcessor**

```python
import requests
from pathlib import Path

class ImageProcessor:
    """统一图片处理"""

    @staticmethod
    def process_images(image_paths: list[str]) -> list[str]:
        """处理图片路径（本地+网络）"""
        processed = []

        for path in image_paths:
            if path.startswith("http"):
                # 下载网络图片
                local_path = ImageProcessor.download_image(path)
                processed.append(local_path)
            else:
                # 本地图片
                processed.append(path)

        return processed

    @staticmethod
    def download_image(url: str) -> str:
        """下载网络图片到临时目录"""
        response = requests.get(url)

        # 保存到临时目录
        temp_path = Path("/tmp") / f"xhs_{uuid.uuid4().hex}.jpg"
        temp_path.write_bytes(response.content)

        return str(temp_path)
```

#### 6.2 日志管理 (logger.py)

```python
from loguru import logger

# 配置日志
logger.add(
    "logs/xhs_toolkit.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO"
)

# 使用
logger.info("开始发布笔记")
logger.error("发布失败: {}", error)
```

#### 6.3 文本处理 (text_utils.py)

```python
def smart_parse_file_paths(input_data) -> list[str]:
    """智能解析文件路径"""

    # 1. 已经是列表
    if isinstance(input_data, list):
        return input_data

    # 2. 尝试 JSON 解析
    try:
        result = json.loads(input_data)
        if isinstance(result, list):
            return result
    except:
        pass

    # 3. 尝试 ast.literal_eval
    try:
        result = ast.literal_eval(input_data)
        if isinstance(result, list):
            return result
    except:
        pass

    # 4. 逗号分隔
    if "," in input_data:
        return [p.strip() for p in input_data.split(",")]

    # 5. 单个文件
    return [input_data]
```

---

### 7. 命令行接口 (src/cli/)

#### 7.1 手动操作命令 (manual_commands.py)

**可用命令：**

```bash
# 数据收集
./xhs manual collect --type all
./xhs manual collect --type dashboard

# 浏览器操作
./xhs manual browser --page publish
./xhs manual browser --page dashboard

# 数据管理
./xhs manual export --format excel
./xhs manual export --format json
./xhs manual analyze
./xhs manual backup
./xhs manual restore
```

---

## 数据流分析

### 1. 发布笔记数据流

```
┌─────────────┐
│  AI 客户端   │
│  (Claude)   │
└──────┬──────┘
       │ MCP 调用
       │ smart_publish_note(title, content, images, topics)
       ▼
┌──────────────────────────────────────────┐
│           MCP 服务器                      │
│  1. 解析参数                              │
│  2. 创建 PublishTask                      │
│  3. 返回 task_id                          │
│  4. 后台执行任务                          │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│         XHSClient.publish_note()         │
│  1. 验证 Cookie                           │
│  2. 初始化浏览器                          │
│  3. 导航到发布页面                        │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│      ImageProcessor.process_images()     │
│  1. 识别本地/网络图片                     │
│  2. 下载网络图片                          │
│  3. 返回本地路径列表                      │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│      XHSFileUploader.upload_images()     │
│  1. 定位上传按钮                          │
│  2. 通过 send_keys 上传文件               │
│  3. 等待上传完成                          │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│     XHSContentFiller.fill_content()      │
│  1. 填写标题                              │
│  2. 填写正文（保留换行）                   │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│   XHSTopicAutomation.add_topics()        │
│  1. 逐字符输入话题                        │
│  2. 等待下拉菜单                          │
│  3. 选择话题                              │
│  4. 验证 data-topic 属性                  │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│        XHSPublisher.publish()            │
│  1. 点击发布按钮                          │
│  2. 等待发布完成                          │
│  3. 返回发布结果                          │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│          TaskManager                     │
│  1. 更新任务状态为 completed              │
│  2. 保存发布结果                          │
└──────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│  AI 客户端   │
│  调用        │
│  get_task_  │
│  result()   │
│  获取结果    │
└─────────────┘
```

### 2. 数据采集数据流

```
┌─────────────────────┐
│   定时任务触发       │
│   (cron: 0 */6 * * *)│
└──────┬──────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  DataCollectionScheduler.collect_data()  │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│   XHSClient.collect_creator_data()       │
│   1. 加载 Cookie                          │
│   2. 初始化浏览器                          │
└──────┬───────────────────────────────────┘
       │
       ├──────────────────┬──────────────────┐
       ▼                  ▼                  ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Dashboard  │  │   Content   │  │    Fans     │
│  Collector  │  │  Analysis   │  │  Collector  │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       │                │                │
       └────────────────┴────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────┐
│       StorageManager.save()              │
│       CSVStorage.save()                  │
│       保存到 data/creator_db/*.csv        │
│       使用中文表头                        │
└──────────────────────────────────────────┘
```

### 3. AI 数据分析数据流

```
┌─────────────┐
│  AI 客户端   │
│  请求分析    │
└──────┬──────┘
       │ MCP 调用
       │ get_creator_data_analysis()
       ▼
┌──────────────────────────────────────────┐
│         MCP 服务器                        │
│  1. 读取 CSV 文件                         │
│  2. 解析中文表头                          │
│  3. 返回结构化数据                        │
└──────┬───────────────────────────────────┘
       │
       ▼
┌─────────────┐
│  AI 客户端   │
│  1. 理解数据 │
│  2. 分析趋势 │
│  3. 提供建议 │
└─────────────┘
```

---

## 技术栈

### 核心框架

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | ≥3.10 | 主开发语言 |
| Selenium | ≥4.15.0 | 浏览器自动化 |
| FastMCP | ≥2.0.0 | MCP 协议实现 |
| Pydantic | ≥2.5.0 | 数据验证 |
| APScheduler | ≥3.10.0 | 定时任务 |

### Web 相关

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | ≥0.104.0 | HTTP 服务器 |
| Uvicorn | ≥0.24.0 | ASGI 服务器 |
| aiohttp | ≥3.9.0 | 异步 HTTP 客户端 |
| requests | ≥2.31.0 | 同步 HTTP 客户端 |

### 数据处理

| 技术 | 版本 | 用途 |
|------|------|------|
| Pandas | ≥2.0.0 | 数据处理 |
| loguru | ≥0.7.2 | 日志管理 |
| python-dotenv | ≥1.0.0 | 环境变量 |

### 安全与加密

| 技术 | 版本 | 用途 |
|------|------|------|
| cryptography | ≥41.0.0 | 加密功能 |
| pycryptodome | ≥3.19.0 | 加密算法 |

---

## 设计模式与原则

### 1. 分层架构

**优势：**
- 职责清晰：每层负责特定功能
- 易于维护：修改某层不影响其他层
- 可测试性：各层可独立测试

**实现：**
```
用户交互层 → 服务层 → 业务逻辑层 → 核心支撑层
```

### 2. 组件化设计

**单一职责原则：**

每个组件只负责一个功能：
- `ContentFiller`：仅负责内容填充
- `FileUploader`：仅负责文件上传
- `TopicAutomation`：仅负责话题自动化

**优势：**
- 代码复用性高
- 易于单元测试
- 降低耦合度

### 3. 依赖注入

**实现：**

```python
class XHSClient:
    def __init__(self, config: XHSConfig):
        self.config = config  # 注入配置
        self.browser_manager = ChromeDriverManager(config)
```

**优势：**
- 便于测试（可注入 Mock 对象）
- 提高灵活性
- 降低耦合度

### 4. 接口抽象

**存储接口示例：**

```python
class BaseStorage(ABC):
    @abstractmethod
    def save(self, data, data_type: str):
        pass
```

**优势：**
- 易于扩展新的存储类型
- 符合开闭原则（对扩展开放，对修改关闭）

### 5. 异步编程

**异步任务管理：**

```python
async def _execute_task(self, task_id):
    """后台异步执行任务"""
    # 避免 MCP 调用超时
```

**优势：**
- 提高并发性能
- 避免阻塞主线程
- 用户体验更好

### 6. 错误处理

**统一异常处理：**

```python
@handle_exception
def risky_operation():
    # 自动捕获并格式化异常
```

**异常层次结构：**
```
XHSBaseException (基类)
├── BrowserError (浏览器相关)
├── NetworkError (网络相关)
├── PublishError (发布相关)
└── ...
```

---

## 关键实现细节

### 1. 话题自动化实现（v1.3.0）

**核心挑战：**
- 直接 `send_keys("#话题")` 无法触发下拉菜单
- 需要完全模拟真实用户操作
- 必须验证话题是否真正添加成功

**解决方案：**

```python
def add_topic_with_validation(driver, topic: str):
    """添加话题并验证"""

    # 1. 逐字符输入（触发下拉菜单）
    actions = ActionChains(driver)
    for char in f"#{topic}":
        actions.send_keys(char)
        time.sleep(0.05)  # 模拟真实打字速度
    actions.perform()

    # 2. 等待下拉菜单出现
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".topic-dropdown .topic-item")
        )
    )

    # 3. 选择第一个话题
    topic_item = driver.find_element(
        By.CSS_SELECTOR, ".topic-dropdown .topic-item"
    )
    topic_item.click()

    # 4. 验证话题转换成功（关键！）
    time.sleep(0.5)
    topic_spans = driver.find_elements(
        By.CSS_SELECTOR, "span[data-topic]"
    )

    if not topic_spans:
        # 备用方案：JavaScript 事件触发
        driver.execute_script("""
            const input = document.querySelector('#post-textarea');
            input.dispatchEvent(new Event('input', {bubbles: true}));
        """)

    # 最终验证
    assert len(topic_spans) > 0, "话题添加失败"
```

**关键点：**
1. **逐字符输入**：模拟真实用户打字
2. **等待下拉菜单**：确保 UI 响应
3. **DOM 验证**：检查 `data-topic` 属性
4. **多重备用方案**：提高成功率

### 2. 智能路径解析

**挑战：**
- 用户输入格式多样（逗号分隔、JSON、数组）
- 需要支持本地路径和网络 URL
- 不同平台传递数据格式不同

**实现：**

```python
def smart_parse_file_paths(input_data):
    """智能解析文件路径"""

    # 1. 已经是列表，直接返回
    if isinstance(input_data, list):
        return input_data

    # 2. JSON 解析
    try:
        result = json.loads(input_data)
        if isinstance(result, list):
            return result
    except:
        pass

    # 3. Python 字面量解析
    try:
        result = ast.literal_eval(input_data)
        if isinstance(result, list):
            return result
    except:
        pass

    # 4. 逗号分隔
    if "," in input_data:
        return [p.strip() for p in input_data.split(",")]

    # 5. 单个文件
    return [input_data]
```

### 3. 远程浏览器连接

**使用场景：**
- Docker 容器化部署
- 复用已登录的浏览器实例
- 远程服务器调试

**实现：**

```python
def _setup_remote_browser(self):
    """连接到远程浏览器"""

    if not self.config.enable_remote_browser:
        return None

    # 连接到远程 Chrome
    remote_url = (
        f"http://{self.config.remote_browser_host}:"
        f"{self.config.remote_browser_port}/wd/hub"
    )

    driver = WebDriver(
        command_executor=remote_url,
        options=self.chrome_options
    )

    return driver
```

**Docker Compose 配置：**

```yaml
services:
  selenium-chrome:
    image: selenium/standalone-chrome:latest
    ports:
      - "4444:4444"  # Selenium
      - "7900:7900"  # VNC
    shm_size: 2g
    environment:
      - SE_VNC_NO_PASSWORD=1
```

### 4. 视频上传等待机制

**挑战：**
- 视频上传时间不确定
- MCP 调用有超时限制
- 需要实时监控上传进度

**实现：**

```python
def wait_for_video_upload(driver, timeout=120):
    """等待视频上传完成"""

    start_time = time.time()
    last_log_time = 0

    while time.time() - start_time < timeout:
        # 检查上传状态
        if "上传成功" in driver.page_source:
            logger.info("视频上传完成")
            return True

        # 每 10 秒打印一次日志
        elapsed = time.time() - start_time
        if elapsed - last_log_time >= 10:
            logger.info(f"视频上传中...已等待 {int(elapsed)} 秒")
            last_log_time = elapsed

        time.sleep(2)  # 每 2 秒检查一次

    raise TimeoutError(f"视频上传超时（{timeout}秒）")
```

### 5. Cookie 验证机制

**关键 Cookie 字段：**

```python
REQUIRED_COOKIES = [
    "web_session",  # 会话标识
    "a1",           # 认证令牌
    "gid",          # 设备标识
    "webId"         # Web 端标识
]

def _check_required_cookies(cookies: list[dict]) -> bool:
    """验证必需的 Cookie 字段"""

    cookie_names = {c["name"] for c in cookies}

    for required in REQUIRED_COOKIES:
        if required not in cookie_names:
            logger.error(f"缺少必需的 Cookie: {required}")
            return False

    return True
```

---

## 扩展指南

### 1. 添加新的 MCP 工具

**步骤：**

1. 在 `src/server/mcp_server.py` 中添加工具：

```python
def _setup_tools(self):
    """注册 MCP 工具"""

    @self.mcp.tool()
    def your_new_tool(param1: str, param2: int) -> dict:
        """
        工具描述

        Args:
            param1: 参数1描述
            param2: 参数2描述

        Returns:
            结果字典
        """
        # 实现逻辑
        return {"status": "success"}
```

2. 重启 MCP 服务器

3. AI 客户端会自动识别新工具

### 2. 添加新的存储类型

**步骤：**

1. 在 `src/data/storage/` 创建新文件：

```python
# mongodb_storage.py
from src.data.storage.base import BaseStorage

class MongoDBStorage(BaseStorage):
    """MongoDB 存储实现"""

    def save(self, data, data_type: str):
        # 实现保存逻辑
        pass

    def load(self, data_type: str):
        # 实现加载逻辑
        pass
```

2. 在 `StorageManager` 中注册：

```python
class StorageManager:
    def __init__(self, storage_type: str = "csv"):
        if storage_type == "csv":
            self.storage = CSVStorage()
        elif storage_type == "mongodb":
            self.storage = MongoDBStorage()
```

3. 在 `.env` 中配置：

```bash
STORAGE_TYPE=mongodb
MONGODB_URI=mongodb://localhost:27017
```

### 3. 添加新的数据采集类型

**步骤：**

1. 在 `src/xiaohongshu/data_collector/` 创建新采集器：

```python
# comments.py
def collect_comments_data(driver):
    """采集评论数据"""

    # 导航到评论页面
    driver.get("https://creator.xiaohongshu.com/comments")

    # 提取数据
    comments = []
    comment_elements = driver.find_elements(
        By.CSS_SELECTOR, ".comment-item"
    )

    for element in comment_elements:
        comment = {
            "用户": element.find_element(By.CSS_SELECTOR, ".user").text,
            "内容": element.find_element(By.CSS_SELECTOR, ".content").text,
            "时间": element.find_element(By.CSS_SELECTOR, ".time").text,
        }
        comments.append(comment)

    return comments
```

2. 在 `XHSClient` 中添加方法：

```python
class XHSClient:
    async def collect_comments_data(self):
        """采集评论数据"""
        from src.xiaohongshu.data_collector.comments import (
            collect_comments_data
        )

        driver = self.browser_manager.start()
        data = collect_comments_data(driver)

        # 保存数据
        self.storage_manager.save(data, "comments")

        return data
```

3. 注册为 MCP 工具：

```python
@self.mcp.tool()
def get_comments_data() -> dict:
    """获取评论数据"""
    client = XHSClient(config)
    data = await client.collect_comments_data()
    return {"data": data}
```

### 4. 添加新的功能组件

**步骤：**

1. 在 `src/xiaohongshu/components/` 创建组件：

```python
# comment_automation.py
class XHSCommentAutomation:
    """评论自动化组件"""

    def __init__(self, driver):
        self.driver = driver

    def post_comment(self, note_url: str, comment_text: str):
        """发布评论"""

        # 导航到笔记
        self.driver.get(note_url)

        # 定位评论框
        comment_box = self.driver.find_element(
            By.CSS_SELECTOR, ".comment-input"
        )

        # 输入评论
        comment_box.send_keys(comment_text)

        # 点击发布
        submit_btn = self.driver.find_element(
            By.CSS_SELECTOR, ".comment-submit"
        )
        submit_btn.click()
```

2. 在 `XHSClient` 中集成：

```python
class XHSClient:
    async def post_comment(self, note_url: str, text: str):
        """发布评论"""
        from src.xiaohongshu.components.comment_automation import (
            XHSCommentAutomation
        )

        driver = self.browser_manager.start()
        automation = XHSCommentAutomation(driver)
        automation.post_comment(note_url, text)
```

---

## 总结

### 架构优势

1. **模块化设计**
   - 职责清晰，易于维护
   - 组件可独立测试和复用

2. **可扩展性强**
   - 接口抽象，易于添加新功能
   - 存储、采集器、组件均支持插件化

3. **异步任务机制**
   - 避免 MCP 调用超时
   - 提高用户体验

4. **跨平台支持**
   - 自动检测系统环境
   - 支持本地和远程浏览器

5. **AI 友好**
   - 中文表头数据
   - 结构化 MCP 工具
   - 智能路径解析

### 技术亮点

1. **话题自动化**
   - 基于实测验证的完整实现
   - 多重备用方案确保成功率

2. **智能路径解析**
   - 支持多种输入格式
   - 自动识别本地/网络路径

3. **任务管理**
   - 异步后台执行
   - 实时状态查询

4. **数据采集**
   - 定时自动采集
   - 中文表头便于 AI 分析

### 未来展望

1. **功能扩展**
   - 评论管理
   - 私信管理
   - 数据可视化

2. **性能优化**
   - 并发发布
   - 缓存机制
   - 连接池

3. **部署优化**
   - Docker 容器化
   - Kubernetes 编排
   - CI/CD 集成

---

**文档版本**：v1.0.0
**最后更新**：2025-01-01
**维护者**：xhs-toolkit 开发团队
