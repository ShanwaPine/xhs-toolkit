"""
内容分析数据采集模块

从小红书创作者中心内容分析页面采集每篇笔记的详细数据，包括：
1. 基础数据：标题、发布时间、观看、点赞、评论、收藏、涨粉、分享等
2. 观众来源数据：推荐、搜索、关注、其他来源的百分比
3. 观众分析数据：性别分布、年龄分布、城市分布、兴趣分布
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .utils import (
    clean_number, wait_for_element, extract_text_safely, 
    find_element_by_selectors, wait_for_page_load, safe_click, scroll_to_element
)
from src.utils.logger import get_logger
from src.data.storage_manager import get_storage_manager

logger = get_logger(__name__)

# 内容分析页面选择器配置
CONTENT_ANALYSIS_SELECTORS = {
    # 文章列表页面选择器 - 基于Playwright调试结果更新
    'note_table': ['.note-data-table', '[class*="el-table"]', '.note-data-container table'],  # 更新为实际发现的选择器
    'note_rows': ['.note-data-table tr', 'tr', '[class*="row"]'],  # 表格行选择器
    'detail_button': '.note-detail',  # 详情数据按钮
    'data_container': '.note-data-container',  # 数据容器
    
    # 详情页面选择器
    'core_data_container': '.el-table__cell',
    'audience_source_container': '[class*="source"]',
    'audience_analysis_container': '[class*="analysis"]',
    
    # 数据提取选择器
    'number_elements': '//*[text()]',
    'percentage_elements': '//*[contains(text(), "%")]'
}

# 表格列索引映射（基于实际DOM结构，共12列）
COLUMN_MAPPING = {
    0: 'note_info',       # 笔记基础信息（包含标题、封面、发布时间）
    1: 'exposure',        # 曝光 (impCount)
    2: 'views',           # 观看 (readCount)
    3: 'cover_click_rate',# 封面点击率 (coverClickRate)
    4: 'likes',           # 点赞 (likeCount)
    5: 'comments',        # 评论 (commentCount)
    6: 'collects',        # 收藏 (favCount)
    7: 'fans_growth',     # 涨粉 (increaseFansCount)
    8: 'shares',          # 分享 (shareCount)
    9: 'avg_watch_time',  # 人均观看时长 (viewTimeAvg)
    10: 'danmu_count',    # 弹幕 (danmakuCount)
    11: 'actions'         # 操作列（包含详情数据按钮）
}


async def collect_content_analysis_data(driver: WebDriver, date: Optional[str] = None, 
                                 limit: int = 50, save_data: bool = True) -> Dict[str, Any]:
    """
    采集内容分析数据
    
    Args:
        driver: WebDriver实例
        date: 采集日期，默认当天
        limit: 最大采集笔记数量
        save_data: 是否保存数据到存储
        
    Returns:
        包含内容分析数据的字典
    """
    logger.info("📊 开始采集内容分析数据...")
    
    # 导航到内容分析页面
    content_url = "https://creator.xiaohongshu.com/statistics/data-analysis"
    try:
        driver.get(content_url)
        logger.info(f"📍 访问内容分析页面: {content_url}")
        
        # 等待页面加载
        if not wait_for_page_load(driver, timeout=30):
            logger.warning("⚠️ 页面加载超时，继续尝试采集")
        
        # 增加等待时间，确保数据完全加载
        time.sleep(10)  # 从5秒增加到10秒
        
    except Exception as e:
        logger.error(f"❌ 访问内容分析页面失败: {e}")
        return {"success": False, "error": str(e)}
    
    # 采集数据
    content_data = {
        "success": True,
        "collect_time": datetime.now().isoformat(),
        "page_url": driver.current_url,
        "notes": [],
        "summary": {}
    }
    
    try:
        # 等待表格加载 - 使用更长的等待时间
        table_element = None
        table_selectors = CONTENT_ANALYSIS_SELECTORS['note_table']
        
        for selector in table_selectors:
            table_element = wait_for_element(driver, selector, timeout=20)  # 从15秒增加到20秒
            if table_element:
                logger.info(f"✅ 找到数据表格，使用选择器: {selector}")
                break
        
        if not table_element:
            logger.warning("⚠️ 未找到数据表格，尝试直接查找笔记行")
            # 尝试直接查找笔记行
            note_rows = driver.find_elements(By.CSS_SELECTOR, '.el-table__row')
            if not note_rows:
                note_rows = driver.find_elements(By.CSS_SELECTOR, 'tr')
            if not note_rows:
                logger.error("❌ 未找到任何数据行")
                return {"success": False, "error": "未找到数据表格或数据行"}
            else:
                logger.info(f"✅ 直接找到 {len(note_rows)} 个数据行")
        
        # 逐页采集笔记列表数据和详情数据
        # 避免分页后元素引用失效的问题
        enhanced_notes_data = _collect_notes_with_details_paginated(driver, limit)

        content_data["notes"] = enhanced_notes_data
        
        # 生成汇总信息
        content_data["summary"] = _generate_summary(enhanced_notes_data)
        
        logger.info(f"✅ 内容分析数据采集完成，共采集 {len(enhanced_notes_data)} 篇笔记")
        
        # 保存数据到存储
        if save_data and enhanced_notes_data:
            try:
                # 格式化数据用于存储
                formatted_notes = _format_notes_for_storage(enhanced_notes_data)
                storage_manager = get_storage_manager()
                storage_manager.save_content_analysis_data(formatted_notes)
                logger.info("💾 内容分析数据已保存到存储")
            except Exception as e:
                logger.error(f"❌ 保存内容分析数据时出错: {e}")
        
    except Exception as e:
        logger.error(f"❌ 采集内容分析数据时出错: {e}")
        content_data["success"] = False
        content_data["error"] = str(e)
    
    return content_data


def _get_total_pages(driver: WebDriver) -> int:
    """
    获取分页组件的总页数

    DOM结构：
    <div class="d-pagination">
      <div class="d-pagination-page">上一页箭头</div>
      <div class="d-pagination-page --color-bg-primary-light">1</div>
      <div class="d-pagination-page">2</div>
      ...
    </div>

    Returns:
        总页数，如果获取失败返回1（至少有一页）
    """
    try:
        # 等待分页组件加载
        pagination_container = wait_for_element(driver, '.d-pagination', timeout=5)
        if not pagination_container:
            logger.info("未找到分页组件，可能只有一页数据")
            return 1

        # 查找所有分页页码元素
        page_elements = driver.find_elements(By.CSS_SELECTOR, '.d-pagination .d-pagination-page')

        if not page_elements:
            return 1

        # 过滤出数字页码（排除上一页/下一页箭头）
        page_numbers = []
        for elem in page_elements:
            try:
                text = extract_text_safely(elem).strip()
                # 检查是否为纯数字
                if text and text.isdigit():
                    page_numbers.append(int(text))
            except:
                continue

        if page_numbers:
            total_pages = max(page_numbers)
            logger.info(f"📄 检测到分页，共 {total_pages} 页")
            return total_pages

        return 1

    except Exception as e:
        logger.warning(f"⚠️ 获取总页数失败: {e}")
        return 1


def _get_current_page(driver: WebDriver) -> int:
    """
    获取当前页码

    当前页的样式类包含 '--color-bg-primary-light' 或 '--color-primary'

    Returns:
        当前页码，如果获取失败返回1
    """
    try:
        # 查找当前激活的页码（通过样式类判断）
        current_page_selectors = [
            '.d-pagination-page.--color-bg-primary-light',
            '.d-pagination-page.--color-primary',
            '.d-pagination-page[class*="primary"]',
            '.d-pagination-page[class*="active"]',
        ]

        for selector in current_page_selectors:
            try:
                current_elem = driver.find_element(By.CSS_SELECTOR, selector)
                if current_elem:
                    text = extract_text_safely(current_elem).strip()
                    if text and text.isdigit():
                        return int(text)
            except:
                continue

        return 1

    except Exception as e:
        logger.debug(f"获取当前页码失败: {e}")
        return 1


def _go_to_next_page(driver: WebDriver) -> bool:
    """
    跳转到下一页

    策略：
    1. 首先尝试点击下一页箭头
    2. 如果失败，尝试点击下一个页码数字

    Returns:
        是否成功跳转
    """
    try:
        current_page = _get_current_page(driver)
        target_page = current_page + 1

        logger.info(f"📄 尝试从第 {current_page} 页跳转到第 {target_page} 页")

        # 查找所有分页元素
        page_elements = driver.find_elements(By.CSS_SELECTOR, '.d-pagination .d-pagination-page')
        if not page_elements:
            logger.warning("未找到分页元素")
            return False

        # 方法1：点击下一页箭头（通常是最后一个分页元素）
        next_arrow = page_elements[-1]
        next_arrow_text = extract_text_safely(next_arrow).strip()

        # 确认不是页码数字（是箭头或图标）
        if not next_arrow_text.isdigit():
            try:
                scroll_to_element(driver, next_arrow)
                if safe_click(next_arrow):
                    time.sleep(2)  # 等待页面数据刷新

                    # 验证是否成功跳转
                    new_page = _get_current_page(driver)
                    if new_page == target_page:
                        logger.info(f"✅ 成功跳转到第 {target_page} 页")
                        return True
            except Exception as e:
                logger.debug(f"点击下一页箭头失败: {e}")

        # 方法2：直接点击目标页码
        for elem in page_elements:
            try:
                text = extract_text_safely(elem).strip()
                if text == str(target_page):
                    scroll_to_element(driver, elem)
                    if safe_click(elem):
                        time.sleep(2)  # 等待页面数据刷新

                        # 验证是否成功跳转
                        new_page = _get_current_page(driver)
                        if new_page == target_page:
                            logger.info(f"✅ 成功跳转到第 {target_page} 页")
                            return True
            except:
                continue

        logger.warning(f"⚠️ 无法跳转到第 {target_page} 页")
        return False

    except Exception as e:
        logger.error(f"❌ 跳转下一页失败: {e}")
        return False


def _wait_for_table_data_refresh(driver: WebDriver, timeout: int = 10) -> bool:
    """
    等待表格数据刷新完成

    Returns:
        是否刷新成功
    """
    try:
        # 等待表格加载完成
        time.sleep(1)  # 短暂等待，让旧数据消失

        # 等待新的表格行出现
        row_selectors = CONTENT_ANALYSIS_SELECTORS['note_rows']
        for selector in row_selectors:
            rows = wait_for_element(driver, selector, timeout=timeout)
            if rows:
                logger.debug("表格数据刷新完成")
                return True

        return False

    except Exception as e:
        logger.debug(f"等待表格刷新失败: {e}")
        return False


def _collect_current_page_notes(driver: WebDriver) -> List[Dict[str, Any]]:
    """
    采集当前页面的笔记数据

    Returns:
        当前页面的笔记数据列表
    """
    notes_data = []

    try:
        # 使用选择器查找所有笔记行
        note_rows = []
        row_selectors = CONTENT_ANALYSIS_SELECTORS['note_rows']

        for selector in row_selectors:
            note_rows = driver.find_elements(By.CSS_SELECTOR, selector)
            if note_rows:
                logger.debug(f"使用选择器 {selector} 找到 {len(note_rows)} 行笔记数据")
                break

        if not note_rows:
            logger.warning("⚠️ 当前页未找到任何笔记行")
            return notes_data

        # 过滤掉表头行
        header_keywords = ['笔记基础信息', '曝光', '观看', '点赞', '评论', '收藏', '涨粉', '分享', '操作']
        filtered_rows = []

        for row in note_rows:
            try:
                row_text = row.text.strip()
                # 检查是否为表头行
                is_header = any(keyword in row_text for keyword in header_keywords)
                if not is_header and row_text:  # 不是表头且有内容
                    filtered_rows.append(row)
            except:
                continue

        logger.debug(f"过滤后剩余 {len(filtered_rows)} 行有效数据")

        # 提取每行数据
        for i, row in enumerate(filtered_rows):
            try:
                note_data = _extract_note_data_from_row(row, i)
                if note_data:
                    notes_data.append(note_data)
                    logger.debug(f"📝 笔记: {note_data.get('title', 'Unknown')[:20]}...")

            except Exception as e:
                logger.warning(f"⚠️ 处理笔记行 {i} 时出错: {e}")
                continue

    except Exception as e:
        logger.warning(f"⚠️ 采集当前页笔记数据时出错: {e}")

    return notes_data


def _collect_notes_with_details_paginated(driver: WebDriver, limit: int) -> List[Dict[str, Any]]:
    """
    逐页采集笔记列表数据和详情数据

    每采集完一页的列表数据后，立即采集该页笔记的详情数据，
    然后再跳转到下一页。这样可以避免分页后元素引用失效的问题。

    Args:
        driver: WebDriver实例
        limit: 最大采集笔记数量

    Returns:
        包含详情数据的笔记列表
    """
    all_notes_data = []

    try:
        # 获取总页数
        total_pages = _get_total_pages(driver)
        logger.info(f"📋 开始逐页采集笔记（含详情），共 {total_pages} 页，限制 {limit} 条")

        current_page = 1

        while current_page <= total_pages and len(all_notes_data) < limit:
            logger.info(f"📄 正在采集第 {current_page}/{total_pages} 页...")

            # 采集当前页面的笔记列表数据
            page_notes = _collect_current_page_notes(driver)

            if page_notes:
                # 计算还需要采集多少条
                remaining = limit - len(all_notes_data)
                page_notes = page_notes[:remaining]

                logger.info(f"✅ 第 {current_page} 页采集到 {len(page_notes)} 条笔记基础数据")

                # 立即采集当前页笔记的详情数据
                enhanced_page_notes = _enhance_notes_with_detail_data(driver, page_notes)
                all_notes_data.extend(enhanced_page_notes)

                logger.info(f"✅ 第 {current_page} 页详情采集完成，累计 {len(all_notes_data)} 条")
            else:
                logger.warning(f"⚠️ 第 {current_page} 页未采集到数据")

            # 检查是否需要继续采集下一页
            if len(all_notes_data) >= limit:
                logger.info(f"📊 已达到采集上限 {limit} 条")
                break

            if current_page < total_pages:
                # 跳转到下一页
                if _go_to_next_page(driver):
                    # 等待数据刷新
                    _wait_for_table_data_refresh(driver)
                    current_page += 1
                else:
                    logger.warning("⚠️ 无法跳转到下一页，停止采集")
                    break
            else:
                # 已经是最后一页
                break

        logger.info(f"📊 笔记采集完成，共 {len(all_notes_data)} 条（含详情数据）")

    except Exception as e:
        logger.error(f"❌ 采集笔记数据时出错: {e}")

    return all_notes_data


def _collect_notes_list_data(driver: WebDriver, limit: int) -> List[Dict[str, Any]]:
    """
    采集笔记列表数据（支持分页，不含详情）

    Args:
        driver: WebDriver实例
        limit: 最大采集笔记数量

    Returns:
        笔记数据列表
    """
    all_notes_data = []

    try:
        # 获取总页数
        total_pages = _get_total_pages(driver)
        logger.info(f"📋 开始采集笔记列表，共 {total_pages} 页，限制 {limit} 条")

        current_page = 1

        while current_page <= total_pages and len(all_notes_data) < limit:
            logger.info(f"📄 正在采集第 {current_page}/{total_pages} 页...")

            # 采集当前页面数据
            page_notes = _collect_current_page_notes(driver)

            if page_notes:
                # 计算还需要采集多少条
                remaining = limit - len(all_notes_data)
                # 只取需要的数量
                page_notes = page_notes[:remaining]
                all_notes_data.extend(page_notes)
                logger.info(f"✅ 第 {current_page} 页采集到 {len(page_notes)} 条笔记，累计 {len(all_notes_data)} 条")
            else:
                logger.warning(f"⚠️ 第 {current_page} 页未采集到数据")

            # 检查是否需要继续采集下一页
            if len(all_notes_data) >= limit:
                logger.info(f"📊 已达到采集上限 {limit} 条")
                break

            if current_page < total_pages:
                # 跳转到下一页
                if _go_to_next_page(driver):
                    # 等待数据刷新
                    _wait_for_table_data_refresh(driver)
                    current_page += 1
                else:
                    logger.warning("⚠️ 无法跳转到下一页，停止采集")
                    break
            else:
                # 已经是最后一页
                break

        logger.info(f"📊 笔记列表采集完成，共 {len(all_notes_data)} 条")

    except Exception as e:
        logger.error(f"❌ 采集笔记列表数据时出错: {e}")

    return all_notes_data


def _extract_note_info_from_cell(cell) -> Dict[str, str]:
    """
    从笔记基础信息单元格中提取标题和发布时间

    DOM结构：
    <div class="note-info-column">
      <div class="note-cover"><img src="..."></div>
      <div class="note-info-content">
        <div class="note-header">
          <span class="note-title">标题文本</span>
        </div>
        <div class="time">发布于2025-12-31 12:50</div>
      </div>
    </div>
    """
    result = {'title': '', 'publish_time': ''}

    try:
        # 尝试使用精确选择器提取标题
        title_selectors = ['.note-title', '.note-header span', '.note-info-content .note-header']
        for selector in title_selectors:
            try:
                title_elem = cell.find_element(By.CSS_SELECTOR, selector)
                if title_elem:
                    title_text = extract_text_safely(title_elem)
                    if title_text:
                        result['title'] = title_text.strip()
                        break
            except:
                continue

        # 尝试使用精确选择器提取发布时间
        time_selectors = ['.time', '.publish-time', '.note-info-content .time']
        for selector in time_selectors:
            try:
                time_elem = cell.find_element(By.CSS_SELECTOR, selector)
                if time_elem:
                    time_text = extract_text_safely(time_elem)
                    if time_text:
                        # 清理"发布于"前缀
                        if time_text.startswith('发布于'):
                            time_text = time_text[3:]
                        result['publish_time'] = time_text.strip()
                        break
            except:
                continue

        # 备用方案：从整个单元格文本解析
        if not result['title']:
            cell_text = extract_text_safely(cell)
            if cell_text:
                if '发布于' in cell_text:
                    parts = cell_text.split('发布于')
                    result['title'] = parts[0].strip()
                    if len(parts) > 1:
                        result['publish_time'] = parts[1].strip()
                else:
                    result['title'] = cell_text.strip()

    except Exception as e:
        logger.debug(f"提取笔记基础信息失败: {e}")

    return result


def _find_detail_button(cell):
    """
    在操作列单元格中查找详情按钮

    DOM结构：
    <td class="d-table__cell--fixed-right">
      <div class="d-table__cell">
        <span class="note-detail">详情数据</span>
      </div>
    </td>

    Returns:
        找到的详情按钮元素，如果未找到返回None
    """
    # 按优先级尝试不同的选择器
    detail_button_selectors = [
        '.note-detail',                    # 主要选择器
        'span.note-detail',                # 更精确的选择器
        '[class*="note-detail"]',          # 模糊匹配
        '[class*="detail"]',               # 更宽泛的匹配
    ]

    for selector in detail_button_selectors:
        try:
            detail_button = cell.find_element(By.CSS_SELECTOR, selector)
            if detail_button and detail_button.is_displayed():
                logger.debug(f"找到详情按钮，使用选择器: {selector}")
                return detail_button
        except:
            continue

    # 备用方案：使用XPath按文本查找
    try:
        detail_button = cell.find_element(By.XPATH, ".//*[contains(text(), '详情')]")
        if detail_button and detail_button.is_displayed():
            logger.debug("找到详情按钮，使用XPath文本匹配")
            return detail_button
    except:
        pass

    return None


def _extract_note_data_from_row(row, row_index: int) -> Optional[Dict[str, Any]]:
    """从表格行中提取笔记数据（基于实际DOM结构，共12列）"""
    try:
        # 查找行中的所有单元格
        cell_selectors = ['td', '.d-table__cell', '.el-table__cell', '[class*="cell"]']
        cells = []

        for selector in cell_selectors:
            cells = row.find_elements(By.CSS_SELECTOR, selector)
            if cells:
                logger.debug(f"使用选择器 {selector} 找到 {len(cells)} 个单元格")
                break

        if len(cells) < 3:  # 至少需要几列数据
            logger.warning(f"⚠️ 行 {row_index} 单元格数量不足: {len(cells)}")
            return None

        note_data = {
            "row_index": row_index,
            "extract_time": datetime.now().isoformat()
        }

        # 按列索引提取数据
        for col_index, cell in enumerate(cells):
            try:
                field_name = COLUMN_MAPPING.get(col_index, f"column_{col_index}")

                if field_name == 'note_info':
                    # 第一列：笔记基础信息，需要特殊处理
                    note_info = _extract_note_info_from_cell(cell)
                    note_data['title'] = note_info.get('title', '')
                    note_data['publish_time'] = note_info.get('publish_time', '')

                elif field_name == 'actions':
                    # 操作列：查找详情数据按钮
                    detail_button = _find_detail_button(cell)
                    if detail_button:
                        note_data['has_detail_button'] = True
                        note_data['detail_button_element'] = detail_button
                    else:
                        note_data['has_detail_button'] = False
                        logger.debug(f"⚠️ 行 {row_index} 未找到详情按钮")

                elif field_name in ['exposure', 'views', 'likes', 'comments',
                                    'collects', 'fans_growth', 'shares', 'danmu_count']:
                    # 数值列，清理并转换为整数
                    cell_text = extract_text_safely(cell)
                    if cell_text:
                        cleaned_value = clean_number(cell_text)
                        note_data[field_name] = cleaned_value

                elif field_name == 'cover_click_rate':
                    # 封面点击率，保持百分比格式
                    cell_text = extract_text_safely(cell)
                    note_data[field_name] = cell_text.strip() if cell_text else '0%'

                elif field_name == 'avg_watch_time':
                    # 时长列，保持原始格式
                    cell_text = extract_text_safely(cell)
                    note_data[field_name] = cell_text.strip() if cell_text else ''

            except Exception as e:
                logger.debug(f"处理列 {col_index} 时出错: {e}")
                continue

        return note_data if note_data.get('title') else None

    except Exception as e:
        logger.warning(f"⚠️ 提取行数据时出错: {e}")
        return None


def _enhance_notes_with_detail_data(driver: WebDriver, notes_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    为每篇笔记采集详细数据

    注意：此函数只处理当前页面的笔记，每次采集详情后需要重新获取笔记列表元素
    """
    enhanced_notes = []
    original_window = driver.current_window_handle

    for i, note in enumerate(notes_data):
        try:
            logger.info(f"📊 采集笔记 {i+1}/{len(notes_data)} 的详细数据: {note.get('title', 'Unknown')}")

            # 重新获取详情按钮（因为页面可能已刷新）
            detail_button = _find_detail_button_by_title(driver, note.get('title', ''))

            if detail_button:
                # 记录当前窗口数量
                original_windows = set(driver.window_handles)

                # 滚动到按钮可见，留出足够空间避免被固定表头遮挡
                driver.execute_script("""
                    arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});
                """, detail_button)
                time.sleep(0.5)

                # 使用 JavaScript 点击，避免被固定表头遮挡导致的 click intercepted 错误
                try:
                    driver.execute_script("arguments[0].click();", detail_button)
                    logger.info(f"✅ 成功点击详情数据按钮")
                except Exception as click_error:
                    logger.warning(f"JavaScript点击失败，尝试普通点击: {click_error}")
                    detail_button.click()

                # 等待并检查是否有新tab打开
                time.sleep(2)
                new_windows = set(driver.window_handles) - original_windows

                if new_windows:
                    # 详情页在新tab中打开
                    new_window = new_windows.pop()
                    driver.switch_to.window(new_window)
                    logger.debug("切换到详情页新tab")
                    time.sleep(2)

                    # 采集详情页面数据
                    detail_data = _collect_detail_page_data(driver)

                    # 关闭新tab并切回原窗口
                    driver.close()
                    driver.switch_to.window(original_window)
                    logger.debug("关闭详情页tab，返回列表页")
                    time.sleep(1)
                else:
                    # 详情页在同一窗口打开（页面跳转）
                    time.sleep(2)
                    detail_data = _collect_detail_page_data(driver)
                    _return_to_list_page(driver)

                # 合并数据
                enhanced_note = {**note, **detail_data}
                # 移除元素引用，避免序列化问题
                enhanced_note.pop('detail_button_element', None)
                enhanced_notes.append(enhanced_note)

            else:
                logger.warning(f"⚠️ 笔记 {note.get('title')} 找不到详情按钮")
                note_copy = {k: v for k, v in note.items() if k != 'detail_button_element'}
                enhanced_notes.append(note_copy)

        except Exception as e:
            logger.error(f"❌ 采集笔记详细数据时出错: {e}")
            note_copy = {k: v for k, v in note.items() if k != 'detail_button_element'}
            enhanced_notes.append(note_copy)

            # 确保回到正确的窗口
            try:
                if driver.current_window_handle != original_window:
                    driver.close()
                    driver.switch_to.window(original_window)
            except:
                pass

    return enhanced_notes


def _find_detail_button_by_title(driver: WebDriver, title: str):
    """
    根据笔记标题在当前页面重新查找详情按钮

    解决 stale element reference 问题
    """
    if not title:
        return None

    try:
        # 查找所有笔记行
        rows = driver.find_elements(By.CSS_SELECTOR, 'tr')

        for row in rows:
            try:
                row_text = row.text
                # 检查这行是否包含目标标题
                if title in row_text:
                    # 在这行中查找详情按钮
                    detail_selectors = ['.note-detail', 'span.note-detail', '[class*="note-detail"]']
                    for selector in detail_selectors:
                        try:
                            detail_btn = row.find_element(By.CSS_SELECTOR, selector)
                            if detail_btn and detail_btn.is_displayed():
                                return detail_btn
                        except:
                            continue

                    # 备用：XPath查找
                    try:
                        detail_btn = row.find_element(By.XPATH, ".//*[contains(text(), '详情')]")
                        if detail_btn and detail_btn.is_displayed():
                            return detail_btn
                    except:
                        pass
            except:
                continue

        return None

    except Exception as e:
        logger.debug(f"根据标题查找详情按钮失败: {e}")
        return None


def _collect_detail_page_data(driver: WebDriver) -> Dict[str, Any]:
    """采集详情页面数据"""
    detail_data = {
        # 观众来源数据
        "source_recommend": "0%",
        "source_search": "0%", 
        "source_follow": "0%",
        "source_other": "0%",
        # 观众分析数据
        "gender_male": "0%",
        "gender_female": "0%",
        "age_18_24": "0%",
        "age_25_34": "0%",
        "age_35_44": "0%",
        "age_45_plus": "0%",
        "city_top1": "",
        "city_top2": "",
        "city_top3": "",
        "interest_top1": "",
        "interest_top2": "",
        "interest_top3": ""
    }
    
    try:
        # 等待页面加载
        time.sleep(3)
        
        # 采集观众来源数据
        source_data = _collect_audience_source_data(driver)
        detail_data.update(source_data)
        
        # 采集观众分析数据
        analysis_data = _collect_audience_analysis_data(driver)
        detail_data.update(analysis_data)
        
        logger.info("✅ 详情页面数据采集完成")
        
    except Exception as e:
        logger.error(f"❌ 采集详情页面数据时出错: {e}")
    
    return detail_data


def _collect_audience_source_data(driver: WebDriver) -> Dict[str, Any]:
    """采集观众来源数据"""
    source_data = {
        "source_recommend": "0%",
        "source_search": "0%",
        "source_follow": "0%",
        "source_other": "0%"
    }
    
    try:
        # 查找包含百分比的元素
        elements = driver.find_elements(By.XPATH, "//*[contains(text(), '%')]")
        
        for elem in elements:
            try:
                text = elem.text.strip()
                if "%" in text and text.replace('%', '').replace('.', '').isdigit():
                    # 获取上下文
                    parent = elem.find_element(By.XPATH, "..")
                    context = parent.text.strip()
                    
                    # 根据上下文判断来源类型
                    if "推荐" in context or "首页" in context:
                        source_data["source_recommend"] = text
                    elif "搜索" in context:
                        source_data["source_search"] = text
                    elif "关注" in context or "个人主页" in context:
                        source_data["source_follow"] = text
                    elif "其他" in context:
                        source_data["source_other"] = text
                        
            except Exception as e:
                continue
        
        logger.info(f"观众来源数据: {source_data}")
        
    except Exception as e:
        logger.warning(f"⚠️ 采集观众来源数据失败: {e}")
    
    return source_data


def _collect_audience_analysis_data(driver: WebDriver) -> Dict[str, Any]:
    """采集观众分析数据"""
    analysis_data = {
        "gender_male": "0%",
        "gender_female": "0%",
        "age_18_24": "0%",
        "age_25_34": "0%",
        "age_35_44": "0%",
        "age_45_plus": "0%",
        "city_top1": "",
        "city_top2": "",
        "city_top3": "",
        "interest_top1": "",
        "interest_top2": "",
        "interest_top3": ""
    }
    
    try:
        # 滚动页面查找观众分析区域
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # 查找性别分布
        gender_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '男性') or contains(text(), '女性')]")
        for elem in gender_elements:
            try:
                text = elem.text.strip()
                if "男性" in text and "%" in text:
                    percentage = text.split("男性")[-1].strip()
                    if "%" in percentage:
                        analysis_data["gender_male"] = percentage
                elif "女性" in text and "%" in text:
                    percentage = text.split("女性")[-1].strip()
                    if "%" in percentage:
                        analysis_data["gender_female"] = percentage
            except:
                continue
        
        # 查找年龄分布
        age_keywords = {
            "18-24": "age_18_24",
            "25-34": "age_25_34", 
            "35-44": "age_35_44",
            "45": "age_45_plus"
        }
        
        for age_range, field_name in age_keywords.items():
            try:
                age_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{age_range}')]")
                for elem in age_elements:
                    text = elem.text.strip()
                    if "%" in text:
                        # 提取百分比
                        percentage = text.split(age_range)[-1].strip()
                        if "%" in percentage:
                            analysis_data[field_name] = percentage
                        break
            except:
                continue
        
        # 查找城市分布（前3名）
        city_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '省') or contains(text(), '市')]")
        city_count = 0
        for elem in city_elements:
            try:
                text = elem.text.strip()
                if ("省" in text or "市" in text) and len(text) < 20:
                    if city_count == 0:
                        analysis_data["city_top1"] = text
                    elif city_count == 1:
                        analysis_data["city_top2"] = text
                    elif city_count == 2:
                        analysis_data["city_top3"] = text
                        break
                    city_count += 1
            except:
                continue
        
        logger.info(f"观众分析数据: {analysis_data}")
        
    except Exception as e:
        logger.warning(f"⚠️ 采集观众分析数据失败: {e}")
    
    return analysis_data


def _return_to_list_page(driver: WebDriver) -> None:
    """返回到列表页面"""
    try:
        # 尝试多种返回方法
        # 方法1：浏览器后退
        driver.back()
        time.sleep(3)
        
        # 检查是否成功返回
        if "data-analysis" in driver.current_url:
            logger.info("✅ 成功返回列表页面")
            return
        
        # 方法2：直接导航到列表页面
        driver.get("https://creator.xiaohongshu.com/statistics/data-analysis")
        time.sleep(3)
        logger.info("✅ 重新导航到列表页面")
        
    except Exception as e:
        logger.warning(f"⚠️ 返回列表页面失败: {e}")


def _format_notes_for_storage(notes_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """格式化笔记数据用于存储"""
    formatted_notes = []
    
    for note in notes_data:
        try:
            # 提取基础字段
            def get_field_value(field_name: str, default: Any = 0) -> Any:
                value = note.get(field_name, default)
                if isinstance(value, str) and value.isdigit():
                    return int(value)
                return value
            
            formatted_note = {
                "timestamp": note.get("extract_time", datetime.now().isoformat()),
                "title": note.get("title", ""),
                "note_type": "图文",  # 默认类型，后续可以根据内容判断
                "publish_time": note.get("publish_time", ""),
                # 新增字段
                "exposure": get_field_value("exposure"),
                "cover_click_rate": note.get("cover_click_rate", "0%"),
                # 原有字段
                "views": get_field_value("views"),
                "likes": get_field_value("likes"),
                "comments": get_field_value("comments"),
                "collects": get_field_value("collects"),
                "shares": get_field_value("shares"),
                "fans_growth": get_field_value("fans_growth"),
                "avg_watch_time": note.get("avg_watch_time", ""),
                "danmu_count": get_field_value("danmu_count"),
                # 观众来源数据
                "source_recommend": note.get("source_recommend", "0%"),
                "source_search": note.get("source_search", "0%"),
                "source_follow": note.get("source_follow", "0%"),
                "source_other": note.get("source_other", "0%"),
                # 观众分析数据
                "gender_male": note.get("gender_male", "0%"),
                "gender_female": note.get("gender_female", "0%"),
                "age_18_24": note.get("age_18_24", "0%"),
                "age_25_34": note.get("age_25_34", "0%"),
                "age_35_44": note.get("age_35_44", "0%"),
                "age_45_plus": note.get("age_45_plus", "0%"),
                "city_top1": note.get("city_top1", ""),
                "city_top2": note.get("city_top2", ""),
                "city_top3": note.get("city_top3", ""),
                "interest_top1": note.get("interest_top1", ""),
                "interest_top2": note.get("interest_top2", ""),
                "interest_top3": note.get("interest_top3", "")
            }
            
            formatted_notes.append(formatted_note)
            
        except Exception as e:
            logger.warning(f"⚠️ 格式化笔记数据时出错: {e}")
            continue
    
    return formatted_notes


def _generate_summary(notes_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """生成数据汇总信息"""
    if not notes_data:
        return {}
    
    try:
        total_views = sum(note.get("views", 0) for note in notes_data)
        total_likes = sum(note.get("likes", 0) for note in notes_data)
        total_comments = sum(note.get("comments", 0) for note in notes_data)
        total_collects = sum(note.get("collects", 0) for note in notes_data)
        total_shares = sum(note.get("shares", 0) for note in notes_data)
        
        return {
            "total_notes": len(notes_data),
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_collects": total_collects,
            "total_shares": total_shares,
            "avg_views_per_note": total_views // len(notes_data) if notes_data else 0,
            "avg_likes_per_note": total_likes // len(notes_data) if notes_data else 0
        }
        
    except Exception as e:
        logger.warning(f"⚠️ 生成汇总信息时出错: {e}")
        return {} 