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
    
    BASE_URL = "https://lu.ma"
    SEARCH_URL = "https://lu.ma/search/events"
    
    def __init__(self):
        """初始化爬虫，设置请求头等"""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
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
                "filter": "upcoming"
            }
            
            # 发送请求
            response = self.session.get(
                self.SEARCH_URL,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            events = []
            
            # 查找所有活动卡片
            event_cards = soup.find_all("div", class_="event-card")
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
            # 提取基本信息
            title_elem = card.find("h2", class_="event-title")
            if not title_elem:
                return None
            
            title = title_elem.text.strip()
            description = card.find("p", class_="event-description")
            description = description.text.strip() if description else "No description available"
            
            # 提取链接
            link_elem = card.find("a", class_="event-link")
            if not link_elem:
                return None
            
            event_url = urljoin(self.BASE_URL, link_elem.get("href", ""))
            
            # 提取时间
            date_elem = card.find("time")
            if not date_elem:
                return None
            
            start_time = datetime.fromisoformat(date_elem.get("datetime", "")).replace(tzinfo=timezone.utc)
            
            # 提取地点信息
            location_elem = card.find("div", class_="event-location")
            venue = location_elem.find("span", class_="venue-name").text.strip() if location_elem else "TBA"
            address = location_elem.find("address").text.strip() if location_elem and location_elem.find("address") else None
            
            location = Location(
                city=city,
                venue=venue,
                address=address
            )
            
            # 提取组织者信息
            org_elem = card.find("div", class_="organizer-info")
            org_name = org_elem.find("span", class_="name").text.strip() if org_elem else "Unknown Organizer"
            org_desc = org_elem.find("p", class_="description").text.strip() if org_elem and org_elem.find("p", class_="description") else None
            
            organizer = Organizer(
                name=org_name,
                description=org_desc,
                website=None  # 需要访问详情页才能获取
            )
            
            # 提取图片
            image_elem = card.find("img", class_="event-image")
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
            
            return event
            
        except Exception as e:
            logger.warning(f"解析活动卡片数据时出错: {str(e)}")
            return None

    def _check_if_virtual(self, venue: str) -> bool:
        """检查是否为虚拟活动"""
        virtual_keywords = ["virtual", "online", "zoom", "remote", "webinar"]
        return any(keyword in venue.lower() for keyword in virtual_keywords)