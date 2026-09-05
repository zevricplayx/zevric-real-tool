
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests, urllib.parse, os

app = Flask(__name__, static_folder='.')
CORS(app, allow_headers=["Content-Type"])

HEADERS = {
    'User-Agent': 'GarenaMSDK/4.0.30',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip'
}
HEADERS_HTML = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def convert_seconds(s):
    try:
        s = int(s)
    except:
        return "0 Day 0 Hour 0 Min 0 Sec"
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d} Day {h} Hour {m} Min {s} Sec"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/check', methods=['GET'])
def api_check():
    token = request.args.get('access_token','').strip()
    if not token:
        return jsonify({'error':'token missing'}), 400
    result = {}
    # 1. Player info via otrss
    try:
        url = f'https://api-otrss.garena.com/support/callback/?access_token={token}'
        r = requests.get(url, headers=HEADERS_HTML, allow_redirects=True, timeout=15)
        parsed = urllib.parse.urlparse(r.url)
        qs = urllib.parse.parse_qs(parsed.query)
        result['player'] = {
            'final_url': r.url,
            'account_id': qs.get('account_id',['Unknown'])[0],
            'nickname': urllib.parse.unquote(qs.get('nickname',['Unknown'])[0]),
            'region': qs.get('region',['Unknown'])[0],
            'access_token_valid': 'account_id' in qs
        }
    except Exception as e:
        result['player'] = {'error': str(e)}

    # 2. Bind info
    try:
        url = 'https://100067.connect.garena.com/game/account_security/bind:get_bind_info'
        r = requests.get(url, params={'app_id':'100067','access_token':token}, headers=HEADERS, timeout=15)
        data = r.json()
        data['countdown_human'] = convert_seconds(data.get('request_exec_countdown',0))
        # summary logic
        email = data.get('email','')
        email_to_be = data.get('email_to_be','')
        if email=='' and email_to_be!='':
            data['summary'] = f"Pending confirmation: {email_to_be} - {data['countdown_human']}"
        elif email!='' and email_to_be=='':
            data['summary'] = f"Email confirmed: {email}"
        elif email=='' and email_to_be=='':
            data['summary'] = "No recovery email set"
        else:
            data['summary'] = f"Current: {email}, Pending: {email_to_be}"
        result['bind'] = data
    except Exception as e:
        result['bind'] = {'error': str(e)}

    return jsonify(result)

@app.route('/api/send-otp', methods=['POST'])
def api_send_otp():
    j = request.json
    url = 'https://100067.connect.garena.com/game/account_security/bind:send_otp'
    payload = {
        'email': j.get('email'),
        'locale': 'en_PK',
        'region': 'PK',
        'app_id': '100067',
        'access_token': j.get('access_token')
    }
    r = requests.post(url, data=payload, headers={**HEADERS, 'Content-Type':'application/x-www-form-urlencoded'}, timeout=15)
    try:
        return jsonify(r.json())
    except:
        return jsonify({'raw': r.text, 'status': r.status_code})

@app.route('/api/verify-otp', methods=['POST'])
def api_verify_otp():
    j = request.json
    url = 'https://100067.connect.garena.com/game/account_security/bind:verify_otp'
    payload = {
        'app_id':'100067',
        'access_token': j.get('access_token'),
        'email': j.get('email'),
        'code': j.get('otp'),
        'otp': j.get('otp'),
        'type': '1'
    }
    r = requests.post(url, data=payload, headers={**HEADERS, 'Content-Type':'application/x-www-form-urlencoded'}, timeout=15)
    try: return jsonify(r.json())
    except: return jsonify({'raw': r.text})

@app.route('/api/verify-identity', methods=['POST'])
def api_verify_identity():
    j = request.json
    url = 'https://100067.connect.garena.com/game/account_security/bind:verify_identity'
    payload = {
        'email': j.get('email'),
        'app_id':'100067',
        'access_token': j.get('access_token'),
        'otp': j.get('otp')
    }
    r = requests.post(url, data=payload, headers={**HEADERS, 'Content-Type':'application/x-www-form-urlencoded'}, timeout=15)
    try: return jsonify(r.json())
    except: return jsonify({'raw': r.text})

@app.route('/api/create-bind', methods=['POST'])
def api_create_bind():
    j = request.json
    url = 'https://100067.connect.garena.com/game/account_security/bind:create_bind_request'
    payload = {
        'email': j.get('email'),
        'app_id':'100067',
        'access_token': j.get('access_token'),
        'verifier_token': j.get('verifier_token'),
        'secondary_password': j.get('secondary_password')
    }
    r = requests.post(url, data=payload, headers={**HEADERS, 'Content-Type':'application/x-www-form-urlencoded'}, timeout=15)
    try: return jsonify(r.json())
    except: return jsonify({'raw': r.text})

@app.route('/api/create-unbind', methods=['POST'])
def api_create_unbind():
    j = request.json
    url = 'https://100067.connect.garena.com/game/account_security/bind:create_unbind_request'
    payload = {
        'app_id':'100067',
        'access_token': j.get('access_token'),
        'identity_token': j.get('identity_token')
    }
    r = requests.post(url, data=payload, headers={**HEADERS, 'Content-Type':'application/x-www-form-urlencoded'}, timeout=15)
    try: return jsonify(r.json())
    except: return jsonify({'raw': r.text})

@app.route('/api/create-rebind', methods=['POST'])
def api_create_rebind():
    j = request.json
    url = 'https://100067.connect.garena.com/game/account_security/bind:create_rebind_request'
    payload = {
        'identity_token': j.get('identity_token'),
        'email': j.get('email'),
        'app_id':'100067',
        'verifier_token': j.get('verifier_token'),
        'access_token': j.get('access_token')
    }
    r = requests.post(url, data=payload, headers={**HEADERS, 'Content-Type':'application/x-www-form-urlencoded'}, timeout=15)
    try: return jsonify(r.json())
    except: return jsonify({'raw': r.text})

@app.route('/api/cancel', methods=['POST'])
def api_cancel():
    j = request.json
    url = 'https://100067.connect.garena.com/game/account_security/bind:cancel_request'
    payload = {'app_id':'100067','access_token': j.get('access_token')}
    r = requests.post(url, data=payload, headers={**HEADERS, 'Content-Type':'application/x-www-form-urlencoded'}, timeout=15)
    try: return jsonify(r.json())
    except: return jsonify({'raw': r.text})

@app.route('/api/revoke', methods=['POST'])
def api_revoke():
    j = request.json
    token = j.get('access_token')
    refresh = '1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8'
    url = f'https://100067.connect.garena.com/oauth/logout?access_token={token}&refresh_token={refresh}'
    r = requests.get(url, headers=HEADERS_HTML, timeout=15)
    return jsonify({'status': r.status_code, 'text': r.text[:500]})

@app.route('/api/eat-to-token', methods=['GET'])
def api_eat():
    eat_input = request.args.get('eat','')
    # extract eat param if URL
    eat_token = eat_input
    if 'http' in eat_input or '?' in eat_input or 'eat=' in eat_input:
        try:
            parsed = urllib.parse.urlparse(eat_input)
            qs = urllib.parse.parse_qs(parsed.query)
            if 'eat' in qs:
                eat_token = qs['eat'][0]
        except:
            pass
    url = f'https://api-otrss.garena.com/support/callback/?access_token={eat_token}'
    r = requests.get(url, headers=HEADERS_HTML, allow_redirects=True, timeout=15)
    parsed = urllib.parse.urlparse(r.url)
    qs = urllib.parse.parse_qs(parsed.query)
    return jsonify({
        'final_url': r.url,
        'account_id': qs.get('account_id',['Unknown'])[0],
        'nickname': urllib.parse.unquote(qs.get('nickname',['Unknown'])[0]),
        'region': qs.get('region',['Unknown'])[0],
        'access_token': qs.get('access_token',[''])[0],
        'valid': 'access_token' in qs
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
