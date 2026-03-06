from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date

# 用户相关Schema
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: str = "user"
    admin_register_key: Optional[str] = None

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    wallet_address: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdminUserResponse(BaseModel):
    username: str
    email: str
    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    items: List[AdminUserResponse]
    total: int
    page: int
    page_size: int


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


class UserRegisterResponse(UserResponse):
    generated_private_key: Optional[str] = None


class UserProfileUpsertRequest(BaseModel):
    profile_data: str
    private_key: Optional[str] = None
    is_public: bool = False


class UserProfileResponse(BaseModel):
    user_id: int
    wallet_address: Optional[str] = None
    profile_is_public: bool
    profile_data: Optional[str] = None


class UserPrivateKeyRevealRequest(BaseModel):
    password: str


class UserPrivateKeyRevealResponse(BaseModel):
    private_key: str

# 健康数据Schema
class HealthDataBase(BaseModel):
    data_title: Optional[str] = None
    data_content: Optional[str] = None
    file_type: str = "text"
    pdf_data_base64: Optional[str] = None
    pdf_size: Optional[int] = None
    is_public: bool = False

class HealthDataCreate(HealthDataBase):
    private_key: Optional[str] = None

class HealthDataUpdate(HealthDataBase):
    private_key: Optional[str] = None

class HealthDataResponse(HealthDataBase):
    id: int
    user_id: int
    requires_private_key: bool = False
    onchain_tx_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
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


class AdminSystemSettings(BaseModel):
    project_name: str = "健康管理系统"
    allow_user_register: bool = True
    ai_enabled: bool = True
    maintenance_mode: bool = False
    default_health_data_public: bool = False


class AdminSystemLogResponse(BaseModel):
    id: int
    level: str
    module: str
    action: str
    message: str
    operator_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
