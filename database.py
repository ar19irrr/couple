import psycopg2
import os
from datetime import datetime, timedelta
import json

# ==================== اتصال به PostgreSQL ====================
def get_db_connection():
    """دریافت اتصال به دیتابیس PostgreSQL"""
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        database=os.environ.get("DB_NAME", "telegram_bot"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", ""),
        port=os.environ.get("DB_PORT", "5432")
    )

def init_db():
    """ایجاد جداول اولیه"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # جدول گروه‌ها
    cur.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            chat_id BIGINT PRIMARY KEY,
            group_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # جدول اعضا
    cur.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            user_id BIGINT,
            user_name TEXT,
            username TEXT,
            gender TEXT,
            interest TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(chat_id, user_id)
        )
    """)
    
    # جدول زوج‌ها
    cur.execute("""
        CREATE TABLE IF NOT EXISTS couples (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            user1_id BIGINT,
            user2_id BIGINT,
            user1_name TEXT,
            user2_name TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # جدول فال‌ها
    cur.execute("""
        CREATE TABLE IF NOT EXISTS faals (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            user_id BIGINT,
            title TEXT,
            interpreter TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ دیتابیس PostgreSQL راه‌اندازی شد.")

# ==================== توابع ====================
def get_groups():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT chat_id, group_name FROM groups")
    groups = [{"id": row[0], "name": row[1] or "گروه ناشناس"} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return groups

def add_group(chat_id, group_name=""):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO groups (chat_id, group_name) VALUES (%s, %s) ON CONFLICT (chat_id) DO NOTHING",
            (chat_id, group_name)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"خطا در افزودن گروه: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def remove_group(chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM groups WHERE chat_id = %s", (chat_id,))
        cur.execute("DELETE FROM members WHERE chat_id = %s", (chat_id,))
        cur.execute("DELETE FROM couples WHERE chat_id = %s", (chat_id,))
        conn.commit()
        return True
    except:
        return False
    finally:
        cur.close()
        conn.close()

def get_members(chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id, user_name, username, gender, interest FROM members WHERE chat_id = %s",
        (chat_id,)
    )
    members = [
        {
            "id": row[0], 
            "name": row[1] or "بدون نام", 
            "username": row[2] or "ندارد",
            "gender": row[3] or "",
            "interest": row[4] or ""
        }
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return members

def set_members(chat_id, members_list):
    conn = get_db_connection()
    cur = conn.cursor()
    for m in members_list:
        cur.execute("""
            INSERT INTO members (chat_id, user_id, user_name, username, gender, interest)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (chat_id, user_id) DO UPDATE SET
                user_name = EXCLUDED.user_name,
                username = EXCLUDED.username
        """, (chat_id, m["id"], m["name"], m["username"], m.get("gender", ""), m.get("interest", "")))
    conn.commit()
    cur.close()
    conn.close()

def set_user_gender(chat_id, user_id, gender):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE members SET gender = %s WHERE chat_id = %s AND user_id = %s",
        (gender, chat_id, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def set_user_interest(chat_id, user_id, interest):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE members SET interest = %s WHERE chat_id = %s AND user_id = %s",
        (interest, chat_id, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def save_couple(chat_id, user1, user2):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO couples (chat_id, user1_id, user2_id, user1_name, user2_name)
        VALUES (%s, %s, %s, %s, %s)
    """, (chat_id, user1["id"], user2["id"], user1["name"], user2["name"]))
    conn.commit()
    cur.close()
    conn.close()

def get_last_couple(chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT user1_id, user2_id, user1_name, user2_name, date
        FROM couples WHERE chat_id = %s
        ORDER BY date DESC LIMIT 1
    """, (chat_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {
            "user1": {"id": row[0], "name": row[2]},
            "user2": {"id": row[1], "name": row[3]},
            "date": row[4].isoformat()
        }
    return None

def get_couple_history(chat_id, limit=10):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT user1_name, user2_name, date
        FROM couples WHERE chat_id = %s
        ORDER BY date DESC LIMIT %s
    """, (chat_id, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"user1": {"name": row[0]}, "user2": {"name": row[1]}, "date": row[2].isoformat()}
        for row in rows
    ]

def get_stats(chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM members WHERE chat_id = %s", (chat_id,))
    total_members = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM couples WHERE chat_id = %s", (chat_id,))
    total_couples = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {
        "total_members": total_members,
        "total_couples": total_couples,
        "unique_users": total_members,
        "last_couple": get_last_couple(chat_id)
    }

def clear_data():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM couples")
    cur.execute("DELETE FROM members")
    cur.execute("DELETE FROM groups")
    conn.commit()
    cur.close()
    conn.close()
    print("✅ دیتابیس پاک شد")

def sync_groups():
    """همگام‌سازی گروه‌ها"""
    return get_groups()

def load_data():
    """بارگذاری دیتابیس (برای سازگاری)"""
    return {"groups": [g["id"] for g in get_groups()]}

def get_global_blocked_users():
    """لیست کاربران بلاک شده"""
    return []

def add_global_blocked_user(user_id):
    return False

def remove_global_blocked_user(user_id):
    return False

def is_user_globally_blocked(user_id):
    return False

def get_user_profile(chat_id, user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT gender, interest FROM members WHERE chat_id = %s AND user_id = %s",
        (chat_id, user_id)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {"gender": row[0] or "", "interest": row[1] or ""}
    return {}

def get_user_couple_stats(chat_id, user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM couples 
        WHERE chat_id = %s AND (user1_id = %s OR user2_id = %s)
    """, (chat_id, user_id, user_id))
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return []

def get_user_total_couples(chat_id, user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM couples 
        WHERE chat_id = %s AND (user1_id = %s OR user2_id = %s)
    """, (chat_id, user_id, user_id))
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total

def update_monthly_score(chat_id, user_id, points=1):
    pass

def get_all_monthly_scores(chat_id):
    return {}

def reset_monthly_scores(chat_id):
    pass

def get_blocked_users(chat_id):
    return []

def clear_blocked_users(chat_id):
    pass

def check_and_reset_blocked(chat_id):
    return False

# ==================== مقداردهی اولیه ====================
init_db()
