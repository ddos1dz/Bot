import telebot
import requests
import json
import time
import threading
import psycopg2
from telebot import types

bot = telebot.TeleBot("7549913156:AAHQDHNq4f0s1E37C_REdRkpAJzjqaeYg2k")

activeDstats = {}

DATABASE_URL = 'postgresql://neondb_owner:npg_vlMeu6RCb8UK@ep-wandering-firefly-a17hrper-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

def initDatabase():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS server_stats (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                username VARCHAR(255),
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                server_id VARCHAR(100) NOT NULL,
                server_name VARCHAR(255) NOT NULL,
                layer VARCHAR(10) NOT NULL,
                category VARCHAR(50) NOT NULL,
                total_requests BIGINT NOT NULL,
                max_rps INTEGER NOT NULL,
                avatar_file_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")

def saveStats(userId, username, firstName, lastName, serverId, serverName, layer, category, totalRequests, maxRps, avatarFileId=None):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute('''
            INSERT INTO server_stats (user_id, username, first_name, last_name, server_id, server_name, layer, category, total_requests, max_rps, avatar_file_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (userId, username, firstName, lastName, serverId, serverName, layer, category, totalRequests, maxRps, avatarFileId))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error saving stats: {e}")

def getRankingData(serverId):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute('''
            SELECT user_id, username, first_name, last_name, total_requests, max_rps, avatar_file_id
            FROM server_stats 
            WHERE server_id = %s 
            ORDER BY total_requests DESC
            LIMIT 20
        ''', (serverId,))
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        return results
    except Exception as e:
        print(f"Error getting ranking data: {e}")
        return []

def formatNumber(num):
    if num >= 1000000000:
        return f"{num/1000000000:.1f}B"
    elif num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(num)

def getServersData():
    headers = {
        "authority": "dstat.space",
        "Accept": "*/*",
        "Accept-Language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
        "Referer": "https://dstat.space/",
        "Sec-Ch-Ua": '"Chromium";v="137", "Not/A)Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?1",
        "Sec-Ch-Ua-Platform": '"Android"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36"
    }
    
    try:
        response = requests.get("https://dstat.space/api/servers", headers=headers)
        return response.json()
    except:
        return None

@bot.message_handler(commands=['home'])
def sendHome(message):
    markup = types.InlineKeyboardMarkup()
    
    rankingBtn = types.InlineKeyboardButton("Ranking", callback_data="ranking")
    layer7Btn = types.InlineKeyboardButton("Layer 7", callback_data="layer7")
    supportBtn = types.InlineKeyboardButton("Support", url="https://t.me/maybe_i_miss_you")
    
    markup.row(rankingBtn)
    markup.row(layer7Btn)
    markup.row(supportBtn)
    
    homeText = """👋 LGBT Count 👋
➖➖➖➖➖➖➖➖➖➖
<a href="https://t.me/deptraiaiyeu">💬 Group Chat</a>"""
    
    bot.send_message(message.chat.id, homeText, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "layer7")
def handleLayerSelection(call):
    if call.from_user.id in activeDstats:
        bot.answer_callback_query(call.id, "Bạn đang thực hiện dstat khác, vui lòng đợi!")
        return
        
    serversData = getServersData()
    if not serversData:
        bot.answer_callback_query(call.id, "Không thể lấy dữ liệu server!")
        return
    
    markup = types.InlineKeyboardMarkup()
    
    massiveBtn = types.InlineKeyboardButton("Massive", callback_data="layer7|massive")
    protectedBtn = types.InlineKeyboardButton("Protected", callback_data="layer7|protected")
    nonProtectedBtn = types.InlineKeyboardButton("Non Protected", callback_data="layer7|non_protected")
    
    markup.row(massiveBtn, protectedBtn, nonProtectedBtn)
    
    backBtn = types.InlineKeyboardButton("⬅️ Back", callback_data="back_home")
    homeBtn = types.InlineKeyboardButton("🏠 Home", callback_data="home")
    markup.row(backBtn, homeBtn)
    
    editText = """🀄 Layer 7 Stats
 
🃏 Select Server Type"""
    
    bot.edit_message_text(editText, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "ranking")
def handleRanking(call):
    markup = types.InlineKeyboardMarkup()
    
    massiveBtn = types.InlineKeyboardButton("Massive", callback_data="ranking|massive")
    protectedBtn = types.InlineKeyboardButton("Protected", callback_data="ranking|protected")
    nonProtectedBtn = types.InlineKeyboardButton("Non Protected", callback_data="ranking|non_protected")
    
    markup.row(massiveBtn, protectedBtn, nonProtectedBtn)
    
    backBtn = types.InlineKeyboardButton("⬅️ Back", callback_data="back_home")
    homeBtn = types.InlineKeyboardButton("🏠 Home", callback_data="home")
    markup.row(backBtn, homeBtn)
    
    editText = """🀄 Layer 7 Ranking

🃏 Select Server Type"""
    
    bot.edit_message_text(editText, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ranking|"))
def handleRankingCategory(call):
    parts = call.data.split("|")
    category = parts[1]
    
    serversData = getServersData()
    if not serversData:
        bot.answer_callback_query(call.id, "Không thể lấy dữ liệu server!")
        return
    
    if "layer7" not in serversData or category not in serversData["layer7"]:
        bot.answer_callback_query(call.id, "Category không tồn tại!")
        return
    
    categoryData = serversData["layer7"][category]
    markup = types.InlineKeyboardMarkup()
    
    for serverId, serverInfo in categoryData["servers"].items():
        serverName = serverInfo["name"]
        capacity = serverInfo["requests"]
        
        btnText = f"{serverName} (~{capacity})"
        btnData = f"ranking_server|{category}|{serverId}"
        btn = types.InlineKeyboardButton(btnText, callback_data=btnData)
        markup.row(btn)
    
    backBtn = types.InlineKeyboardButton("⬅️ Back", callback_data="ranking")
    homeBtn = types.InlineKeyboardButton("🏠 Home", callback_data="home")
    markup.row(backBtn, homeBtn)
    
    editText = f"""🀄 Layer 7 {categoryData["category_name"]} Ranking

🃏 Select Server"""
    
    bot.edit_message_text(editText, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ranking_server|"))
def handleRankingServer(call):
    parts = call.data.split("|")
    category = parts[1]
    serverId = parts[2]
    
    serversData = getServersData()
    if not serversData or "layer7" not in serversData or category not in serversData["layer7"]:
        bot.answer_callback_query(call.id, "Dữ liệu không hợp lệ!")
        return
    
    serverInfo = serversData["layer7"][category]["servers"][serverId]
    serverName = serverInfo["name"]
    capacity = serverInfo["requests"]
    
    rankingData = getRankingData(serverId)
    
    if not rankingData:
        bot.answer_callback_query(call.id, "Không có dữ liệu Ranking cho server này.")
        return
    
    topUser = rankingData[0]
    userId, username, firstName, lastName, totalRequests, maxRps, avatarFileId = topUser
    
    caption = f"""📊 {serverName} (~{capacity})
➖➖➖➖➖➖➖➖"""
    
    markup = types.InlineKeyboardMarkup()
    
    for user in rankingData:
        userIdDb, usernameDb, firstNameDb, lastNameDb, totalReqDb, maxRpsDb, avatarFileIdDb = user
        
        displayName = firstNameDb
        if lastNameDb:
            displayName = f"{firstNameDb} {lastNameDb}"
        
        formattedReq = formatNumber(totalReqDb)
        
        nameBtn = types.InlineKeyboardButton(displayName, callback_data=f"user_{userIdDb}")
        reqBtn = types.InlineKeyboardButton(formattedReq, callback_data=f"req_{totalReqDb}")
        markup.row(nameBtn, reqBtn)
    
    backBtn = types.InlineKeyboardButton("⬅️ Back", callback_data=f"ranking|{category}")
    homeBtn = types.InlineKeyboardButton("🏠 Home", callback_data="home")
    markup.row(backBtn, homeBtn)
    
    if avatarFileId:
        try:
            bot.send_photo(call.message.chat.id, avatarFileId, caption=caption, reply_markup=markup)
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            bot.edit_message_text(caption, call.message.chat.id, call.message.message_id, reply_markup=markup)
    else:
        bot.edit_message_text(caption, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: "|" in call.data and call.data.split("|")[0] == "layer7")
def handleCategorySelection(call):
    if call.from_user.id in activeDstats:
        bot.answer_callback_query(call.id, "Bạn đang thực hiện dstat khác, vui lòng đợi!")
        return
        
    serversData = getServersData()
    if not serversData:
        bot.answer_callback_query(call.id, "Không thể lấy dữ liệu server!")
        return
    
    parts = call.data.split("|")
    layer = parts[0]
    category = parts[1]
    
    if layer not in serversData:
        bot.answer_callback_query(call.id, "Layer không tồn tại!")
        return
        
    if category not in serversData[layer]:
        bot.answer_callback_query(call.id, "Category không tồn tại!")
        return
    
    categoryData = serversData[layer][category]
    markup = types.InlineKeyboardMarkup()
    
    for serverId, serverInfo in categoryData["servers"].items():
        serverName = serverInfo["name"]
        capacity = serverInfo["requests"]
        
        btnText = f"{serverName} (~{capacity})"
        btnData = f"select|{layer}|{category}|{serverId}"
        btn = types.InlineKeyboardButton(btnText, callback_data=btnData)
        markup.row(btn)
    
    backBtn = types.InlineKeyboardButton("⬅️ Back", callback_data=layer)
    homeBtn = types.InlineKeyboardButton("🏠 Home", callback_data="home")
    markup.row(backBtn, homeBtn)
    
    editText = f"""🀄 Layer 7 {categoryData["category_name"]}

🃏 Select Server Type"""
    
    bot.edit_message_text(editText, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select|"))
def handleServerSelection(call):
    if call.from_user.id in activeDstats:
        bot.answer_callback_query(call.id, "Bạn đang thực hiện dstat khác, vui lòng đợi!")
        return
    
    serversData = getServersData()
    if not serversData:
        bot.answer_callback_query(call.id, "Không thể lấy dữ liệu server!")
        return
    
    parts = call.data.split("|")
    layer = parts[1]
    category = parts[2]
    serverId = parts[3]
    
    if layer not in serversData or category not in serversData[layer]:
        bot.answer_callback_query(call.id, "Dữ liệu không hợp lệ!")
        return
    
    serverInfo = serversData[layer][category]["servers"][serverId]
    serverName = serverInfo["name"]
    serverUrl = serverInfo["url"]
    serverDetail = serverInfo["details"]
    capacity = serverInfo["requests"]
    
    startText = f"""📊 {serverName} (~{capacity})
-> Start Statistics
-> Target Adress: {serverUrl}
-> Statistics Duration: 120 Seconds
Detail: {serverDetail}"""
    
    bot.send_message(call.message.chat.id, startText)
    
    initialStatsText = f"""```
📊 {serverName} (~{capacity})
➖➖➖➖➖➖➖➖➖
Peak Requests Per Second: 0
➖➖➖➖➖➖➖➖➖
Total Requests: 0
➖➖➖➖➖➖➖➖➖
🧭 Time Left: 120s
```"""
    
    statsMsg = bot.send_message(call.message.chat.id, initialStatsText, parse_mode='Markdown')
    
    activeDstats[call.from_user.id] = {
        'active': True,
        'message_id': statsMsg.message_id,
        'chat_id': call.message.chat.id
    }
    
    startDstat(call.from_user.id, call.message.chat.id, statsMsg.message_id, serverId, serverName, capacity, layer, category)

def startDstat(userId, chatId, messageId, serverId, serverName, capacity, layer, category):
    totalRequests = 0
    maxRps = 0
    timeLeft = 120
    
    def updateStats():
        nonlocal totalRequests, maxRps, timeLeft
        
        while timeLeft > 0 and userId in activeDstats and activeDstats[userId]['active']:
            try:
                apiUrl = f"https://dstat.space/api/layer7/{serverId}"
                headers = {
                    "Referer": f"https://dstat.space/l7?id={serverId}",
                    "Origin": "https://dstat.space",
                    "User-Agent": "Mozilla/5.0"
                }
                
                response = requests.get(apiUrl, headers=headers)
                data = response.json()
                
                if "data" in data and len(data["data"]) > 0:
                    currentRequests = int(data["data"][0])
                    totalRequests += currentRequests
                    currentRps = currentRequests // 5
                    
                    if currentRps > maxRps:
                        maxRps = currentRps
                
                updatedText = f"""```
📊 {serverName} (~{capacity})
➖➖➖➖➖➖➖➖➖
Peak Requests Per Second: {maxRps}
➖➖➖➖➖➖➖➖➖
Total Requests: {totalRequests}
➖➖➖➖➖➖➖➖➖
🧭 Time Left: {timeLeft}s
```"""
                
                bot.edit_message_text(updatedText, chatId, messageId, parse_mode='Markdown')
                
            except Exception as e:
                print(f"Error updating stats: {e}")
            
            time.sleep(5)
            timeLeft -= 5
        
        if userId in activeDstats:
            bot.delete_message(chatId, messageId)
            
            finalText = f"""```
📊 {serverName} (~{capacity}) Dstat Ended
➖➖➖➖➖➖➖➖➖➖➖➖➖➖
Total Requests: {totalRequests}
➖➖➖➖➖➖➖➖➖➖➖➖➖➖
Max Requests Per Second: {maxRps}
➖➖➖➖➖➖➖➖➖➖➖➖➖➖
```"""
            
            bot.send_message(chatId, finalText, parse_mode='Markdown')
            
            try:
                user = bot.get_chat_member(chatId, userId).user
                firstName = user.first_name
                lastName = user.last_name
                username = user.username
                
                avatarFileId = None
                try:
                    photos = bot.get_user_profile_photos(userId, limit=1)
                    if photos.total_count > 0:
                        avatarFileId = photos.photos[0][-1].file_id
                except:
                    pass
                
                saveStats(userId, username, firstName, lastName, serverId, serverName, layer, category, totalRequests, maxRps, avatarFileId)
                
                if lastName:
                    fullName = f"{firstName} {lastName}"
                else:
                    fullName = firstName
                    
                sourceText = f"🎯 Data Source: {fullName}[tg://user?id={userId}]"
                bot.send_message(chatId, sourceText, parse_mode='Markdown')
            except:
                pass
            
            del activeDstats[userId]
    
    thread = threading.Thread(target=updateStats)
    thread.daemon = True
    thread.start()

@bot.callback_query_handler(func=lambda call: call.data in ["home", "back_home"])
def handleHomeNavigation(call):
    markup = types.InlineKeyboardMarkup()
    
    rankingBtn = types.InlineKeyboardButton("Ranking", callback_data="ranking")
    layer7Btn = types.InlineKeyboardButton("Layer 7", callback_data="layer7")
    supportBtn = types.InlineKeyboardButton("Support", url="https://t.me/maybe_i_miss_you")
    
    markup.row(rankingBtn)
    markup.row(layer7Btn)
    markup.row(supportBtn)
    
    homeText = """👋 LGBT Count 👋
➖➖➖➖➖➖➖➖➖➖
<a href="https://t.me/deptraiaiyeu">💬 Group Chat</a>"""
    
    bot.edit_message_text(homeText, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_") or call.data.startswith("req_"))
def handleUserClick(call):
    bot.answer_callback_query(call.id)

if __name__ == "__main__":
    initDatabase()
    print("Bot started...")
    bot.infinity_polling()
