import datetime
import uuid
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, index=True) # Telegram User ID
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_blocked = Column(Boolean, default=False)
    
    quizzes = relationship("Quiz", back_populates="creator")
    sessions = relationship("QuizSession", back_populates="user")

class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    unique_code = Column(String(50), unique=True, index=True, nullable=True)
    title = Column(String(500), nullable=False)
    creator_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    total_questions = Column(Integer, default=0)
    chunk_size = Column(Integer, default=0) # 0 means all questions
    timer_seconds = Column(Integer, default=0) # 0 means unlimited
    shuffle_mode = Column(String(50), default="none") # questions, options, both, none
    
    creator = relationship("User", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    sessions = relationship("QuizSession", back_populates="quiz", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False) # List of strings
    correct_option_index = Column(Integer, nullable=False) # Index in options
    
    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("PollAnswer", back_populates="question", cascade="all, delete-orphan")

class QuizSession(Base):
    __tablename__ = "quiz_sessions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    selected_question_count = Column(Integer, default=0)
    timer_seconds = Column(Integer, default=0) # 0 means unlimited
    current_question_index = Column(Integer, default=0)
    score = Column(Integer, default=0)
    status = Column(String(50), default="active") # active, completed, timed_out
    
    shuffled_questions = Column(JSON, nullable=True) # List of question IDs in shuffled order
    shuffled_options_map = Column(JSON, nullable=True) # Map of QuestionID -> { options: List[str], correct_index: int }
    
    active_poll_id = Column(String(255), nullable=True) # Active telegram poll ID
    active_message_id = Column(Integer, nullable=True) # Active telegram poll message ID
    
    user = relationship("User", back_populates="sessions")
    quiz = relationship("Quiz", back_populates="sessions")
    answers = relationship("PollAnswer", back_populates="session", cascade="all, delete-orphan")

class PollAnswer(Base):
    __tablename__ = "poll_answers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    selected_option_index = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    answered_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    session = relationship("QuizSession", back_populates="answers")
    question = relationship("Question", back_populates="answers")

class BroadcastMessage(Base):
    __tablename__ = "broadcasts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False) # text, photo, video, file
    content = Column(Text, nullable=False) # text content, or file path/file_id
    buttons = Column(JSON, nullable=True) # List of dicts [{"text": "...", "url": "..."}]
    status = Column(String(50), default="pending") # pending, sending, completed, cancelled
    
    total_targets = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    
    scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AdminLog(Base):
    __tablename__ = "admin_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(BigInteger, nullable=False)
    action = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    group_message_id = Column(Integer, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class BroadcastTarget(Base):
    __tablename__ = "broadcast_targets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    broadcast_id = Column(Integer, ForeignKey("broadcasts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    status = Column(String(50), default="pending") # pending, sent, failed
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
