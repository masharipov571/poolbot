import os
import random
import datetime
from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from ...database import SessionLocal
from ... import models
from ...parser import parse_quiz_file, QuizParseError
from ..keyboards.inline import (
    get_chunk_keyboard, get_timer_keyboard, get_shuffle_keyboard, 
    get_go_home_keyboard, get_completed_keyboard
)

router = Router()

class UploadStates(StatesGroup):
    WaitingForDocument = State()

# Directory for temp uploads
UPLOAD_DIR = "./data/temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def generate_unique_quiz_code(db) -> str:
    """
    Generates a unique 6-digit code for a quiz to share easily.
    """
    while True:
        code = str(random.randint(100000, 999999))
        q = await db.execute(select(models.Quiz).where(models.Quiz.unique_code == code))
        if not q.scalar_one_or_none():
            return code

@router.callback_query(F.data == "auto_test_create")
async def cb_auto_test_create(callback: types.CallbackQuery, state: FSMContext):
    """
    Instructions when admin/user starts test creation.
    """
    await state.set_state(UploadStates.WaitingForDocument)
    instruction_text = (
        "📄 **Fayl yuboring**\n\n"
        "📁 **Qo'llab-quvvatlanadigan formatlar:** DOCX, DOC, TXT, PDF\n\n"
        "📋 **Fayl formati:**\n"
        "Har bir savol quyidagi shaklda bo'lishi kerak:\n\n"
        "```text\n"
        "+++\n"
        "Savol matni?\n"
        "===\n"
        "#To'g'ri javob\n"
        "===\n"
        "Noto'g'ri javob 1\n"
        "===\n"
        "Noto'g'ri javob 2\n"
        "===\n"
        "Noto'g'ri javob 3\n"
        "+++\n"
        "```\n\n"
        "⚠️ **Muhim:**\n"
        "• `+++` — savol boshlanishi va tugashi\n"
        "• `===` — variantlar orasidagi ajratuvchi\n"
        "• `#` — to'g'ri javob oldiga qo'yiladi\n"
        "• Har bir savolda faqat bitta to'g'ri javob bo'lishi kerak\n"
        "• Variantlar soni 2 dan 10 gacha bo'lishi mumkin"
    )
    await callback.message.edit_text(
        instruction_text,
        reply_markup=get_go_home_keyboard(),
        parse_mode="Markdown"
    )

@router.message(UploadStates.WaitingForDocument, F.document)
async def handle_document_upload(message: types.Message, state: FSMContext):
    """
    Receives DOCX, PDF, or TXT documents and parses them in lenient mode.
    """
    await state.clear()
    doc = message.document
    filename = doc.file_name
    _, ext = os.path.splitext(filename.lower())
    
    if ext not in [".docx", ".pdf", ".txt", ".doc"]:
        await message.answer("⚠️ Faqat **DOCX**, **PDF** yoki **TXT** formatidagi test fayllarini yuklashingiz mumkin.")
        return
        
    processing_msg = await message.answer("⏳ Fayl yuklanmoqda va tahlil qilinmoqda...")
    
    # Download
    file_info = await message.bot.get_file(doc.file_id)
    dest_path = os.path.join(UPLOAD_DIR, f"{message.from_user.id}_{datetime.datetime.utcnow().timestamp()}{ext}")
    
    try:
        await message.bot.download_file(file_info.file_path, dest_path)
        
        # LENIENT PARSING: skips invalid blocks, ensures perfect stability
        parsed_questions = parse_quiz_file(dest_path)
        
        async with SessionLocal() as db:
            # Create Quiz (initially without code and settings)
            quiz = models.Quiz(
                title=os.path.splitext(filename)[0],
                creator_id=message.from_user.id,
                total_questions=len(parsed_questions)
            )
            db.add(quiz)
            await db.flush() # Populate Quiz ID
            
            for q in parsed_questions:
                question = models.Question(
                    quiz_id=quiz.id,
                    question_text=q["question_text"],
                    options=q["options"],
                    correct_option_index=q["correct_option_index"]
                )
                db.add(question)
                
            await db.commit()
            
            # Switch to inline settings selector (Chunking configuration)
            success_text = (
                f"✅ **Savollar muvaffaqiyatli yuklandi!**\n\n"
                f"📌 **Nomi:** {quiz.title}\n"
                f"❓ **Jami savollar:** {quiz.total_questions} ta\n\n"
                f"⚙️ **Sozlash:** Ushbu test savollarini do'stlaringiz nechtadan chunk (qism) qilib yechishini xohlaysiz?"
            )
            
            await processing_msg.delete()
            await message.answer(
                success_text, 
                reply_markup=get_chunk_keyboard(quiz.id, quiz.total_questions),
                parse_mode="Markdown"
            )
            
    except QuizParseError as e:
        await processing_msg.delete()
        await message.answer(f"❌ **Parse xatoligi:**\n{str(e)}", parse_mode="Markdown")
    except Exception as e:
        await processing_msg.delete()
        await message.answer(f"❌ Faylni yuklashda xatolik yuz berdi: {str(e)}")
    finally:
        if os.path.exists(dest_path):
            os.remove(dest_path)

@router.callback_query(F.data.startswith("setupchunk_"))
async def cb_setup_chunk(callback: types.CallbackQuery):
    """
    Sets the chunk size and redirects to timer settings.
    """
    _, quiz_id, chunk_size = callback.data.split("_")
    chunk_size = int(chunk_size)
    
    await callback.message.edit_text(
        f"⏱️ **Har bir savol uchun vaqt (taymer) belgilang:**\n(Chunk hajmi: {chunk_size} ta savol)",
        reply_markup=get_timer_keyboard(quiz_id, chunk_size),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("setuptimer_"))
async def cb_setup_timer(callback: types.CallbackQuery):
    """
    Sets the timer and redirects to shuffle mode.
    """
    _, quiz_id, chunk_size, timer = callback.data.split("_")
    chunk_size = int(chunk_size)
    timer = int(timer)
    
    await callback.message.edit_text(
        f"🔀 **Aralashtirish parametrlarini tanlang:**\n"
        f"(Chunk: {chunk_size} ta savol | Taymer: {timer if timer > 0 else 'Cheksiz'} soniya)",
        reply_markup=get_shuffle_keyboard(quiz_id, chunk_size, timer),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("setupshuf_"))
async def cb_setup_shuffle(callback: types.CallbackQuery):
    """
    Finalizes all settings, generates unique code, and saves everything.
    """
    _, quiz_id, chunk_size, timer, shuffle_mode = callback.data.split("_")
    chunk_size = int(chunk_size)
    timer = int(timer)
    
    async with SessionLocal() as db:
        q = await db.execute(select(models.Quiz).where(models.Quiz.id == quiz_id))
        quiz = q.scalar_one_or_none()
        
        if not quiz:
            await callback.answer("Quiz topilmadi.", show_alert=True)
            return
            
        # Generate 6-digit code
        unique_code = await generate_unique_quiz_code(db)
        
        quiz.unique_code = unique_code
        quiz.chunk_size = chunk_size
        quiz.timer_seconds = timer
        quiz.shuffle_mode = shuffle_mode
        
        await db.commit()
        
        # Display success card
        shuf_lbl = {
            "questions": "Savollar aralashtiriladi",
            "options": "Javoblar aralashtiriladi",
            "both": "Savollar va javoblar aralashtiriladi",
            "none": "Aralashtirilmaydi"
        }.get(shuffle_mode, "Aralashtirilmaydi")
        
        success_msg = (
            f"🎉 **Test muvaffaqiyatli yaratildi va faollashtirildi!**\n\n"
            f"📌 **Nomi:** {quiz.title}\n"
            f"🔑 **Unikal kod:** `{unique_code}`\n"
            f"📦 **Chunk hajmi:** {chunk_size} tadan\n"
            f"⏱️ **Taymer:** {timer if timer > 0 else 'Cheksiz'} soniya\n"
            f"🔀 **Tartib:** {shuf_lbl}\n\n"
            f"📢 **Ulashish uchun:** Do'stlaringizga ushbu unikal kodni yuboring. "
            f"Ular botga kirib **🔑 Kod orqali Test Yechish** bo'limida kodni kiritsa, test avtomatik ishga tushadi!"
        )
        
        await callback.message.edit_text(
            success_msg,
            reply_markup=get_completed_keyboard(unique_code),
            parse_mode="Markdown"
        )
