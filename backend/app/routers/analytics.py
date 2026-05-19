import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from ..database import get_db
from ..schemas import AnalyticsDashboard
from ..auth import get_current_admin
from .. import models

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=AnalyticsDashboard)
async def get_dashboard_analytics(
    admin_id: int = Depends(get_current_admin), 
    db: AsyncSession = Depends(get_db)
):
    """
    Returns premium real-time metrics for the admin dashboard.
    Designed to work on both SQLite and PostgreSQL without modification.
    """
    now = datetime.datetime.utcnow()
    
    # 1. Total Users
    total_users_q = await db.execute(select(func.count(models.User.id)))
    total_users = total_users_q.scalar_one_or_none() or 0
    
    # 2. Active Users (DAU, WAU, MAU)
    day_ago = now - datetime.timedelta(days=1)
    week_ago = now - datetime.timedelta(days=7)
    month_ago = now - datetime.timedelta(days=30)
    
    dau_q = await db.execute(select(func.count(models.User.id)).where(models.User.last_active_at >= day_ago))
    dau = dau_q.scalar_one_or_none() or 0
    
    wau_q = await db.execute(select(func.count(models.User.id)).where(models.User.last_active_at >= week_ago))
    wau = wau_q.scalar_one_or_none() or 0
    
    mau_q = await db.execute(select(func.count(models.User.id)).where(models.User.last_active_at >= month_ago))
    mau = mau_q.scalar_one_or_none() or 0
    
    # 3. Quiz & Completion Stats
    total_quizzes_q = await db.execute(select(func.count(models.Quiz.id)))
    total_quizzes = total_quizzes_q.scalar_one_or_none() or 0
    
    total_questions_q = await db.execute(select(func.count(models.Question.id)))
    total_questions = total_questions_q.scalar_one_or_none() or 0
    
    total_completions_q = await db.execute(
        select(func.count(models.QuizSession.id)).where(models.QuizSession.status == "completed")
    )
    total_completions = total_completions_q.scalar_one_or_none() or 0
    
    avg_score_q = await db.execute(
        select(func.avg(models.QuizSession.score)).where(models.QuizSession.status == "completed")
    )
    avg_score = avg_score_q.scalar_one_or_none() or 0.0
    avg_score = round(float(avg_score), 1)
    
    # 4. User Growth Curve (Last 15 days)
    # Pull user signups from last 15 days, group in python for cross-db safety
    fifteen_days_ago = now - datetime.timedelta(days=15)
    users_recent_q = await db.execute(
        select(models.User.created_at)
        .where(models.User.created_at >= fifteen_days_ago)
        .order_by(models.User.created_at)
    )
    recent_signups = users_recent_q.scalars().all()
    
    # Pre-populate dates
    growth_dict = {}
    for d in range(15):
        date_str = (now - datetime.timedelta(days=d)).strftime("%Y-%m-%d")
        growth_dict[date_str] = 0
        
    for signup in recent_signups:
        date_str = signup.strftime("%Y-%m-%d")
        if date_str in growth_dict:
            growth_dict[date_str] += 1
            
    # Formulate cumulative or direct growth list
    # We will show cumulative growth curve (it looks beautiful)
    user_growth_list = []
    # Get base users before fifteen days
    base_users_q = await db.execute(select(func.count(models.User.id)).where(models.User.created_at < fifteen_days_ago))
    running_total = base_users_q.scalar_one_or_none() or 0
    
    sorted_dates = sorted(growth_dict.keys())
    for d_str in sorted_dates:
        running_total += growth_dict[d_str]
        user_growth_list.append({"date": d_str, "count": running_total})
        
    # In case there are no past users, ensure we display at least some points
    if not user_growth_list:
        for d in range(14, -1, -1):
            date_str = (now - datetime.timedelta(days=d)).strftime("%Y-%m-%d")
            user_growth_list.append({"date": date_str, "count": total_users})
            
    # 5. Most Active Users
    active_users_q = await db.execute(
        select(
            models.User.id, 
            models.User.username, 
            models.User.first_name, 
            func.count(models.QuizSession.id).label("session_count"),
            func.sum(models.QuizSession.score).label("total_score")
        )
        .join(models.QuizSession, models.User.id == models.QuizSession.user_id)
        .group_by(models.User.id, models.User.username, models.User.first_name)
        .order_by(desc("session_count"))
        .limit(5)
    )
    active_users_res = active_users_q.all()
    most_active_users = []
    for u_id, username, first_name, session_count, total_score in active_users_res:
        most_active_users.append({
            "id": u_id,
            "username": username or "No username",
            "name": first_name or "Ismsiz",
            "completions": session_count,
            "total_score": int(total_score or 0)
        })
        
    # 6. Most Used Quizzes
    used_quizzes_q = await db.execute(
        select(
            models.Quiz.id,
            models.Quiz.title,
            func.count(models.QuizSession.id).label("use_count")
        )
        .join(models.QuizSession, models.Quiz.id == models.QuizSession.quiz_id)
        .group_by(models.Quiz.id, models.Quiz.title)
        .order_by(desc("use_count"))
        .limit(5)
    )
    used_quizzes_res = used_quizzes_q.all()
    most_used_quizzes = []
    for q_id, title, use_count in used_quizzes_res:
        most_used_quizzes.append({
            "id": q_id,
            "title": title,
            "usage": use_count
        })
        
    # 7. Online/Active Sessions (Currently playing in the last 15 minutes)
    fifteen_mins_ago = now - datetime.timedelta(minutes=15)
    online_q = await db.execute(
        select(func.count(models.QuizSession.id))
        .where(models.QuizSession.status == "active")
        .where(models.QuizSession.started_at >= fifteen_mins_ago)
    )
    online_count = online_q.scalar_one_or_none() or 0
    
    # 8. Recent Admin Logs
    logs_q = await db.execute(
        select(models.AdminLog)
        .order_by(desc(models.AdminLog.created_at))
        .limit(5)
    )
    logs_res = logs_q.scalars().all()
    recent_logs = []
    for log in logs_res:
        recent_logs.append({
            "id": log.id,
            "action": log.action,
            "details": log.details,
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    return AnalyticsDashboard(
        total_users=total_users,
        active_users={
            "daily": dau,
            "weekly": wau,
            "monthly": mau
        },
        quiz_stats={
            "total_quizzes": total_quizzes,
            "total_questions": total_questions,
            "total_completions": total_completions,
            "average_score": avg_score
        },
        user_growth=user_growth_list,
        most_active_users=most_active_users,
        most_used_quizzes=most_used_quizzes,
        online_sessions_count=online_count,
        recent_logs=recent_logs
    )
