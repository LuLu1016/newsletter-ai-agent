import logging
from typing import List, Optional
from datetime import datetime, timezone
import requests
from pydantic import BaseModel

from app.models.event import Event, Location, Organizer
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LumaClientException(Exception):
    """自定义异常类，用于处理API相关错误"""
    pass

class LumaClient:
    """Luma API客户端"""
    
    BASE_URL = "https://public-api.luma.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化API客户端"""
        self.api_key = api_key or settings.LUMA_API_KEY
        if not self.api_key:
            raise LumaClientException("未提供Luma API密钥")
        
        self.session = requests.Session()
        self.session.headers.update({
            "x-luma-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
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
            LumaClientException: 当API调用失败时
        """
        try:
            logger.info(f"开始获取活动数据: city={city}, category={category}")
            
            # 根据城市获取日历ID
            calendar_id = self._get_calendar_id(city)
            
            # 获取活动列表
            response = self.session.get(
                f"{self.BASE_URL}/calendars/{calendar_id}/events",
                params={
                    "filter": category,
                    "status": "upcoming"
                }
            )
            response.raise_for_status()
            
            # 解析响应
            events_data = response.json()
            logger.debug(f"API响应: {events_data}")
            
            # 转换为Event对象
            events = []
            for event_data in events_data.get("events", []):
                try:
                    event = self._convert_to_event(event_data, city, category)
                    if event:
                        events.append(event)
                except Exception as e:
                    logger.warning(f"转换活动数据时出错: {str(e)}")
                    continue
            
            logger.info(f"成功获取 {len(events)} 个活动")
            return events
            
        except requests.RequestException as e:
            error_msg = f"调用Luma API失败: {str(e)}"
            logger.error(error_msg)
            raise LumaClientException(error_msg)
        except Exception as e:
            error_msg = f"获取活动数据时出错: {str(e)}"
            logger.error(error_msg)
            raise LumaClientException(error_msg)

    def _get_calendar_id(self, city: str) -> str:
        """获取城市对应的日历ID"""
        # 城市到日历ID的映射
        city_calendars = {
            "NYC": "nyc",
            "New York": "nyc",
            "Boston": "boston",
            # 可以添加更多城市
        }
        
        calendar_id = city_calendars.get(city.strip())
        if not calendar_id:
            raise LumaClientException(f"不支持的城市: {city}")
        
        return calendar_id

    def _convert_to_event(self, event_data: dict, city: str, category: str) -> Optional[Event]:
        """将API响应数据转换为Event对象"""
        try:
            # 提取地点信息
            location_data = event_data.get("location", {})
            location = Location(
                city=city,
                venue=location_data.get("name", "TBA"),
                address=location_data.get("address")
            )
            
            # 提取组织者信息
            host_data = event_data.get("host", {})
            organizer = Organizer(
                name=host_data.get("name", "Unknown Organizer"),
                description=host_data.get("bio"),
                website=host_data.get("website")
            )
            
            # 创建Event实例
            event = Event(
                id=f"luma_{event_data['id']}",
                title=event_data["title"],
                description=event_data.get("description", "No description available"),
                start_time=datetime.fromisoformat(event_data["start_time"]).replace(tzinfo=timezone.utc),
                end_time=datetime.fromisoformat(event_data["end_time"]).replace(tzinfo=timezone.utc) if event_data.get("end_time") else None,
                location=location,
                organizer=organizer,
                url=event_data["url"],
                image_url=event_data.get("image_url"),
                category=[category],
                is_virtual=event_data.get("is_virtual", False),
                source="luma"
            )
            
            return event
            
        except Exception as e:
            logger.warning(f"转换活动数据时出错: {str(e)}")
            return None
