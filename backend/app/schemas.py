from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date

# 用户相关Schema
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


ARTICLE_CATEGORIES = [
    "慢性病管理",
    "饮食营养",
    "心理健康",
    "运动健身",
    "老年健康",
    "儿童健康",
]


class HealthArticleBase(BaseModel):
    title: str
    category: str
    summary: Optional[str] = None
    content: str
    cover_image: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class HealthArticleCreate(HealthArticleBase):
    pass


class HealthArticleUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = None
    tags: Optional[List[str]] = None


class HealthArticleResponse(HealthArticleBase):
    id: int
    view_count: int
    favorite_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthArticleListResponse(BaseModel):
    items: List[HealthArticleResponse]
    total: int
    page: int
    page_size: int


class FavoriteResponse(BaseModel):
    article_id: int
    is_favorited: bool


class ReadingHistoryResponse(BaseModel):
    article_id: int
    article_title: str
    category: str
    last_read_at: datetime
    read_count: int


class HomepageRecommendationResponse(BaseModel):
    hot_articles: List[HealthArticleResponse]
    latest_articles: List[HealthArticleResponse]

class Token(BaseModel):
    access_token: str
    token_type: str
    username: Optional[str] = None
    role: Optional[str] = None

# 健康数据Schema
class HealthDataBase(BaseModel):
    weight: Optional[float] = None
    height: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    blood_sugar: Optional[float] = None

class HealthDataCreate(HealthDataBase):
    recorded_at: Optional[datetime] = None

class HealthDataUpdate(HealthDataBase):
    recorded_at: Optional[datetime] = None

class HealthDataResponse(HealthDataBase):
    id: int
    user_id: int
    recorded_at: datetime
    
    class Config:
        from_attributes = True

class HealthAnalysisRequest(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None

# AI聊天Schema
class ChatMessage(BaseModel):
    message: str
    is_user: bool = True

class ChatResponse(BaseModel):
    reply: str
    timestamp: datetime

# 知识库Schema
class KnowledgeBase(BaseModel):
    title: str
    content: str
    category: str
    tags: Optional[list] = []

class KnowledgeResponse(KnowledgeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
