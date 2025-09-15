import logging
from typing import List, Optional
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

from app.models.event import Event, Location, Organizer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LumaScraperException(Exception):
    """自定义异常类，用于处理爬虫相关错误"""
    pass

class LumaScraper:
    """Luma活动爬虫服务"""
    
    BASE_URL = "https://lu.ma"  # 修正域名
    SEARCH_URL = "https://lu.ma/search/events"  # 修正搜索URL
    
    def __init__(self):
        """初始化爬虫，设置请求头等"""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://lu.ma/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
        })

    def get_events(self, city: str, category: str) -> List[Event]:
        """
        获取指定城市和类别的活动列表
        
        Args:
            city: 城市名称 (e.g., "NYC", "Boston")
            category: 活动类别 (e.g., "Tech", "Web3")
            
        Returns:
            List[Event]: 活动列表
            
        Raises:
            LumaScraperException: 当爬取或解析过程中出现错误时
        """
        try:
            logger.info(f"开始获取活动数据: city={city}, category={category}")
            
            # 构建搜索参数
            params = {
                "q": f"{category} in {city}",
                "type": "events",
                "sort": "upcoming"
            }
            
            # 发送请求
            response = self.session.get(
                self.SEARCH_URL,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            # 打印响应内容以便调试
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response URL: {response.url}")
            logger.debug(f"Response content length: {len(response.text)}")
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            events = []
            
            # 查找所有活动卡片（更新选择器）
            event_cards = soup.find_all("div", {"data-testid": "event-card"}) or \
                         soup.find_all("div", class_=lambda x: x and "event-card" in x.lower())
            
            logger.info(f"找到 {len(event_cards)} 个活动卡片")
            
            for card in event_cards:
                try:
                    event = self._parse_event_card(card, city, category)
                    if event:
                        events.append(event)
                except Exception as e:
                    logger.warning(f"解析活动卡片时出错: {str(e)}")
                    continue
            
            logger.info(f"成功解析 {len(events)} 个活动")
            return events
            
        except requests.RequestException as e:
            error_msg = f"请求Luma网站失败: {str(e)}"
            logger.error(error_msg)
            raise LumaScraperException(error_msg)
        except Exception as e:
            error_msg = f"获取活动数据时出错: {str(e)}"
            logger.error(error_msg)
            raise LumaScraperException(error_msg)

    def _parse_event_card(self, card: BeautifulSoup, city: str, category: str) -> Optional[Event]:
        """解析单个活动卡片"""
        try:
            # 打印卡片HTML以便调试
            logger.debug(f"Card HTML: {card.prettify()}")
            
            # 提取基本信息（更新选择器）
            title_elem = card.find("h3") or card.find("h2") or card.find(class_=lambda x: x and "title" in x.lower())
            if not title_elem:
                logger.debug("未找到标题元素")
                return None
            
            title = title_elem.text.strip()
            description = card.find("p") or card.find(class_=lambda x: x and "description" in x.lower())
            description = description.text.strip() if description else "No description available"
            
            # 提取链接
            link_elem = card.find("a")
            if not link_elem:
                logger.debug("未找到链接元素")
                return None
            
            event_url = urljoin(self.BASE_URL, link_elem.get("href", ""))
            
            # 提取时间（更新选择器）
            date_elem = card.find("time") or card.find(class_=lambda x: x and "date" in x.lower())
            if not date_elem:
                logger.debug("未找到时间元素")
                return None
            
            # 尝试不同的日期属性
            date_str = date_elem.get("datetime") or date_elem.get("data-date") or date_elem.text.strip()
            try:
                start_time = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
            except ValueError:
                logger.warning(f"无法解析日期: {date_str}")
                start_time = datetime.now(timezone.utc)  # 使用当前时间作为后备
            
            # 提取地点信息（更新选择器）
            location_elem = card.find(class_=lambda x: x and "location" in x.lower())
            venue = "TBA"
            address = None
            
            if location_elem:
                venue_elem = location_elem.find(class_=lambda x: x and "venue" in x.lower())
                venue = venue_elem.text.strip() if venue_elem else location_elem.text.strip()
                address_elem = location_elem.find("address")
                address = address_elem.text.strip() if address_elem else None
            
            location = Location(
                city=city,
                venue=venue,
                address=address
            )
            
            # 提取组织者信息（更新选择器）
            org_elem = card.find(class_=lambda x: x and "organizer" in x.lower())
            org_name = "Unknown Organizer"
            org_desc = None
            
            if org_elem:
                name_elem = org_elem.find(class_=lambda x: x and "name" in x.lower())
                org_name = name_elem.text.strip() if name_elem else org_elem.text.strip()
                desc_elem = org_elem.find(class_=lambda x: x and "description" in x.lower())
                org_desc = desc_elem.text.strip() if desc_elem else None
            
            organizer = Organizer(
                name=org_name,
                description=org_desc,
                website=None
            )
            
            # 提取图片（更新选择器）
            image_elem = card.find("img")
            image_url = image_elem.get("src") if image_elem else None
            
            # 创建Event实例
            event = Event(
                id=f"luma_{event_url.split('/')[-1]}",
                title=title,
                description=description,
                start_time=start_time,
                location=location,
                organizer=organizer,
                url=event_url,
                image_url=image_url,
                category=[category],
                is_virtual=self._check_if_virtual(venue),
                source="luma"
            )
            
            logger.debug(f"成功解析活动: {title}")
            return event
            
        except Exception as e:
            logger.warning(f"解析活动卡片数据时出错: {str(e)}")
            return None

    def _check_if_virtual(self, venue: str) -> bool:
        """检查是否为虚拟活动"""
        virtual_keywords = ["virtual", "online", "zoom", "remote", "webinar"]
        return any(keyword in venue.lower() for keyword in virtual_keywords)