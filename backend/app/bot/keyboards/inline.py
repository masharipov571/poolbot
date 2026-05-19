from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_start_keyboard() -> InlineKeyboardMarkup:
    """
    Returns the main menu keyboard with updated, professional options.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Avtomatik Test Tuzish", callback_data="auto_test_create")
    builder.button(text="🔑 Kod orqali Test Yechish", callback_data="solve_test_code")
    builder.button(text="📊 Mening Natijalarim", callback_data="my_stats")
    builder.button(text="📬 Adminga Murojaat", callback_data="support_contact")
    builder.button(text="⚙️ Yordam", callback_data="quiz_help")
    builder.adjust(1, 2, 2)
    return builder.as_markup()

def get_chunk_keyboard(quiz_id: str, total_q: int) -> InlineKeyboardMarkup:
    """
    Displays chunking configuration sizes (25, 30, 50, etc.).
    """
    builder = InlineKeyboardBuilder()
    options = [25, 30, 50, 100, total_q]
    # Filter and sort distinct options smaller than or equal to total questions
    options = sorted(list(set([x for x in options if x <= total_q])))
    
    for opt in options:
        label = "Barchasi" if opt == total_q else f"{opt} talik chunk"
        builder.button(text=label, callback_data=f"setupchunk_{quiz_id}_{opt}")
        
    builder.button(text="🏠 Bosh Menyu", callback_data="go_home")
    builder.adjust(1)
    return builder.as_markup()

def get_timer_keyboard(quiz_id: str, chunk: int) -> InlineKeyboardMarkup:
    """
    Timer options keyboard for chunked sets (15s, 30s, 45s, 50s, 60s).
    """
    builder = InlineKeyboardBuilder()
    timers = [
        (15, "15 soniya ⚡"),
        (30, "30 soniya"),
        (45, "45 soniya"),
        (50, "50 soniya"),
        (60, "1 daqiqa"),
        (0, "Cheksiz ⏱️")
    ]
    
    for t_val, t_lbl in timers:
        builder.button(text=t_lbl, callback_data=f"setuptimer_{quiz_id}_{chunk}_{t_val}")
        
    builder.button(text="🏠 Bosh Menyu", callback_data="go_home")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def get_shuffle_keyboard(quiz_id: str, chunk: int, timer: int) -> InlineKeyboardMarkup:
    """
    Shuffle options keyboard.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Savollarni aralashtirish", callback_data=f"setupshuf_{quiz_id}_{chunk}_{timer}_questions")
    builder.button(text="🔀 Javoblarni aralashtirish", callback_data=f"setupshuf_{quiz_id}_{chunk}_{timer}_options")
    builder.button(text="🔥 Barchasini aralashtirish", callback_data=f"setupshuf_{quiz_id}_{chunk}_{timer}_both")
    builder.button(text="❌ Aralashtirmasdan", callback_data=f"setupshuf_{quiz_id}_{chunk}_{timer}_none")
    builder.button(text="🏠 Bosh Menyu", callback_data="go_home")
    builder.adjust(1)
    return builder.as_markup()

def get_play_keyboard(session_id: str) -> InlineKeyboardMarkup:
    """
    Interactive play keyboard with skip option.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="➡️ Savolni o'tkazib yuborish (Skip)", callback_data=f"skip_{session_id}")
    return builder.as_markup()

def get_completed_keyboard(quiz_id: str) -> InlineKeyboardMarkup:
    """
    Keyboard shown at the end of a session.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Qayta topshirish", callback_data=f"start_code_quiz_{quiz_id}")
    builder.button(text="🏠 Bosh menyu", callback_data="go_home")
    builder.adjust(1)
    return builder.as_markup()

def get_go_home_keyboard() -> InlineKeyboardMarkup:
    """
    A single go-home button keyboard.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Bosh Menyu", callback_data="go_home")
    return builder.as_markup()

def get_parts_keyboard(quiz_id: str, total: int, chunk: int) -> InlineKeyboardMarkup:
    """
    Generates a list of part selection buttons (e.g. 1-qism (1-25), 2-qism (26-50)).
    """
    builder = InlineKeyboardBuilder()
    import math
    num_parts = math.ceil(total / chunk)
    for i in range(num_parts):
        start_num = i * chunk + 1
        end_num = min((i + 1) * chunk, total)
        builder.button(
            text=f"📦 {i+1}-qism ({start_num}-{end_num}-savollar)",
            callback_data=f"playchunk_{quiz_id}_{i}"
        )
    builder.button(text="🏠 Bosh Menyu", callback_data="go_home")
    builder.adjust(1)
    return builder.as_markup()

