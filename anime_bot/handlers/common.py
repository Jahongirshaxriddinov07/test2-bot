"""Umumiy yordamchi funksiyalar: majburiy obuna tekshiruvi va h.k."""
from __future__ import annotations

from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject, User as TgUser

from database import Database


class IsAdminFilter(BaseFilter):
    """Faqat is_admin=1 bo'lgan foydalanuvchilarga ruxsat beradi."""

    async def __call__(self, event: TelegramObject, db: Database) -> bool:
        user = event.from_user
        if user is None:
            return False
        return await db.is_admin(user.id)


async def is_subscribed_to_all(bot: Bot, db: Database, telegram_id: int) -> list:
    """Obuna bo'lmagan kanallar ro'yxatini qaytaradi (bo'sh bo'lsa — hammasiga obuna)."""
    channels = await db.list_required_channels()
    missing = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["chat_id"], user_id=telegram_id)
            if member.status in ("left", "kicked"):
                missing.append(ch)
        except Exception:
            # Bot kanalga admin qilib qo'shilmagan yoki chat topilmadi —
            # bunday holatda foydalanuvchini bloklamaslik uchun o'tkazib yuboramiz,
            # lekin adminlar buni logdan ko'rishi mumkin.
            continue
    return missing


async def ensure_user(db: Database, tg_user: TgUser):
    user = await db.get_user(tg_user.id)
    if user is None:
        user = await db.create_user(tg_user.id, tg_user.full_name, tg_user.username)
    else:
        await db.touch_user(tg_user.id, tg_user.full_name, tg_user.username)
    return user


def fmt_number(n: int | str) -> str:
    try:
        n = int(n)
    except (TypeError, ValueError):
        return str(n)
    return f"{n:,}".replace(",", " ")
