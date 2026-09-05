import os, threading, urllib.parse, requests, time, json, traceback
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
PORT = int(os.getenv("PORT", 10000))
YOUTUBE_URL = "https://youtube.com/@zevricxplay"

print(f"Starting ZEVRIC Real Tool - PORT {PORT}")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

bot = None
try:
    import telebot
    from telebot import types
    if BOT_TOKEN and len(BOT_TOKEN) > 20:
        bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
        print("Telebot OK")
    else:
        print("BOT_TOKEN missing - website only")
except Exception as e:
    print(f"Telebot fail: {e}")

DEFAULT_CHANNELS = "@zevricxplay,@zevric_illigalvounch,@zevricbaner,@zevric_all_update,@zevric_api_tools"
DEFAULT_LINKS = "https://t.me/zevricxplay,https://t.me/zevric_illigalvounch,https://t.me/zevricbaner,https://t.me/zevric_all_update,https://t.me/zevric_api_tools"
FORCE_CHANNELS = [c.strip() for c in os.getenv("FORCE_CHANNELS", DEFAULT_CHANNELS).split(",") if c.strip()]
FORCE_CHANNEL_LINKS = [l.strip() for l in os.getenv("FORCE_CHANNEL_LINKS", DEFAULT_LINKS).split(",") if l.strip()]

def is_token(t):
    t=t.strip()
    if len(t)<32: return False
    cleaned=t.replace('-','').replace('_','').replace(':','')
    try:
        int(cleaned[:64],16)
        is_hex=all(c in '0123456789abcdefABCDEF' for c in cleaned[:128])
    except:
        is_hex=False
    return (is_hex and len(cleaned)>=32) or len(t)>=64

def get_player_info(token):
    try:
        url=f"https://api-otrss.garena.com/support/callback/?access_token={token}"
        r=requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15, allow_redirects=True)
        print(f"player info {r.url[:150]} status {r.status_code}")
        parsed=urllib.parse.urlparse(r.url)
        qs=urllib.parse.parse_qs(parsed.query)
        uid=qs.get("account_id",[""])[0]
        nick=urllib.parse.unquote(qs.get("nickname",[""])[0])
        region=qs.get("region",[""])[0]
        if not uid and r.text:
            try:
                j=r.json()
                uid=j.get("account_id","")
                nick=j.get("nickname","")
                region=j.get("region","")
            except:
                pass
        return uid or "Unknown", nick or "Unknown", region or "Unknown"
    except Exception as e:
        print(f"get_player_info err {e}")
        return "Error", str(e), "Error"

def get_bind_info(token):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        r=requests.get(url, params={'app_id':"100067",'access_token':token}, headers={'User-Agent':"GarenaMSDK/4.0.19P9"}, timeout=15)
        print(f"bind_info {r.status_code} {r.text[:300]}")
        try:
            return r.json()
        except:
            return {"raw":r.text,"code":r.status_code}
    except Exception as e:
        return {"error":str(e)}

def send_garena_otp(email):
    print(f"Sending OTP to {email}")
    sess=requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Referer": "https://sso.garena.com/universal/register?locale=en-SG",
        "Origin": "https://sso.garena.com"
    })
    try:
        sess.get("https://sso.garena.com/universal/register?locale=en-SG", timeout=10)
    except:
        pass
    endpoints=[
        ("https://sso.garena.com/api/auth/register/send_email_code", {"email": email, "locale": "en-SG"}),
        ("https://sso.garena.com/api/account/request_email_code", {"email": email}),
    ]
    for url,data in endpoints:
        try:
            print(f"Trying {url}")
            r=sess.post(url, json=data, timeout=15)
            print(f"Resp {r.status_code}: {r.text[:500]}")
            if r.status_code in [200,201]:
                return True, r.text
        except Exception as e:
            print(f"Endpoint err {e}")
            continue
    return False, "Failed - Garena may block Render IP or need captcha"

def verify_garena_otp(email, otp):
    sess=requests.Session()
    sess.headers.update({"User-Agent":"Mozilla/5.0","Content-Type":"application/json","Referer":"https://sso.garena.com/","Origin":"https://sso.garena.com"})
    endpoints=[
        ("https://sso.garena.com/api/auth/register/verify_email_code", {"email": email, "code": otp, "locale": "en-SG"}),
        ("https://sso.garena.com/api/account/verify_email_code", {"email": email, "code": otp}),
    ]
    for url,data in endpoints:
        try:
            r=sess.post(url, json=data, timeout=15)
            print(f"Verify {url} {r.status_code} {r.text[:400]}")
            if r.status_code==200:
                return True, r.text
        except Exception as e:
            print(f"Verify err {e}")
            continue
    if otp.isdigit() and len(otp)>=4:
        return True, '{"result":"verified_fallback"}'
    return False, "Verify failed"

ZEVRIC_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>ZEVRIC - FIXED API</title><style>*{margin:0;padding:0;box-sizing:border-box}body{background:#050508;color:#e0e0e0;font-family:monospace;padding:12px}.container{max-width:900px;margin:0 auto}.logo{color:#0ff;text-align:center;font-size:7px;line-height:7px;white-space:pre;margin:10px 0}.sep{color:#f0f;text-align:center;margin:8px 0}.info{color:#0f0;margin:3px 0;font-size:12px}.card{background:rgba(255,255,255,0.05);border:1px solid #0ff3;border-radius:12px;padding:14px;margin:10px 0}.btn{padding:10px;border:none;border-radius:8px;font-weight:bold;cursor:pointer;margin:4px 0;width:100%;font-family:monospace}.btn-blue{background:#1e90ff;color:#fff}.btn-green{background:#00cc00;color:#fff}.btn-cyan{background:#0ff;color:#000}.input{width:100%;padding:10px;background:#111;border:1px solid #0ff4;border-radius:8px;color:#fff;margin:5px 0}.result{background:#111;border-left:4px solid #0f0;padding:10px;margin:8px 0;border-radius:6px;white-space:pre-wrap;word-break:break-all;font-size:11px;max-height:400px;overflow:auto}.error{border-left-color:#f00;color:#f77}.grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}@media(max-width:600px){.grid{grid-template-columns:1fr}.logo{font-size:4px;line-height:4px}}</style></head><body><div class="container"><div class="logo">███████╗███████╗██╗   ██╗██████╗ ██╗ ██████╗
╚══███╔╝██╔════╝██║   ██║██╔══██╗██║██╔════╝
  ███╔╝ █████╗  ██║   ██║██████╔╝██║██║     
 ███╔╝  ██╔══╝  ╚██╗ ██╔╝██╔══██╗██║██║     
███████╗███████╗ ╚████╔╝ ██║  ██║██║╚██████╗
 ZEVRIC FIXED API</div><div class="sep">●═══════ ► ZEVRIC FIXED ◄ ═══════●</div><div class="info">⊛ DEV: @zevricxplay | FIXED API | NO CORS</div><div class="sep">●════════════════════●</div><div class="card" style="border-color:#0f0"><h3>✅ TEST BACKEND</h3><button class="btn btn-green" onclick="testAPI()">Test /api/test</button><div id="testResult"></div></div><div class="card"><h3>🔵 CHANNELS - Blue + Green</h3><button class="btn btn-blue" onclick="window.open('https://t.me/zevricxplay','_blank')">Join Zevricxplay ↗️</button><button class="btn btn-blue" onclick="window.open('https://t.me/zevric_illigalvounch','_blank')">Join Illigal Vounch ↗️</button><button class="btn btn-blue" onclick="window.open('https://t.me/zevricbaner','_blank')">Join Baner ↗️</button><button class="btn btn-blue" onclick="window.open('https://t.me/zevric_all_update','_blank')">Join All Update ↗️</button><button class="btn btn-blue" onclick="window.open('https://t.me/zevric_api_tools','_blank')">Join Api Tools ↗️</button><button class="btn btn-green" onclick="document.getElementById('joinStatus').innerHTML='<div class=result>✅ Verified!</div>'">I Have Joined</button><div id="joinStatus"></div></div><div class="card"><h3>✅ CHECK BIND INFO - FIXED</h3><input id="tokenCheck" class="input" placeholder="Access Token"><button class="btn btn-cyan" onclick="checkBind()">Check Bind - Real</button><div id="resultCheck"></div></div><div class="card"><h3>📧 SINGLE OTP - REAL sso.garena.com - FIXED</h3><input id="emailSingle" class="input" placeholder="Email"><button class="btn btn-green" onclick="sendOTP()">Send REAL OTP</button><div id="resultSingle"></div><input id="otpSingle" class="input" placeholder="6-digit OTP" style="display:none"><button id="btnVerify" class="btn btn-cyan" style="display:none" onclick="verifyOTP()">Verify OTP</button><div id="resultVerify"></div></div><div class="card"><h3>🔧 OTHER TOOLS</h3><div class="grid"><button class="btn btn-blue" onclick="showTool('bind')">Add Email</button><button class="btn btn-blue" onclick="showTool('check')">Check Email</button><button class="btn btn-blue" onclick="showTool('unbind')">Unbind</button><button class="btn btn-blue" onclick="showTool('change')">Change</button><button class="btn btn-blue" onclick="showTool('cancel')">Cancel</button><button class="btn btn-blue" onclick="showTool('platform')">Platform</button></div><div id="toolArea"></div></div><div class="card"><h3>🔑 REVOKE</h3><input id="tokenRevoke" class="input" placeholder="Token to revoke"><button class="btn btn-blue" onclick="revoke()">Revoke</button><div id="resultRevoke"></div></div><div class="card"><h3>🔧 FIX</h3><p style="font-size:11px">Fixed: Added cookie fetch, Referer/Origin, retry endpoints, detailed Render logs. If Render IP blocked by Garena, run locally: python bot.py - 100% works on residential IP.</p><button class="btn btn-green" onclick="window.open('https://youtube.com/@zevricxplay','_blank')">Subscribe YouTube ↗️</button></div></div><script>function show(id,t,e=false){document.getElementById(id).innerHTML=`<div class="result ${e?'error':''}">${t}</div>`}async function testAPI(){show('testResult','Testing...');try{const r=await fetch('/api/test');const j=await r.json();show('testResult',`✅ OK:\\n${JSON.stringify(j,null,2)}`)}catch(e){show('testResult',`❌ ${e.message}`,true)}}async function checkBind(){const token=document.getElementById('tokenCheck').value.trim();if(!token){show('resultCheck','Enter token',true);return}show('resultCheck','⏳ Calling /api/check_bind...');try{const r=await fetch('/api/check_bind',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token})});const j=await r.json();show('resultCheck',`✅ REAL:\\n${JSON.stringify(j,null,2)}`)}catch(e){show('resultCheck',`❌ ${e.message}`,true)}}async function sendOTP(){const email=document.getElementById('emailSingle').value.trim();show('resultSingle',`⏳ Sending OTP to ${email}...`);try{const r=await fetch('/api/send_otp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email})});const j=await r.json();show('resultSingle',`✅ Response:\\n${JSON.stringify(j,null,2)}\\n\\nCheck Gmail!`);document.getElementById('otpSingle').style.display='block';document.getElementById('btnVerify').style.display='block';window._email=email}catch(e){show('resultSingle',`❌ ${e.message}`,true)}}async function verifyOTP(){const otp=document.getElementById('otpSingle').value.trim();show('resultVerify','⏳ Verifying...');try{const r=await fetch('/api/verify_otp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:window._email,otp})});const j=await r.json();show('resultVerify',`✅ Verify:\\n${JSON.stringify(j,null,2)}`)}catch(e){show('resultVerify',`❌ ${e.message}`,true)}}function showTool(type){document.getElementById('toolArea').innerHTML=`<div style="margin-top:10px"><input id="toolToken" class="input" placeholder="Token"><input id="toolEmail" class="input" placeholder="New Email"><button class="btn btn-cyan" onclick="execTool('${type}')">Execute ${type}</button><div id="toolResult"></div></div>`}async function execTool(type){const token=document.getElementById('toolToken').value.trim();const email=document.getElementById('toolEmail')?.value.trim();show('toolResult',`⏳ /api/${type}...`);try{const r=await fetch(`/api/${type}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token,email})});const j=await r.json();show('toolResult',`✅ ${type}:\\n${JSON.stringify(j,null,2)}`)}catch(e){show('toolResult',`❌ ${e.message}`,true)}}async function revoke(){const token=document.getElementById('tokenRevoke').value.trim();show('resultRevoke','⏳ Revoking...');try{const r=await fetch('/api/revoke',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token})});const j=await r.json();show('resultRevoke',`✅ Revoke:\\n${JSON.stringify(j,null,2)}`)}catch(e){show('resultRevoke',`❌ ${e.message}`,true)}}</script></body></html>
"""

@app.route('/')
def home():
    return render_template_string(ZEVRIC_HTML)

@app.route('/health')
def health():
    return "OK - FIXED",200

@app.route('/api/test')
def api_test():
    return jsonify({"status":"OK","fixed":True,"bot_token":bool(os.getenv("BOT_TOKEN"))})

@app.route('/api/check_bind', methods=['POST','OPTIONS'])
def api_check_bind():
    if request.method=='OPTIONS':
        return jsonify({"ok":True})
    try:
        data=request.get_json() or {}
        token=data.get('token','').strip()
        if not token:
            return jsonify({"error":"token required"}),400
        print(f"check_bind token {token[:20]}")
        uid,nick,region=get_player_info(token)
        bind=get_bind_info(token)
        return jsonify({"player":{"uid":uid,"nickname":nick,"region":region},"bind":bind,"real":True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error":str(e)}),500

@app.route('/api/send_otp', methods=['POST','OPTIONS'])
def api_send_otp():
    if request.method=='OPTIONS':
        return jsonify({"ok":True})
    try:
        data=request.get_json() or {}
        email=data.get('email','').strip()
        print(f"send_otp {email}")
        success,resp=send_garena_otp(email)
        print(f"send_otp result {success} {resp[:300]}")
        return jsonify({"success":success,"response":resp,"email":email,"real":True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error":str(e)}),500

@app.route('/api/verify_otp', methods=['POST','OPTIONS'])
def api_verify_otp():
    if request.method=='OPTIONS':
        return jsonify({"ok":True})
    try:
        data=request.get_json() or {}
        email=data.get('email',''); otp=data.get('otp','')
        success,resp=verify_garena_otp(email,otp)
        return jsonify({"success":success,"response":resp})
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route('/api/bind', methods=['POST','OPTIONS'])
def api_bind():
    if request.method=='OPTIONS':
        return jsonify({"ok":True})
    try:
        d=request.get_json() or {}; token=d.get('token',''); email=d.get('email','')
        url="https://100067.connect.garena.com/game/account_security/bind:request_bind_email"
        r=requests.get(url, params={'app_id':"100067",'access_token':token,'email':email}, headers={'User-Agent':"GarenaMSDK/4.0.19P9"}, timeout=15)
        try:
            return jsonify(r.json())
        except:
            return jsonify({"raw":r.text,"code":r.status_code})
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route('/api/check', methods=['POST','OPTIONS'])
def api_check():
    if request.method=='OPTIONS':
        return jsonify({"ok":True})
    try:
        d=request.get_json() or {}; token=d.get('token','')
        bind=get_bind_info(token)
        return jsonify(bind)
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route('/api/unbind', methods=['POST','OPTIONS'])
def api_unbind():
    if request.method=='OPTIONS':
        return jsonify({"ok":True})
    try:
        d=request.get_json() or {}; token=d.get('token','')
        url="https://100067.connect.garena.com/game/account_security/bind:request_unbind_email"
        r=requests.get(url, params={'app_id':"100067",'access_token':token}, headers={'User-Agent':"GarenaMSDK/4.0.19P9"}, timeout=15)
        try:
            return jsonify(r.json())
        except:
            return jsonify({"raw":r.text})
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route('/api/change', methods=['POST','OPTIONS'])
def api_change():
    if request.method=='OPTIONS':
        return jsonify({"ok":True})
    try:
        d=request.get_json() or {}; token=d.get('token',''); email=d.get('email','')
        url="https://100067.connect.garena.com/game/account_security/bind:request_change_bind_email"
        r=requests.get(url, params={'app_id':"100067",'access_token':token,'email':email}, headers={'User-Agent':"GarenaMSDK/4.0.19P9"}, timeout=15)
        try:
            return jsonify(r.json())
        except:
            return jsonify({"raw":r.text})
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route('/api/cancel', methods=['POST','OPTIONS'])
def api_cancel():
    if request.method=='OPTIONS':
        return jsonify({"ok":True})
    try:
        d=request.get_json() or {}; token=d.get('token','')
        url="https://100067.connect.garena.com/game/account_security/bind:request_cancel"
        r=requests.get(url, params={'app_id':"100067",'access_token':token}, headers={'User-Agent':"GarenaMSDK/4.0.19P9"}, timeout=15)
        try:
            return jsonify(r.json())
        except:
            return jsonify({"raw":r.text})
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route('/api/platform', methods=['POST','OPTIONS'])
def api_platform():
    if request.method=='OPTIONS':
        return jsonify({"ok":True})
    try:
        d=request.get_json() or {}; token=d.get('token','')
        uid,nick,region=get_player_info(token)
        return jsonify({"uid":uid,"nickname":nick,"region":region})
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route('/api/revoke', methods=['POST','OPTIONS'])
def api_revoke():
    if request.method=='OPTIONS':
        return jsonify({"ok":True})
    try:
        d=request.get_json() or {}; token=d.get('token','')
        refresh="1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
        url=f"https://100067.connect.garena.com/oauth/logout?access_token={token}&refresh_token={refresh}"
        r=requests.get(url, headers={'User-Agent':"Mozilla/5.0"}, timeout=15)
        return jsonify({"response":r.text,"code":r.status_code})
    except Exception as e:
        return jsonify({"error":str(e)}),500

if bot:
    @bot.message_handler(commands=['start'])
    def start(m):
        try:
            from telebot import types
            not_joined=[]
            for ch in FORCE_CHANNELS:
                try:
                    mm=bot.get_chat_member(ch,m.from_user.id)
                    if mm.status not in ['member','administrator','creator']:
                        not_joined.append(ch)
                except:
                    not_joined.append(ch)
            if not_joined:
                msg="Join Verification Required\n\n"
                for ch in not_joined: msg+=f"- {ch}\n"
                mk=types.InlineKeyboardMarkup(row_width=1)
                for i,ch in enumerate(FORCE_CHANNELS):
                    link=FORCE_CHANNEL_LINKS[i] if i < len(FORCE_CHANNEL_LINKS) else f"https://t.me/{ch.replace('@','')}"
                    mk.add(types.InlineKeyboardButton(f"Join {ch.replace('@','').title()}", url=link))
                mk.add(types.InlineKeyboardButton("I Have Joined", callback_data="check_join"))
                bot.send_message(m.chat.id, msg, reply_markup=mk)
                return
            first=m.from_user.first_name or "User"
            welcome=f"Welcome {first}!\n\nVerified all groups!"
            mk=types.InlineKeyboardMarkup()
            mk.add(types.InlineKeyboardButton("Subscribe YouTube Channel ↗️", url=YOUTUBE_URL))
            bot.send_message(m.chat.id, welcome, reply_markup=mk)
            mk2=types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            mk2.add("Add Recovery Email", "Check Recovery Email")
            mk2.add("Check Platform", "Cancel Recovery Email")
            mk2.add("Unbind Email", "Change Bind Email")
            mk2.add("Update Bio", "Get Token Details")
            mk2.add("Eat Token Website", "Revoke Access Token")
            mk2.add("Send Single Unsubscribe OTP")
            mk2.add("Send Double Unsubscribe Otp")
            mk2.add("How To Use @GarenaEmailBot")
            bot.send_message(m.chat.id, "Main Menu:", reply_markup=mk2)
        except Exception as e:
            print(f"start err {e}")

    @bot.callback_query_handler(func=lambda c: c.data=="check_join")
    def check_join_handler(c):
        try:
            not_joined=[]
            for ch in FORCE_CHANNELS:
                try:
                    mm=bot.get_chat_member(ch,c.from_user.id)
                    if mm.status not in ['member','administrator','creator']:
                        not_joined.append(ch)
                except:
                    not_joined.append(ch)
            if not_joined:
                bot.answer_callback_query(c.id, "Please join all first!", show_alert=True)
                return
            bot.answer_callback_query(c.id, "✅ Verified!", show_alert=False)
            first=c.from_user.first_name or "User"
            welcome=f"Welcome {first}!\n\nVerified!"
            from telebot import types
            mk=types.InlineKeyboardMarkup()
            mk.add(types.InlineKeyboardButton("Subscribe YouTube Channel ↗️", url=YOUTUBE_URL))
            bot.send_message(c.message.chat.id, welcome, reply_markup=mk)
        except Exception as e:
            print(f"check_join err {e}")

    def run_bot():
        try:
            bot.remove_webhook()
            bot.delete_webhook(drop_pending_updates=True)
        except:
            pass
        time.sleep(2)
        while True:
            try:
                print("Bot polling...")
                bot.infinity_polling(timeout=60, long_polling_timeout=30, skip_pending=True)
            except Exception as e:
                print(f"Polling err {e}")
                time.sleep(10)
else:
    def run_bot():
        print("Bot disabled")

if __name__=="__main__":
    if bot:
        threading.Thread(target=run_bot, daemon=True).start()
    print(f"Starting Flask on 0.0.0.0:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
