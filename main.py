import os
import re
import sqlite3
import threading
import time
from flask import Flask
import telebot

# -------------------------------------------------------------
# 1. FLASK WEB SERVER (Render မအိပ်ဘဲ 24/7 Run နေစေရန်)
# -------------------------------------------------------------
app = Flask("")


@app.route("/")
def home():
    return "Bot is Live and Running 24/7!"


def run_flask():
    try:
        port = int(os.environ.get("PORT", 8080))
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask Server Error: {e}")


def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()


# -------------------------------------------------------------
# 2. BOT CONFIGURATION & DATABASE
# -------------------------------------------------------------
API_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(API_TOKEN, threaded=True, num_threads=10)
DB_PATH = "data.db"

# Owner ID
OWNER_ID = 6767500672


def db(q, p=()):
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(q, p)
        res = c.fetchall()
        conn.commit()
        conn.close()
        return res
    except Exception as e:
        print(f"Database Error: {e}")
        return []


# Database Tables Initialization
db(
    "CREATE TABLE IF NOT EXISTS memory (q TEXT PRIMARY KEY, a TEXT, is_sticker"
    " INTEGER DEFAULT 0)"
)
db("CREATE TABLE IF NOT EXISTS bl (word TEXT PRIMARY KEY)")
db(
    "CREATE TABLE IF NOT EXISTS members (chat_id INTEGER, user_id INTEGER, name"
    " TEXT, PRIMARY KEY(chat_id, user_id))"
)
db("CREATE TABLE IF NOT EXISTS groups (chat_id INTEGER PRIMARY KEY)")
db(
    "CREATE TABLE IF NOT EXISTS warns (chat_id INTEGER, user_id INTEGER, count"
    " INTEGER, PRIMARY KEY(chat_id, user_id))"
)
db(
    "CREATE TABLE IF NOT EXISTS settings (chat_id INTEGER PRIMARY KEY, rules"
    " TEXT, welcome TEXT)"
)


# Helper Functions
def is_admin(m):
    try:
        return bot.get_chat_member(m.chat.id, m.from_user.id).status in [
            "creator",
            "administrator",
        ]
    except:
        return False


def typing_effect(chat_id, reply_to_id, full_text):
    try:
        msg = bot.send_message(
            chat_id, full_text[0], reply_to_message_id=reply_to_id
        )
        current_text = full_text[0]
        step = 3
        for i in range(1, len(full_text), step):
            current_text += full_text[i : i + step]
            try:
                bot.edit_message_text(current_text, chat_id, msg.message_id)
                time.sleep(0.2)
            except:
                pass
        if current_text != full_text:
            try:
                bot.edit_message_text(full_text, chat_id, msg.message_id)
            except:
                pass
    except:
        try:
            bot.send_message(chat_id, full_text, reply_to_message_id=reply_to_id)
        except:
            pass


# -------------------------------------------------------------
# 3. TELEGRAM BOT HANDLERS
# -------------------------------------------------------------
@bot.message_handler(commands=["start", "help"])
def start_cmd(m):
    if m.chat.type == "private":
        cmds_text = (
            "📌 **Available Commands:**\n\n"
            "▫️ /id - Target Id View\n"
            "▫️ /promote - Promote user to Admin (Reply)\n"
            "▫️ /demote - Remove Admin status (Reply)\n"
            "▫️ /mute [time] [reason] - Mute User (Reply)\n"
            "▫️ /unmute - Mute release (Reply)\n"
            "▫️ /kick - Kick user from group (Reply)\n"
            "▫ /ban - Ban user from group (Reply)\n"
            "▫️ /warn - Warning 3 times auto mute (Reply)\n"
            "▫️ /rules - View Group Rules\n"
            "▫️ /setrules - Set Group Rules (Admin)\n"
            "▫️ /setwelcome - Set Welcome Message (Admin)\n"
            "▫️ /addbadword - Add bad word to filter list (Admin)\n"
            "▫️ /delbadword - Remove bad word from list (Admin)\n"
            "▫️ /badwords - View bad word list (Admin)\n"
            "▫️ /status - Bot Statistics (Everyone)"
        )
        threading.Thread(
            target=typing_effect, args=(m.chat.id, m.message_id, cmds_text)
        ).start()
    else:
        threading.Thread(
            target=typing_effect,
            args=(m.chat.id, m.message_id, "Hello My Friend 👋"),
        ).start()


@bot.message_handler(commands=["id"])
def get_id(m):
    try:
        if m.reply_to_message:
            target = m.reply_to_message.from_user
            bot.reply_to(
                m,
                f"👤 Name: {target.first_name}\n🆔 User ID: `{target.id}`",
                parse_mode="Markdown",
            )
        else:
            bot.reply_to(
                m,
                f"👥 Chat ID: `{m.chat.id}`\n👤 Your ID: `{m.from_user.id}`",
                parse_mode="Markdown",
            )
    except:
        pass


@bot.message_handler(commands=["status"])
def status_cmd(m):
    g = len(db("SELECT * FROM groups"))
    u = len(db("SELECT DISTINCT user_id FROM members"))
    bot.reply_to(
        m,
        f"📊 **Bot Statistics:**\n\n👥 Total Users: {u}\n🏠 Total Groups: {g}",
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["promote", "demote"])
def admin_promote_demote(m):
    if is_admin(m) and m.reply_to_message:
        uid = m.reply_to_message.from_user.id
        try:
            if "promote" in m.text:
                bot.promote_chat_member(
                    m.chat.id,
                    uid,
                    can_change_info=True,
                    can_delete_messages=True,
                    can_invite_users=True,
                    can_restrict_members=True,
                    can_pin_messages=True,
                    can_manage_video_chats=True,
                )
                bot.reply_to(
                    m,
                    f"✅ **{m.reply_to_message.from_user.first_name}** is now"
                    " an Admin!",
                )
            elif "demote" in m.text:
                bot.promote_chat_member(
                    m.chat.id,
                    uid,
                    can_change_info=False,
                    can_post_messages=False,
                    can_edit_messages=False,
                    can_delete_messages=False,
                    can_invite_users=False,
                    can_restrict_members=False,
                    can_pin_messages=False,
                    can_promote_members=False,
                    can_manage_video_chats=False,
                )
                bot.reply_to(
                    m,
                    "❌ Admin privileges removed for"
                    f" **{m.reply_to_message.from_user.first_name}**.",
                )
        except Exception as e:
            bot.reply_to(m, f"❌ Error: {e}")


@bot.message_handler(commands=["broadcast"])
def bc(m):
    if m.from_user.id != OWNER_ID:
        return

    if m.reply_to_message:
        for row in db("SELECT chat_id FROM groups"):
            try:
                bot.forward_message(
                    row[0], m.chat.id, m.reply_to_message.message_id
                )
            except:
                pass
        bot.reply_to(m, "Broadcast (Forwarded) done.")
    else:
        txt = m.text.replace("/broadcast", "").strip()
        if txt:
            for row in db("SELECT chat_id FROM groups"):
                try:
                    bot.send_message(row[0], txt)
                except:
                    pass
            bot.reply_to(m, "Broadcast done.")


@bot.message_handler(commands=["mute", "unmute", "kick", "ban"])
def admin_acts(m):
    if is_admin(m) and m.reply_to_message:
        uid = m.reply_to_message.from_user.id
        try:
            if "unmute" in m.text:
                bot.restrict_chat_member(
                    m.chat.id,
                    uid,
                    permissions=telebot.types.ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_other_messages=True,
                    ),
                )
                bot.reply_to(m, "✅ Unmuted.")
            elif "kick" in m.text:
                bot.ban_chat_member(m.chat.id, uid)
                bot.unban_chat_member(m.chat.id, uid)
                bot.reply_to(m, "👢 Kicked.")
            elif "ban" in m.text:
                bot.ban_chat_member(m.chat.id, uid)
                bot.unban_chat_member(m.chat.id, uid)
                bot.reply_to(m, "🚫 Banned.")
            elif "mute" in m.text:
                args = m.text.split()
                until_time = 0
                reason = "No reason provided"

                if len(args) > 1:
                    time_str = args[1]
                    unit = time_str[-1].lower()
                    if unit in ["m", "h", "d"] and time_str[:-1].isdigit():
                        val = int(time_str[:-1])
                        if unit == "m":
                            until_time = int(time.time() + val * 60)
                        elif unit == "h":
                            until_time = int(time.time() + val * 3600)
                        elif unit == "d":
                            until_time = int(time.time() + val * 86400)
                        if len(args) > 2:
                            reason = " ".join(args[2:])
                    else:
                        reason = " ".join(args[1:])

                bot.restrict_chat_member(
                    m.chat.id,
                    uid,
                    permissions=telebot.types.ChatPermissions(
                        can_send_messages=False,
                        can_send_media_messages=False,
                        can_send_other_messages=False,
                    ),
                    until_date=(
                        until_time
                        if until_time > 0
                        else int(time.time() + 31536000)
                    ),
                )

                duration = (
                    args[1]
                    if (until_time > 0 and len(args) > 1)
                    else "Forever (Until Unmuted)"
                )
                bot.reply_to(
                    m,
                    "🔇 **Muted**\n\n👤 **User:**"
                    f" {m.reply_to_message.from_user.first_name}\n⏳ **Duration:**"
                    f" {duration}\n📝 **Reason:** {reason}",
                    parse_mode="Markdown",
                )
        except Exception as e:
            bot.reply_to(m, f"❌ Admin Error: {e}")


@bot.message_handler(commands=["pin", "unpin"])
def pin_acts(m):
    if is_admin(m):
        try:
            if "unpin" in m.text:
                bot.unpin_chat_message(m.chat.id)
            elif m.reply_to_message:
                bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id)
            bot.reply_to(m, "Done.")
        except:
            pass


@bot.message_handler(commands=["warn"])
def warn_user(m):
    if is_admin(m) and m.reply_to_message:
        uid = m.reply_to_message.from_user.id
        try:
            res = db(
                "SELECT count FROM warns WHERE chat_id=? AND user_id=?",
                (m.chat.id, uid),
            )
            count = (res[0][0] if res else 0) + 1
            if count >= 3:
                bot.restrict_chat_member(
                    m.chat.id,
                    uid,
                    permissions=telebot.types.ChatPermissions(
                        can_send_messages=False,
                        can_send_media_messages=False,
                        can_send_other_messages=False,
                    ),
                    until_date=int(time.time() + 86400),
                )
                db(
                    "DELETE FROM warns WHERE chat_id=? AND user_id=?",
                    (m.chat.id, uid),
                )
                bot.reply_to(m, "🔇 Auto Muted 24 Hours (3/3 Warns).")
            else:
                db(
                    "INSERT OR REPLACE INTO warns VALUES (?,?,?)",
                    (m.chat.id, uid, count),
                )
                bot.reply_to(m, f"⚠️ Warned ({count}/3)")
        except Exception as e:
            bot.reply_to(m, f"❌ Error: {e}")


@bot.message_handler(commands=["setrules"])
def set_rules(m):
    if is_admin(m):
        txt = m.text.replace("/setrules", "").strip()
        if txt:
            db(
                "INSERT INTO settings (chat_id, rules) VALUES (?, ?) ON"
                " CONFLICT(chat_id) DO UPDATE SET rules=excluded.rules",
                (m.chat.id, txt),
            )
            bot.reply_to(m, "✅ Rules Saved.")


@bot.message_handler(commands=["rules"])
def view_rules(m):
    res = db("SELECT rules FROM settings WHERE chat_id=?", (m.chat.id,))
    if res and res[0][0]:
        bot.reply_to(m, f"📋 **Group Rules:**\n\n{res[0][0]}")
    else:
        bot.reply_to(m, "❌ No rules set for this group yet.")


@bot.message_handler(commands=["setwelcome"])
def set_welcome(m):
    if is_admin(m):
        txt = m.text.replace("/setwelcome", "").strip()
        if txt:
            db(
                "INSERT INTO settings (chat_id, welcome) VALUES (?, ?) ON"
                " CONFLICT(chat_id) DO UPDATE SET welcome=excluded.welcome",
                (m.chat.id, txt),
            )
            bot.reply_to(m, "✅ Welcome Message Saved.")


# -------------------------------------------------------------
# BAD WORD FILTER COMMANDS
# -------------------------------------------------------------

# 1. မိုက်ရိုင်းသော စကားလုံး Add ရန် (/addbadword သို့မဟုတ် /filter)
@bot.message_handler(commands=["addbadword", "filter"])
def add_filters(m):
    if is_admin(m):
        # command အလိုက် သန့်ရှင်းပေးခြင်း
        txt = m.text
        for c in ["/addbadword", "/filter"]:
            txt = txt.replace(c, "")
        w = txt.strip().lower()
        if w:
            db("INSERT OR REPLACE INTO bl VALUES (?)", (w,))
            bot.reply_to(m, f"✅ Added '{w}' to Filter list.")
        else:
            bot.reply_to(m, "❌ Usage: `/addbadword [စကားလုံး]`", parse_mode="Markdown")


# 2. မိုက်ရိုင်းသော စကားလုံး ပြန်ထုတ်ရန် (/delbadword)
@bot.message_handler(commands=["delbadword"])
def del_filters(m):
    if is_admin(m):
        w = m.text.replace("/delbadword", "").strip().lower()
        if w:
            db("DELETE FROM bl WHERE word=?", (w,))
            bot.reply_to(m, f"🗑 Removed '{w}' from Filter list.")
        else:
            bot.reply_to(m, "❌ Usage: `/delbadword [စကားလုံး]`", parse_mode="Markdown")


# 3. သတ်မှတ်ထားသော စကားလုံးများကြည့်ရန် (/badwords)
@bot.message_handler(commands=["badwords"])
def list_badwords(m):
    if is_admin(m):
        rows = db("SELECT word FROM bl")
        if rows:
            words = "\n".join([f"• {r[0]}" for r in rows])
            bot.reply_to(m, f"🚫 **Bad Word List:**\n\n{words}", parse_mode="Markdown")
        else:
            bot.reply_to(m, "ℹ️ No bad words added yet.")


# -------------------------------------------------------------
# MAIN MESSAGE HANDLER
# -------------------------------------------------------------
@bot.message_handler(
    func=lambda m: True,
    content_types=[
        "text",
        "sticker",
        "new_chat_members",
        "left_chat_member",
    ],
)
def auto_handlers(m):
    if m.chat.type != "private":
        db("INSERT OR REPLACE INTO groups VALUES (?)", (m.chat.id,))
        if m.from_user and not m.from_user.is_bot:
            db(
                "INSERT OR REPLACE INTO members VALUES (?,?,?)",
                (m.chat.id, m.from_user.id, m.from_user.first_name),
            )
    else:
        if m.from_user and not m.from_user.is_bot:
            db(
                "INSERT OR REPLACE INTO members VALUES (?,?,?)",
                (m.chat.id, m.from_user.id, m.from_user.first_name),
            )

    if m.content_type == "new_chat_members":
        res = db("SELECT welcome FROM settings WHERE chat_id=?", (m.chat.id,))
        w_text = (
            res[0][0]
            if res and res[0][0]
            else "Welcome {name} to our group! 🎉"
        )
        for new_user in m.new_chat_members:
            if not new_user.is_bot:
                formatted_text = w_text.replace("{name}", new_user.first_name)
                bot.send_message(m.chat.id, formatted_text)
        return

    if m.content_type == "left_chat_member":
        if not m.left_chat_member.is_bot:
            bot.send_message(
                m.chat.id, f"Goodbye {m.left_chat_member.first_name}! 👋"
            )
        return

    # Anti-Link & Anti-Badwords Filter (Admin မဟုတ်ပါက စာဖျက်မည်)
    if m.content_type == "text" and m.chat.type != "private":
        txt = m.text.strip()
        
        if not is_admin(m):
            # 1. Link Filter
            link_pattern = r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+|@[a-zA-Z0-9_]+)"
            if re.search(link_pattern, txt, re.IGNORECASE):
                try:
                    bot.delete_message(m.chat.id, m.message_id)
                    return
                except:
                    pass

            # 2. Bad Words Filter
            for row in db("SELECT word FROM bl"):
                if row[0] and row[0] in txt.lower():
                    try:
                        bot.delete_message(m.chat.id, m.message_id)
                        return
                    except:
                        pass

    # Bot Auto Reply Memory System
    if m.reply_to_message and not m.from_user.is_bot:
        if m.reply_to_message.content_type == "text":
            q_text = m.reply_to_message.text.strip().lower()
            if q_text and not q_text.startswith("/"):
                if m.content_type == "sticker":
                    db(
                        "INSERT OR REPLACE INTO memory VALUES (?,?,1)",
                        (q_text, m.sticker.file_id),
                    )
                elif m.content_type == "text":
                    a_text = m.text.strip()
                    if a_text and not a_text.startswith("/"):
                        db(
                            "INSERT OR REPLACE INTO memory VALUES (?,?,0)",
                            (q_text, a_text),
                        )

    if m.content_type != "text":
        return
    txt = m.text.strip()

    res = db("SELECT a, is_sticker FROM memory WHERE q=?", (txt.lower(),))
    if res:
        if res[0][1] == 1:
            bot.send_sticker(
                m.chat.id, res[0][0], reply_to_message_id=m.message_id
            )
        else:
            bot.reply_to(m, res[0][0])
        return


# -------------------------------------------------------------
# 4. MAIN EXECUTION
# -------------------------------------------------------------
if __name__ == "__main__":
    keep_alive()

    try:
        bot.delete_webhook(drop_pending_updates=True)
    except:
        pass

    print("Bot starting polling...")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)
      
