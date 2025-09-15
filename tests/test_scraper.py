import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.luma_scraper import LumaScraper, LumaScraperException
from app.models.event import Event

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_luma_scraper():
    """测试Luma爬虫"""
    try:
        # 实例化爬虫
        scraper = LumaScraper()
        
        # 设置搜索参数
        city = "new york"
        category = "tech"
        
        logger.info(f"开始测试爬虫: city={city}, category={category}")
        
        # 获取活动
        events = scraper.get_events(city, category)
        
        # 打印结果
        logger.info(f"成功获取 {len(events)} 个活动")
        
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
        else:
            logger.warning("没有找到任何活动")
            
    except LumaScraperException as e:
        logger.error(f"爬虫错误: {str(e)}")
    except Exception as e:
        logger.error(f"未预期的错误: {str(e)}")

if __name__ == "__main__":
    test_luma_scraper()
