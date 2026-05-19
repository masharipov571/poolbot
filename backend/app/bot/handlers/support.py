from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from ...database import SessionLocal
from ... import models
from ...config import settings
from ..keyboards.inline import get_go_home_keyboard

router = Router()

class SupportStates(StatesGroup):
    WaitingForSupportMessage = State()

@router.callback_query(F.data == "support_contact")
async def cb_support_contact(callback: types.CallbackQuery, state: FSMContext):
    """
    Triggers support ticket creation state.
    """
    await state.set_state(SupportStates.WaitingForSupportMessage)
    await callback.message.edit_text(
        "📬 **Adminga Murojaat bo'limi**\n\n"
        "Iltimos, adminga yubormoqchi bo'lgan savolingiz yoki taklifingizni matn ko'rinishida yozib yuboring.\n"
        "Admin javob yozganida bot sizga real-time rejimda xabar beradi! ⚡",
        reply_markup=get_go_home_keyboard(),
        parse_mode="Markdown"
    )

@router.message(SupportStates.WaitingForSupportMessage)
async def handle_waiting_support_msg(message: types.Message, state: FSMContext):
    """
    Captures inquiry and forwards to the Admin Support Group if configured.
    """
    inquiry = message.text.strip()
    await state.clear()
    
    if not settings.ADMIN_GROUP_ID:
        await message.answer(
            "⚠️ Hozircha **Adminga Murojaat** tizimi sozlanmagan. Iltimos, keyinroq urinib ko'ring yoki to'g'ridan-to'g'ri admin bilan bog'laning.",
            reply_markup=get_go_home_keyboard()
        )
        return
        
    try:
        # Format the support ticket metadata block
        user = message.from_user
        ticket_card = (
            f"📬 **YANGI MUROJAAT!**\n\n"
            f"👤 **Foydalanuvchi:** {user.first_name or ''} {user.last_name or ''}\n"
            f"🏷️ **Username:** @{user.username or 'yoq'}\n"
            f"🆔 **Telegram ID:** `{user.id}`\n\n"
            f"💬 **Savol:** {inquiry}"
        )
        
        # Send inquiry to Admin Group
        group_msg = await message.bot.send_message(
            chat_id=settings.ADMIN_GROUP_ID,
            text=ticket_card,
            parse_mode="Markdown"
        )
        
        # Store ticket mapping to handle reply matching later
        async with SessionLocal() as db:
            ticket = models.SupportTicket(
                user_id=user.id,
                group_message_id=group_msg.message_id
            )
            db.add(ticket)
            await db.commit()
            
        await message.answer(
            "✅ **Sizning savolingiz adminga muvaffaqiyatli yetkazildi!**\n"
            "Admin javob yo'llashi bilanoq sizga xabar beramiz.",
            reply_markup=get_go_home_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await message.answer(
            f"❌ Savolni adminga yetkazishda xatolik yuz berdi: {str(e)}",
            reply_markup=get_go_home_keyboard()
        )

@router.message(F.chat.id == settings.ADMIN_GROUP_ID)
async def handle_admin_group_reply(message: types.Message):
    """
    Intercepts group replies. If an admin replies to a forwarded ticket message,
    routes the response directly back to the target user.
    """
    if not message.reply_to_message:
        return
        
    group_msg_id = message.reply_to_message.message_id
    
    async with SessionLocal() as db:
        # Check if replied message is an active support ticket
        ticket_q = await db.execute(select(models.SupportTicket).where(models.SupportTicket.group_message_id == group_msg_id))
        ticket = ticket_q.scalar_one_or_none()
        
        if not ticket:
            return
            
        target_user_id = ticket.user_id
        
        try:
            # Deliver response privately to user
            response_card = (
                f"📬 **Admindan Javob keldi!**\n\n"
                f"💬 {message.text or '[Media xabar]'}"
            )
            await message.bot.send_message(
                chat_id=target_user_id,
                text=response_card,
                parse_mode="Markdown"
            )
            
            # Confirm delivery in the support group
            await message.reply("✅ Javobingiz foydalanuvchiga muvaffaqiyatli yetkazildi!")
            
        except Exception as e:
            await message.reply(f"❌ Javobni yetkazishda xatolik yuz berdi: {str(e)}")
