"""
StockSense AI — Admin Role Assignment CLI Utility

Usage:
  python make_admin.py <email_or_name>
  python make_admin.py --list
"""

import sys
import os
import asyncio
# Add backend/ directory to path so 'app' package is importable from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from sqlalchemy import select, func, or_
from app.db.session import AsyncSessionLocal
from app.models.portfolio import User

async def list_users():
    async with AsyncSessionLocal() as db:
        stmt = select(User).order_by(User.created_at.desc())
        res = await db.execute(stmt)
        users = res.scalars().all()
        print("\n--- StockSense AI Registered Users ---")
        if not users:
            print("No users found in database.")
            return
        for u in users:
            admin_tag = "[ADMIN]" if getattr(u, "is_admin", False) or getattr(u, "role", "") == "admin" else "[USER]"
            print(f"• {admin_tag} ID: {u.id} | Name: {u.full_name or u.username} | Email: {u.email} | Active: {u.is_active}")
        print("--------------------------------------\n")

async def promote_user(identifier: str):
    clean = identifier.strip().lower()
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(
            or_(
                func.lower(User.email) == clean,
                func.lower(User.full_name) == clean,
                func.lower(User.username) == clean,
            )
        )
        res = await db.execute(stmt)
        user = res.scalars().first()
        if not user:
            print(f"Error: No user found matching '{identifier}'.")
            print("Run 'python make_admin.py --list' to see all registered users.")
            return

        user.is_admin = True
        user.role = "admin"
        await db.commit()
        print(f"SUCCESS: User '{user.full_name or user.username}' ({user.email}) has been granted ADMINISTRATOR privileges.")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print(__doc__)
        return

    arg = sys.argv[1]
    if arg in ("--list", "-l"):
        asyncio.run(list_users())
    else:
        asyncio.run(promote_user(arg))

if __name__ == "__main__":
    main()
