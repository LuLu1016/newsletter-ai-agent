import sys
import os
import logging
from datetime import datetime
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.luma_client import LumaClient, LumaClientException
from app.models.event import Event

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_luma_client():
    """测试Luma API客户端"""
    try:
        # 实例化客户端
        client = LumaClient()
        
        # 测试纽约科技活动
        logger.info("测试获取纽约科技活动:")
        test_nyc_events(client)
        
        # 测试波士顿科技活动
        logger.info("\n测试获取波士顿科技活动:")
        test_boston_events(client)
        
    except LumaClientException as e:
        logger.error(f"API错误: {str(e)}")
    except Exception as e:
        logger.error(f"未预期的错误: {str(e)}")

def test_nyc_events(client: LumaClient):
    """测试获取纽约活动"""
    events = client.get_events(city="NYC", category="Tech")
    print_events(events)

def test_boston_events(client: LumaClient):
    """测试获取波士顿活动"""
    events = client.get_events(city="Boston", category="Tech")
    print_events(events)

def print_events(events: list[Event]):
    """打印活动信息"""
    logger.info(f"获取到 {len(events)} 个活动")
    
    if events:
        # 打印第一个活动的详细信息
        first_event = events[0]
        logger.info("\n第一个活动的详细信息:")
        logger.info(f"标题: {first_event.title}")
        logger.info(f"时间: {first_event.start_time}")
        logger.info(f"地点: {first_event.location.venue}")
        logger.info(f"城市: {first_event.location.city}")
        logger.info(f"组织者: {first_event.organizer.name}")
        logger.info(f"描述: {first_event.description[:200]}...")
        logger.info(f"链接: {first_event.url}")
        logger.info(f"是否为线上活动: {first_event.is_virtual}")
        
        # 保存所有活动数据到文件（用于调试）
        with open("events_debug.json", "w", encoding="utf-8") as f:
            events_data = [
                {
                    "title": e.title,
                    "start_time": e.start_time.isoformat(),
                    "venue": e.location.venue,
                    "city": e.location.city,
                    "organizer": e.organizer.name,
                    "url": e.url,
                    "is_virtual": e.is_virtual
                }
                for e in events
            ]
            json.dump(events_data, f, indent=2, ensure_ascii=False)
        logger.info("已保存所有活动数据到events_debug.json")
    else:
        logger.warning("没有找到任何活动")

if __name__ == "__main__":
    test_luma_client()
