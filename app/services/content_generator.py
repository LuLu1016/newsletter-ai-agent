import logging
from typing import List
from datetime import datetime
import os
from openai import OpenAI
from pydantic import BaseModel

from app.models.event import Event

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentGenerationException(Exception):
    """自定义异常类，用于处理内容生成相关错误"""
    pass

class ContentFormat(BaseModel):
    """内容格式配置"""
    email: str = "email"
    linkedin: str = "linkedin"

class ContentGenerator:
    """AI驱动的通讯内容生成服务"""
    
    def __init__(self):
        """初始化OpenAI客户端"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 系统提示词
        self.system_prompt = """You are an expert newsletter writer for startup founders and VCs, specializing in tech and investment events in the US East Coast. Your writing style is professional, concise, and insightful, similar to top-tier VC newsletters like a16z and Bessemer Venture Partners.

Key Requirements:
1. Tone: Professional, concise, insightful. Avoid overly promotional language.
2. Audience: Tech startup founders and investors - smart, busy professionals.
3. Style: Data-driven insights, clear value propositions, actionable takeaways.

Format Requirements:
- Email: 300-500 words, comprehensive yet concise
- LinkedIn: 150-250 words, punchy and engaging

Your content should help busy professionals quickly decide which events are worth their time."""

    def generate_newsletter_content(self, events: List[Event], format: str = "email") -> str:
        """
        生成通讯内容
        
        Args:
            events: 活动列表
            format: 输出格式 ("email" 或 "linkedin")
            
        Returns:
            str: 生成的通讯内容
            
        Raises:
            ContentGenerationException: 当内容生成失败时
        """
        try:
            # 验证格式
            if format not in ["email", "linkedin"]:
                raise ValueError(f"不支持的格式: {format}")
            
            # 构建用户提示词
            user_prompt = self._build_user_prompt(events, format)
            
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000 if format == "email" else 500
            )
            
            # 提取生成的内容
            content = response.choices[0].message.content.strip()
            
            logger.info(f"成功生成{format}格式的通讯内容")
            return content
            
        except Exception as e:
            error_msg = f"生成通讯内容时出错: {str(e)}"
            logger.error(error_msg)
            raise ContentGenerationException(error_msg)

    def _build_user_prompt(self, events: List[Event], format: str) -> str:
        """构建用户提示词"""
        
        # 按城市分组事件
        events_by_city = {}
        for event in events:
            city = event.location.city
            if city not in events_by_city:
                events_by_city[city] = []
            events_by_city[city].append(event)
        
        # 构建事件描述
        events_description = ""
        for city, city_events in events_by_city.items():
            events_description += f"\n{city} Events:\n"
            for event in city_events:
                event_type = "Online" if event.is_virtual else "In-person"
                events_description += f"""
- Event: {event.title}
  Date: {event.start_time.strftime('%B %d, %Y')}
  Time: {event.start_time.strftime('%I:%M %p')}
  Location: {event.location.venue or 'TBA'} ({event_type})
  Description: {event.description}
  Organizer: {event.organizer.name}
  URL: {event.url}
"""

        # 构建完整的提示词
        prompt = f"""Please generate a {format.upper()} format newsletter about the following upcoming tech and investment events.

Output Requirements:
{"- Length: 300-500 words, provide sufficient details and context" if format == "email" else "- Length: 150-250 words, concise and engaging for social media"}
- Structure:
  1. Compelling headline
  2. Brief intro highlighting key events
  3. Event details (grouped by city)
  4. Encouraging outro

Events Data:
{events_description}

Additional Guidelines:
1. Focus on value proposition for founders/investors
2. Include specific dates and registration links
3. Maintain professional tone
4. {"Provide comprehensive overview" if format == "email" else "Keep it punchy and social-media friendly"}"""

        return prompt