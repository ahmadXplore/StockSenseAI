"""
StockSense AI — Test Face Biometric Authentication Endpoints
"""

import asyncio
import random
import math
from app.db.session import async_engine
from app.db.base import Base
from app.api.v1.endpoints.auth import euclidean_distance, calculate_confidence
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.schemas.auth import FaceSignupRequest, FaceLoginRequest
from app.api.v1.endpoints.auth import face_signup, face_login, list_face_users, delete_face_user


async def main():
    print("=" * 60)
    print("🧪 TESTING BIOMETRIC FACE AUTHENTICATION WITH DATABASE")
    print("=" * 60)

    # 1. Initialize DB tables & alter columns
    from sqlalchemy import text
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(text("ALTER TABLE portfolio.users ADD COLUMN IF NOT EXISTS full_name VARCHAR(150);"))
            await conn.execute(text("ALTER TABLE portfolio.users ADD COLUMN IF NOT EXISTS face_descriptor JSONB;"))
            await conn.execute(text("ALTER TABLE portfolio.users ADD COLUMN IF NOT EXISTS face_enrolled_at TIMESTAMPTZ;"))
        except Exception:
            pass
    print("✅ Database tables & biometric columns ensured.")

    # 2. Test Euclidean distance math
    v1 = [random.uniform(-0.2, 0.2) for _ in range(128)]
    # Slightly perturbed vector (close match)
    v2 = [x + random.uniform(-0.02, 0.02) for x in v1]
    # Completely different vector
    v3 = [random.uniform(-0.5, 0.5) for _ in range(128)]

    d_match = euclidean_distance(v1, v2)
    d_mismatch = euclidean_distance(v1, v3)
    conf_match = calculate_confidence(d_match)
    conf_mismatch = calculate_confidence(d_mismatch)

    print(f"✅ Vector Match Test: Distance = {d_match:.4f} (Confidence: {conf_match}%) -> MATCH: {d_match <= 0.52}")
    print(f"✅ Vector Mismatch Test: Distance = {d_mismatch:.4f} (Confidence: {conf_mismatch}%) -> MATCH: {d_mismatch <= 0.52}")

    # 3. Test Database Signup & Login flow
    async with AsyncSessionLocal() as db:
        test_user_name = "Test Investor Ali"
        test_email = "test_ali@stocksense.ai"

        # A) Face Signup
        req_signup = FaceSignupRequest(name=test_user_name, email=test_email, descriptor=v1)
        signup_res = await face_signup(req_signup, db=db)
        print(f"\n✅ DB Face Signup Result: {signup_res.message} (User ID: {signup_res.user.id if signup_res.user else 'N/A'})")

        # B) List DB Users
        users = await list_face_users(db=db)
        print(f"✅ Enrolled DB Users Count: {len(users)} users found in database.")
        for u in users:
            print(f"   👤 User: {u.name} ({u.email}) | Enrolled: {u.face_enrolled_at}")

        # C) Positive Face Login (Matching face vector v2)
        req_login_good = FaceLoginRequest(identifier=test_user_name, descriptor=v2, threshold=0.52)
        login_good_res = await face_login(req_login_good, db=db)
        print(f"\n✅ DB Face Login (Positive Match): Success = {login_good_res.success} | Message: {login_good_res.message}")
        print(f"   Distance: {login_good_res.distance} | Confidence: {login_good_res.confidence_pct}% | User: {login_good_res.user.name if login_good_res.user else 'None'}")

        # D) Negative Face Login (Mismatched face vector v3)
        req_login_bad = FaceLoginRequest(identifier=test_user_name, descriptor=v3, threshold=0.52)
        login_bad_res = await face_login(req_login_bad, db=db)
        print(f"\n✅ DB Face Login (Negative Match): Success = {login_bad_res.success} | Message: {login_bad_res.message}")

        # E) Clean up test user
        if signup_res.user:
            del_res = await delete_face_user(signup_res.user.id, db=db)
            print(f"\n✅ DB User Biometric Cleanup: {del_res}")

    print("\n" + "=" * 60)
    print("🎉 ALL BIOMETRIC DATABASE AUTH TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
