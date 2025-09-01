import telebot
import requests
import json
import time
import threading
import psycopg2
from telebot import types

bot = telebot.TeleBot("7549913156:AAHQDHNq4f0s1E37C_REdRkpAJzjqaeYg2k")

activeDstats = {}

DATABASE_URL = "postgresql://neondb_owner:npg_vlMeu6RCb8UK@ep-wandering-firefly-a17hrper-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def initDatabase():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rankings (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                username VARCHAR(255),
                full_name VARCHAR(255),
                server_id VARCHAR(100),
                server_name VARCHAR(255),
                layer VARCHAR(10),
                category VARCHAR(50),
                total_requests BIGINT,
                max_rps INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database init error: {e}")

def saveRanking(userId, username, fullName, serverId, serverName, layer, category, totalRequests, maxRps):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO rankings (user_id, username, full_name, server_id, server_name, layer, category, total_requests, max_rps)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (userId, username, fullName, serverId, serverName, layer, category, totalRequests, maxRps))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Save ranking error: {e}")

def getRankings(serverId):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT full_name, total_requests, max_rps
            FROM rankings
            WHERE server_id = %s
            ORDER BY total_requests DESC
            LIMIT 10
        """, (serverId,))
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        return results
    except Exception as e:
        print(f"Get rankings error: {e}")
        return []

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
    layer4Btn = types.InlineKeyboardButton("Layer 4", callback_data="layer4")
    layer7Btn = types.InlineKeyboardButton("Layer 7", callback_data="layer7")
    supportBtn = types.InlineKeyboardButton("Support", url="https://t.me/maybe_i_miss_you")
    
    markup.row(rankingBtn)
    markup.row(layer4Btn, layer7Btn)
    markup.row(supportBtn)
    
    homeText = """👋 LGBT Count 👋
➖➖➖➖➖➖➖➖➖➖
<a href="https://t.me/deptraiaiyeu">💬 Group Chat</a>"""
    
    bot.send_message(message.chat.id, homeText, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data in ["layer4", "layer7"])
def handleLayerSelection(call):
    serversData = getServersData()
    if not serversData:
        bot.answer_callback_query(call.id, "Không thể lấy dữ liệu server!")
        return
    
    layer = call.data
    markup = types.InlineKeyboardMarkup()
    
    massiveBtn = types.InlineKeyboardButton("Massive", callback_data=f"{layer}_massive")
    protectedBtn = types.InlineKeyboardButton("Protected", callback_data=f"{layer}_protected")
    nonProtectedBtn = types.InlineKeyboardButton("Non Protected", callback_data=f"{layer}_non_protected")
    
    markup.row(massiveBtn, protectedBtn, nonProtectedBtn)
    
    backBtn = types.InlineKeyboardButton("⬅️ Back", callback_data="back_home")
    homeBtn = types.InlineKeyboardButton("🏠 Home", callback_data="home")
    markup.row(backBtn, homeBtn)
    
    layerNum = layer[-1]
    editText = f"""🀄 Layer {layerNum} Stats
 
🃏 Select Server Type"""
    
    bot.edit_message_text(editText, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: "_" in call.data and call.data.split("_")[0] in ["layer4", "layer7"] and not call.data.startswith("select_"))
def handleCategorySelection(call):
    serversData = getServersData()
    if not serversData:
        bot.answer_callback_query(call.id, "Không thể lấy dữ liệu server!")
        return
    
    parts = call.data.split("_")
    layer = parts[0]
    category = parts[1]
    
    if category == "non":
        category = "non_protected"
    
    layerNum = layer[-1]
    categoryData = serversData[layer][category]
    
    markup = types.InlineKeyboardMarkup()
    
    for serverId, serverInfo in categoryData["servers"].items():
        serverName = serverInfo["name"]
        if layer == "layer7":
            capacity = serverInfo["requests"]
        else:
            capacity = serverInfo["bandwidth"]
        
        btnText = f"{serverName} (~{capacity})"
        btnData = f"select_{layer}_{category}_{serverId}"
        btn = types.InlineKeyboardButton(btnText, callback_data=btnData)
        markup.row(btn)
    
    backBtn = types.InlineKeyboardButton("⬅️ Back", callback_data=layer)
    homeBtn = types.InlineKeyboardButton("🏠 Home", callback_data="home")
    markup.row(backBtn, homeBtn)
    
    editText = f"""🀄 Layer {layerNum} {categoryData["category_name"]}

🃏 Select Server Type"""
    
    bot.edit_message_text(editText, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def handleServerSelection(call):
    if call.from_user.id in activeDstats:
        bot.answer_callback_query(call.id, "Bạn đang thực hiện dstat khác, vui lòng đợi!")
        return
    
    serversData = getServersData()
    if not serversData:
        bot.answer_callback_query(call.id, "Không thể lấy dữ liệu server!")
        return
    
    parts = call.data.split("_")
    layer = parts[1]
    category = parts[2]
    serverId = parts[3]
    
    serverInfo = serversData[layer][category]["servers"][serverId]
    serverName = serverInfo["name"]
    serverUrl = serverInfo["url"]
    serverDetail = serverInfo["details"]
    
    if layer == "layer7":
        capacity = serverInfo["requests"]
    else:
        capacity = serverInfo["bandwidth"]
    
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
                if layer == "layer7":
                    apiUrl = f"https://dstat.space/api/layer7/{serverId}"
                    headers = {
                        "Referer": f"https://dstat.space/l7?id={serverId}",
                        "Origin": "https://dstat.space",
                        "User-Agent": "Mozilla/5.0"
                    }
                else:
                    apiUrl = f"https://dstat.space/api/layer4/{serverId}"
                    headers = {
                        "Referer": f"https://dstat.space/l4?id={serverId}",
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
                username = user.username if user.username else ""
                if user.last_name:
                    fullName = f"{firstName} {user.last_name}"
                else:
                    fullName = firstName
                    
                saveRanking(userId, username, fullName, serverId, serverName, layer, category, totalRequests, maxRps)
                    
                sourceText = f"🎯 Data Source: {fullName}[tg://user?id={userId}]"
                bot.send_message(chatId, sourceText, parse_mode='Markdown')
            except:
                pass
            
            del activeDstats[userId]
    
    thread = threading.Thread(target=updateStats)
    thread.daemon = True
    thread.start()

@bot.callback_query_handler(func=lambda call: call.data == "ranking")
def handleRanking(call):
    serversData = getServersData()
    if not serversData:
        bot.answer_callback_query(call.id, "Không thể lấy dữ liệu server!")
        return
    
    markup = types.InlineKeyboardMarkup()
    
    layer7MassiveBtn = types.InlineKeyboardButton("Layer 7 Massive", callback_data="rank_layer7_massive")
    layer7ProtectedBtn = types.InlineKeyboardButton("Layer 7 Protected", callback_data="rank_layer7_protected")
    layer7NonProtectedBtn = types.InlineKeyboardButton("Layer 7 Non Protected", callback_data="rank_layer7_non_protected")
    
    layer4MassiveBtn = types.InlineKeyboardButton("Layer 4 Massive", callback_data="rank_layer4_massive")
    layer4ProtectedBtn = types.InlineKeyboardButton("Layer 4 Protected", callback_data="rank_layer4_protected")
    layer4NonProtectedBtn = types.InlineKeyboardButton("Layer 4 Non Protected", callback_data="rank_layer4_non_protected")
    
    markup.row(layer7MassiveBtn)
    markup.row(layer7ProtectedBtn)
    markup.row(layer7NonProtectedBtn)
    markup.row(layer4MassiveBtn)
    markup.row(layer4ProtectedBtn)
    markup.row(layer4NonProtectedBtn)
    
    backBtn = types.InlineKeyboardButton("⬅️ Back", callback_data="back_home")
    homeBtn = types.InlineKeyboardButton("🏠 Home", callback_data="home")
    markup.row(backBtn, homeBtn)
    
    editText = """🀄 Ranking Stats
 
🃏 Select Category"""
    
    bot.edit_message_text(editText, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rank_"))
def handleRankingCategory(call):
    serversData = getServersData()
    if not serversData:
        bot.answer_callback_query(call.id, "Không thể lấy dữ liệu server!")
        return
    
    parts = call.data.split("_")
    layer = parts[1]
    category = parts[2]
    
    if category == "non":
        category = "non_protected"
    
    layerNum = layer[-1]
    categoryData = serversData[layer][category]
    
    markup = types.InlineKeyboardMarkup()
    
    for serverId, serverInfo in categoryData["servers"].items():
        serverName = serverInfo["name"]
        btnText = f"{serverName}"
        btnData = f"show_rank_{serverId}_{serverName}"
        btn = types.InlineKeyboardButton(btnText, callback_data=btnData)
        markup.row(btn)
    
    backBtn = types.InlineKeyboardButton("⬅️ Back", callback_data="ranking")
    homeBtn = types.InlineKeyboardButton("🏠 Home", callback_data="home")
    markup.row(backBtn, homeBtn)
    
    editText = f"""🀄 Layer {layerNum} {categoryData["category_name"]} Ranking

🃏 Select Server Type"""
    
    bot.edit_message_text(editText, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("show_rank_"))
def handleShowRanking(call):
    parts = call.data.split("_", 2)
    serverId = parts[2]
    serverName = parts[3] if len(parts) > 3 else serverId
    
    rankings = getRankings(serverId)
    
    if not rankings:
        bot.answer_callback_query(call.id, f"Chưa có dữ liệu ranking cho {serverName}!")
        return
    
    rankingText = f"🏆 Ranking For Server {serverName}\n\n"
    
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, (fullName, totalRequests, maxRps) in enumerate(rankings):
        if i < 10:
            emoji = emojis[i]
            rankingText += f"{emoji} {fullName} {totalRequests}\n"
    
    bot.send_message(call.message.chat.id, rankingText)

@bot.callback_query_handler(func=lambda call: call.data in ["home", "back_home"])
def handleHomeNavigation(call):
    markup = types.InlineKeyboardMarkup()
    
    rankingBtn = types.InlineKeyboardButton("Ranking", callback_data="ranking")
    layer4Btn = types.InlineKeyboardButton("Layer 4", callback_data="layer4")
    layer7Btn = types.InlineKeyboardButton("Layer 7", callback_data="layer7")
    supportBtn = types.InlineKeyboardButton("Support", url="https://t.me/maybe_i_miss_you")
    
    markup.row(rankingBtn)
    markup.row(layer4Btn, layer7Btn)
    markup.row(supportBtn)
    
    homeText = """👋 LGBT Count 👋
➖➖➖➖➖➖➖➖➖➖
<a href="https://t.me/deptraiaiyeu">💬 Group Chat</a>"""
    
    bot.edit_message_text(homeText, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')

if __name__ == "__main__":
    initDatabase()
    print("Bot started...")
    bot.infinity_polling()
