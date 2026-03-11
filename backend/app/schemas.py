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


class RagKnowledgeDocBase(BaseModel):
    title: str
    category: str
    content: str
    source: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True


class RagKnowledgeDocCreate(RagKnowledgeDocBase):
    pass


class RagKnowledgeDocUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class RagKnowledgeDocResponse(RagKnowledgeDocBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RagKnowledgeDocListResponse(BaseModel):
    items: List[RagKnowledgeDocResponse]
    total: int
    page: int
    page_size: int


class RagKnowledgeImportResponse(BaseModel):
    items: List[RagKnowledgeDocResponse] = Field(default_factory=list)
    imported_count: int = 0
    skipped_files: List[str] = Field(default_factory=list)
    message: str


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
    is_favorited: bool = False
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
    favorite_count: int = 0


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


class SocialLoginInitRequest(BaseModel):
    provider: str
    auth_code: Optional[str] = None
    nickname: Optional[str] = None


class SocialLoginInitResponse(BaseModel):
    need_profile_completion: bool
    social_ticket: Optional[str] = None
    social_provider: Optional[str] = None
    social_nickname: Optional[str] = None
    suggested_username: Optional[str] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None


class SocialProfileCompleteRequest(BaseModel):
    social_ticket: str
    username: str
    email: EmailStr
    password: str


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
    chat_id: Optional[int] = None
    references: List[str] = Field(default_factory=list)
    personalization_used: bool = False


class AiHomeAdviceResponse(BaseModel):
    summary: str
    recommendations: List[str] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    based_on_public_records: int = 0

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
    project_subtitle: str = "智能健康数据与知识服务平台"
    welcome_message: str = "欢迎使用健康管理系统，请根据角色进入对应工作台。"
    support_email: str = "support@health.local"
    support_phone: str = "400-800-2026"
    allow_user_register: bool = True
    allow_social_login: bool = True
    ai_enabled: bool = True
    knowledge_import_enabled: bool = True
    article_auto_publish: bool = False
    enable_operation_log: bool = True
    enable_blockchain_sync: bool = False
    maintenance_mode: bool = False
    default_health_data_public: bool = False
    default_article_cover: str = ""
    session_timeout_minutes: int = 120
    max_upload_size_mb: int = 20
    homepage_banner_title: str = "科学管理健康，智能辅助决策"
    homepage_banner_subtitle: str = "聚合健康数据、知识内容与 AI 分析能力"
    password_min_length: int = 6
    log_retention_days: int = 30


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
