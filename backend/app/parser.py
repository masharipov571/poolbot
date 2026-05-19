import os
import re
from typing import List, Dict, Any
from docx import Document
from pypdf import PdfReader

class QuizParseError(Exception):
    pass

def parse_quiz_text(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parses the custom quiz format:
    +++
    Question?
    ===
    #Correct Answer
    ===
    Incorrect Answer 1
    ===
    Incorrect Answer 2
    +++
    
    Robust upgrades:
    - Skips blocks without a '#' marked option (perfectly ignores headers, intros, and malformed questions).
    - Ignores leading whitespaces when checking for '#' prefix (e.g., '  #Option' works).
    """
    # Split text by '+++' boundary
    blocks = raw_text.split("+++")
    questions = []
    
    for i, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue
            
        # Split by '===' boundary
        parts = [p.strip() for p in block.split("===") if p.strip()]
        
        if len(parts) < 2:
            # Not a valid question block (e.g., header, title, description)
            continue
            
        question_text = parts[0]
        options = parts[1:]
        
        # Robust check: Ensure at least one option starts with '#' (ignoring spaces)
        has_correct = False
        for opt in options:
            if opt.strip().startswith("#"):
                has_correct = True
                break
                
        if not has_correct:
            # If no option has '#', it's likely header/intro text or a malformed block.
            # We simply skip it to prevent crashing the entire quiz import!
            continue
            
        correct_index = -1
        cleaned_options = []
        
        for idx, option in enumerate(options):
            opt_stripped = option.strip()
            if opt_stripped.startswith("#"):
                if correct_index != -1:
                    raise QuizParseError(
                        f"Xatolik yuz berdi: Savol '{question_text[:50]}...'da birdan ortiq to'g'ri javob (#) topildi."
                    )
                correct_index = idx
                # Remove '#' and strip spaces
                cleaned_options.append(opt_stripped[1:].strip())
            else:
                cleaned_options.append(option)
                
        if len(cleaned_options) < 2:
            # Question must have at least 2 options to be played
            continue
            
        if len(cleaned_options) > 10:
            raise QuizParseError(
                f"Xatolik: '{question_text[:50]}...' savolida variantlar soni 10 tadan ko'p ({len(cleaned_options)} ta). Telegram testlarida maksimal 10 ta variant bo'lishi mumkin."
            )
            
        questions.append({
            "question_text": question_text,
            "options": cleaned_options,
            "correct_option_index": correct_index
        })
        
    if not questions:
        raise QuizParseError("Faylda hech qanday yaroqli test savoli (boshiga '#' qo'yilgan to'g'ri javobga ega savol) topilmadi. Formatni tekshiring.")
        
    return questions

def parse_docx(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts text from a DOCX file and parses it.
    """
    try:
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        text = "\n".join(full_text)
        return parse_quiz_text(text)
    except Exception as e:
        if isinstance(e, QuizParseError):
            raise e
        raise QuizParseError(f"DOCX faylini o'qishda xatolik yuz berdi: {str(e)}")

def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts text from a PDF file and parses it.
    """
    try:
        reader = PdfReader(file_path)
        full_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
        text = "\n".join(full_text)
        return parse_quiz_text(text)
    except Exception as e:
        if isinstance(e, QuizParseError):
            raise e
        raise QuizParseError(f"PDF faylini o'qishda xatolik yuz berdi: {str(e)}")

def parse_txt(file_path: str) -> List[Dict[str, Any]]:
    """
    Reads a TXT file and parses it.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return parse_quiz_text(text)
    except Exception as e:
        if isinstance(e, QuizParseError):
            raise e
        raise QuizParseError(f"TXT faylini o'qishda xatolik yuz berdi: {str(e)}")

def parse_quiz_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Routes the file to the appropriate parser based on extension.
    """
    _, ext = os.path.splitext(file_path.lower())
    if ext == ".docx":
        return parse_docx(file_path)
    elif ext == ".pdf":
        return parse_pdf(file_path)
    elif ext in [".txt", ".doc"]: # Treat doc as txt or let them convert if doc fails. Or we can try docx logic.
        # Note: True binary legacy .doc is rarely used today, but if passed, we attempt as raw text or raise error.
        try:
            return parse_txt(file_path)
        except Exception:
            raise QuizParseError("Eski .DOC formatini to'g'ridan-to'g'ri o'qib bo'lmadi. Iltimos uni .DOCX yoki .TXT formatiga o'tkazib yuboring.")
    else:
        raise QuizParseError(f"Qo'llab-quvvatlanmaydigan fayl formati: {ext}. Faqat DOCX, PDF, TXT fayllari qabul qilinadi.")
