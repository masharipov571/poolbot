from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Dict, Any
from ..database import get_db
from ..schemas import QuizResponse, QuizDetailResponse
from ..auth import get_current_admin
from .. import models

router = APIRouter(prefix="/quizzes", tags=["Quizzes Management"])

@router.get("", response_model=List[Dict[str, Any]])
async def get_quizzes(
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns all uploaded quizzes with statistics (total sessions, questions count).
    """
    query = select(models.Quiz).order_by(desc(models.Quiz.created_at))
    res = await db.execute(query)
    quizzes = res.scalars().all()
    
    quizzes_list = []
    for quiz in quizzes:
        # Fetch creator details
        creator_name = "System"
        if quiz.creator_id:
            creator_q = await db.execute(select(models.User).where(models.User.id == quiz.creator_id))
            creator = creator_q.scalar_one_or_none()
            if creator:
                creator_name = creator.username or creator.first_name or str(creator.id)
                
        # Total sessions
        sess_count_q = await db.execute(
            select(func.count(models.QuizSession.id)).where(models.QuizSession.quiz_id == quiz.id)
        )
        total_sessions = sess_count_q.scalar_one_or_none() or 0
        
        quizzes_list.append({
            "id": quiz.id,
            "title": quiz.title,
            "creator_id": quiz.creator_id,
            "creator_name": creator_name,
            "created_at": quiz.created_at,
            "total_questions": quiz.total_questions,
            "total_sessions": total_sessions
        })
        
    return quizzes_list

@router.get("/{quiz_id}", response_model=QuizDetailResponse)
async def get_quiz_detail(
    quiz_id: str,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns specific quiz information along with all questions.
    """
    quiz_q = await db.execute(
        select(models.Quiz).where(models.Quiz.id == quiz_id)
    )
    quiz = quiz_q.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz topilmadi."
        )
        
    # Fetch questions
    questions_q = await db.execute(
        select(models.Question).where(models.Question.quiz_id == quiz_id)
    )
    questions = questions_q.scalars().all()
    
    return QuizDetailResponse(
        id=quiz.id,
        title=quiz.title,
        creator_id=quiz.creator_id,
        created_at=quiz.created_at,
        total_questions=quiz.total_questions,
        questions=[
            {
                "id": q.id,
                "question_text": q.question_text,
                "options": q.options
            } for q in questions
        ]
    )

@router.delete("/{quiz_id}", response_model=Dict[str, Any])
async def delete_quiz(
    quiz_id: str,
    admin_id: int = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Deletes a quiz and all associated sessions/questions from the database.
    """
    quiz_q = await db.execute(
        select(models.Quiz).where(models.Quiz.id == quiz_id)
    )
    quiz = quiz_q.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz topilmadi."
        )
        
    quiz_title = quiz.title
    
    await db.delete(quiz)
    
    # Log admin action
    admin_log = models.AdminLog(
        admin_id=admin_id,
        action="DELETE_QUIZ",
        details=f"Quiz o'chirib tashlandi: {quiz_title} (ID: {quiz_id})"
    )
    db.add(admin_log)
    await db.commit()
    
    return {
        "message": "Quiz muvaffaqiyatli o'chirildi.",
        "quiz_id": quiz_id
    }
