from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Auth Schemas
class TokenRequest(BaseModel):
    token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str

# User Schemas
class UserResponse(BaseModel):
    id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: datetime
    last_active_at: datetime
    is_blocked: bool

    class Config:
        from_attributes = True

# Quiz Schemas
class QuestionResponse(BaseModel):
    id: int
    question_text: str
    options: List[str]

    class Config:
        from_attributes = True

class QuizResponse(BaseModel):
    id: str
    title: str
    creator_id: Optional[int]
    created_at: datetime
    total_questions: int

    class Config:
        from_attributes = True

class QuizDetailResponse(QuizResponse):
    questions: List[QuestionResponse]

# Quiz Session Schemas
class SessionStartRequest(BaseModel):
    quiz_id: str
    question_count: int
    timer_seconds: int

class SessionResponse(BaseModel):
    id: str
    user_id: int
    quiz_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    selected_question_count: int
    timer_seconds: int
    current_question_index: int
    score: int
    status: str

    class Config:
        from_attributes = True

# Broadcast Schemas
class BroadcastCreate(BaseModel):
    type: str # text, photo, video, file
    content: str
    buttons: Optional[List[Dict[str, str]]] = None # [{"text": "BTN", "url": "https://..."}]
    scheduled_at: Optional[datetime] = None

class BroadcastResponse(BaseModel):
    id: int
    type: str
    content: str
    buttons: Optional[List[Dict[str, str]]] = None
    status: str
    total_targets: int
    sent_count: int
    failed_count: int
    scheduled_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class BroadcastTargetResponse(BaseModel):
    id: int
    broadcast_id: int
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    status: str
    error_message: Optional[str]
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True

# Analytics Schemas
class UserGrowthPoint(BaseModel):
    date: str
    count: int

class ActiveUserStats(BaseModel):
    daily: int
    weekly: int
    monthly: int

class QuizStats(BaseModel):
    total_quizzes: int
    total_questions: int
    total_completions: int
    average_score: float

class AnalyticsDashboard(BaseModel):
    total_users: int
    active_users: ActiveUserStats
    quiz_stats: QuizStats
    user_growth: List[UserGrowthPoint]
    most_active_users: List[Dict[str, Any]]
    most_used_quizzes: List[Dict[str, Any]]
    online_sessions_count: int
    recent_logs: List[Dict[str, Any]]
