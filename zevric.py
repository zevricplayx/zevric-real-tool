import requests
import os
import sys
import json
import time
import urllib.parse

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'

# ==========================================
# UI & STYLING ENGINE (RAO THEME)
# ==========================================
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_header(subtitle=""):
    clear_screen()
    
    rao_logo = f"""{Colors.CYAN}
██████╗  █████╗  ██████╗ 
██╔══██╗██╔══██╗██╔═══██╗
██████╔╝███████║██║   ██║
██╔══██╗██╔══██║██║   ██║
██║  ██║██║  ██║╚██████╔╝
╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝   {Colors.END}"""
    print(rao_logo)
    
    # Pink separator with Title
    print(f"{Colors.MAGENTA}●{'═' * 16} {Colors.WHITE}{Colors.BOLD}► ON TOP ◄ {Colors.END}{Colors.MAGENTA}{'═' * 17}●{Colors.END}\n")
    
    # Info Section
    print(f" {Colors.GREEN}⊛ DEVELOPER : {Colors.WHITE}@raostarr{Colors.END}")
    print(f" {Colors.GREEN}⊛ STATUS    : {Colors.WHITE}SAFE & SECURE{Colors.END}")
    
    print(f"\n{Colors.MAGENTA}●{'═' * 48}●{Colors.END}\n")
    
    if subtitle:
        print(f" {Colors.CYAN}CURRENT OPTION : {Colors.WHITE}{subtitle}{Colors.END}")
        print(f"\n{Colors.MAGENTA}●{'═' * 48}●{Colors.END}\n")

def input_prompt(msg):
    return input(f"{Colors.CYAN}» {Colors.WHITE}{msg} : {Colors.END}").strip()

def print_step(current, total, msg):
    print(f"\n {Colors.MAGENTA}⊛ {Colors.CYAN}[{current}/{total}]{Colors.END} {Colors.WHITE}{msg}{Colors.END}")

def print_success(msg):
    print(f" {Colors.GREEN}⊛ {msg}{Colors.END}")

def print_error(msg):
    print(f" {Colors.RED}⊛ {msg}{Colors.END}")

def print_info(msg):
    print(f" {Colors.CYAN}⊛ {msg}{Colors.END}")

def wait_for_enter():
    print(f"\n{Colors.MAGENTA}●{'═' * 48}●{Colors.END}\n")
    input(f"{Colors.CYAN}» {Colors.WHITE}Press Enter to return to menu : {Colors.END}")
    print(Colors.END, end="")

# ==========================================
# CORE UTILITIES & API HANDLING
# ==========================================
def format_response(response_text, title="API Response"):
    """Silently parses response and prints a clean status instead of messy raw JSON."""
    try:
        parsed = json.loads(response_text)
        result_code = parsed.get("result")
        
        if result_code == 0:
            print_success(f"{title}: SUCCESS")
        elif result_code is not None:
            error_msg = parsed.get("error", "Unknown error")
            print_error(f"{title}: FAILED (Code: {result_code} | {error_msg})")
        else:
            print_info(f"{title}: Completed (No standard result code)")
            
    except Exception:
        if '"result": 0' in response_text.replace(" ", ""):
            print_success(f"{title}: SUCCESS")
        else:
            print_error(f"{title}: Unrecognized response format")


def convert_seconds(s):
    """Convert seconds to human readable format"""
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d} Day {h} Hour {m} Min {s} Sec"

def check_bind_info(access_token=None, show_raw=False):
    """Directly calls Garena API to check bind status"""
    if not access_token:
        access_token = input_prompt("Enter Access Token")
    
    print_info("Fetching account bind information from Garena...\n")
    
    # ---------------------------------------------------------
    # FETCH PLAYER INFORMATION (UID, Nickname, Region)
    # ---------------------------------------------------------
    try:
        player_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        player_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        # Requests will automatically follow the redirect
        p_res = requests.get(player_url, headers=player_headers, timeout=15, allow_redirects=True)
        
        # Parse the final URL to extract the query parameters
        parsed_url = urllib.parse.urlparse(p_res.url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        uid = query_params.get("account_id", ["Unknown"])[0]
        nickname = query_params.get("nickname", ["Unknown"])[0]
        region = query_params.get("region", ["Unknown"])[0]
        
        print(f"  {Colors.GREEN}{Colors.BOLD}≡ Player Information{Colors.END}")
        print(f"    {Colors.CYAN}● UID:{Colors.END}       {Colors.WHITE}{uid}{Colors.END}")
        print(f"    {Colors.YELLOW}● Nickname:{Colors.END}  {Colors.WHITE}{nickname}{Colors.END}")
        print(f"    {Colors.MAGENTA}● Region:{Colors.END}    {Colors.WHITE}{region}{Colors.END}\n")
        
    except Exception as e:
        print_error(f"Failed to fetch player details: {str(e)}\n")

    # ---------------------------------------------------------
    # FETCH BIND INFORMATION
    # ---------------------------------------------------------
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    payload = {'app_id': "100067", 'access_token': access_token}
    headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }
    
    try:
        response = requests.get(url, params=payload, headers=headers, timeout=15)
        
        print(f"  {Colors.GREEN}{Colors.BOLD}≡ Bind Information{Colors.END}")
        
        if response.status_code == 200:
            data = response.json()
            
            email = data.get("email", "")
            email_to_be = data.get("email_to_be", "")
            countdown = data.get("request_exec_countdown", 0)
            
            countdown_human = convert_seconds(countdown)
            result_code = data.get("result", -1)
            
            print(f"    {Colors.CYAN}● Current Email:{Colors.END}  {Colors.WHITE}{email if email else 'None'}{Colors.END}")
            print(f"    {Colors.YELLOW}● Pending Email:{Colors.END}  {Colors.WHITE}{email_to_be if email_to_be else 'None'}{Colors.END}")
            if email_to_be:
                print(f"    {Colors.MAGENTA}● Countdown:{Colors.END}      {Colors.WHITE}{countdown_human}{Colors.END}")
            if result_code == 0:
                print(f"    {Colors.GREEN}● Result:{Colors.END}         {Colors.GREEN}✓ SUCCESS{Colors.END}")
            else:
                print(f"    {Colors.RED}● Result:{Colors.END}         {Colors.RED}✗ FAILED (Code: {result_code}){Colors.END}")

            summary = ""
            if email == "" and email_to_be != "":
                summary = f"Pending email confirmation: {email_to_be} - Confirms in: {countdown_human}"
            elif email != "" and email_to_be == "":
                summary = f"Email confirmed: {email}"
            elif email == "" and email_to_be == "":
                summary = "No recovery email set"
                
            if summary:
                print(f"\n    {Colors.BLUE}● Summary:{Colors.END} {Colors.WHITE}{summary}{Colors.END}")

            if show_raw:
                print(f"\n    {Colors.DIM}Raw Response: {json.dumps(data)}{Colors.END}")
                
        else:
            print_error(f"API Error (Status {response.status_code}): {response.text[:100]}")
            
    except Exception as e:
        print_error(f"Failed to fetch info: {str(e)}")

# ==========================================
# MODULES
# ==========================================

# 1. BIND EMAIL
def bind_email():
    draw_header("BIND EMAIL")
    
    access_token = input_prompt("Enter Access Token")
    print("")
    check_bind_info(access_token, show_raw=False)
    print("")
    email = input_prompt("Enter Email to bind")
    
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    print_step(1, 3, f"Sending OTP to {email}...")
    send_otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    send_otp_data = {
        "email": email,
        "locale": "en_PK",
        "region": "PK",
        "app_id": "100067",
        "access_token": access_token
    }
    resp_send = requests.post(send_otp_url, headers=headers, data=send_otp_data)
    format_response(resp_send.text, "Send OTP")

    otp = input_prompt("Enter OTP received in email")

    print_step(2, 3, "Verifying OTP securely...")
    verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    verify_data = {
        "app_id": "100067",
        "access_token": access_token,
        "email": email,
        "code": otp,
        "otp": otp,
        "type": "1"
    }
    resp_verify = requests.post(verify_url, headers=headers, data=verify_data)
    format_response(resp_verify.text, "Verify OTP")

    verifier_token = ""
    try:
        verifier_token = resp_verify.json().get("verifier_token", "")
    except: pass

    if not verifier_token:
        print_error("Could not automatically extract verifier_token.")
        verifier_token = input_prompt("Please enter the verifier_token manually")
    else:
        print_success("Verifier Token extracted successfully!")

        security_code = input_prompt("Set 6-digits security code")

    print_step(3, 3, "Creating bind request...")
    bind_url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
    bind_data = {
        "email": email,
        "app_id": "100067",
        "access_token": access_token,
        "verifier_token": verifier_token,
        "secondary_password": security_code
    }
    resp_bind = requests.post(bind_url, headers=headers, data=bind_data)
    format_response(resp_bind.text, "Final Bind Request")

    wait_for_enter()

# 2. CHANGE BIND EMAIL
def change_bind_email():
    draw_header("CHANGE BIND EMAIL")
    
    access_token = input_prompt("Enter Access Token")
    print("")
    check_bind_info(access_token, show_raw=False)
    
    # Silently fetch the current bound email to use as old_email
    try:
        url_info = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        info_payload = {'app_id': "100067", 'access_token': access_token}
        info_headers = {'User-Agent': "GarenaMSDK/4.0.30"}
        r_info = requests.get(url_info, params=info_payload, headers=info_headers, timeout=10)
        old_email = r_info.json().get("email", "")
    except:
        old_email = ""
        
    if not old_email:
        print_error("No currently bound email found! You cannot use 'Change Bind' without an existing email.")
        return wait_for_enter()
    
    
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    print_step(1, 5, f"Sending OTP to {old_email}...")
    url_send = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {
        "email": old_email,
        "locale": "en_PK",
        "region": "PK",
        "app_id": "100067",
        "access_token": access_token
    }
    r = requests.post(url_send, headers=headers, data=data)
    format_response(r.text, "Send Old Email OTP")
    
    otp_old = input_prompt(f"Enter OTP from {old_email}")
    
    print_step(2, 5, "Verifying Old Email Identity...")
    url_verify_identity = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    data = {"email": old_email, "app_id": "100067", "access_token": access_token, "otp": otp_old}
    r = requests.post(url_verify_identity, headers=headers, data=data)
    format_response(r.text, "Verify Identity")

    identity_token = None
    try:
        identity_token = r.json().get("identity_token")
        if identity_token:
            print_success("Identity Token Extracted!")
        else:
            print_error("No identity token received!")
            return wait_for_enter()
    except:
        return wait_for_enter()

    new_email = input_prompt("Enter New Email")

    print_step(3, 5, f"Sending OTP to {new_email}...")
    data = {"email": new_email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": access_token}
    r = requests.post(url_send, headers=headers, data=data)
    format_response(r.text, "Send New Email OTP")
    
    otp_new = input_prompt(f"Enter OTP from {new_email}")

    print_step(4, 5, "Verifying New Email OTP...")
    url_verify_otp = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    data = {"email": new_email, "app_id": "100067", "access_token": access_token, "otp": otp_new}
    r = requests.post(url_verify_otp, headers=headers, data=data)
    format_response(r.text, "Verify OTP")

    verifier_token = None
    try:
        verifier_token = r.json().get("verifier_token")
        if verifier_token:
            print_success("Verifier Token Extracted!")
        else:
            print_error("No verifier token received!")
            return wait_for_enter()
    except:
        return wait_for_enter()

    print_step(5, 5, "Creating Rebind Request...")
    url_rebind = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
    data = {"identity_token": identity_token, "email": new_email, "app_id": "100067", "verifier_token": verifier_token, "access_token": access_token}
    r = requests.post(url_rebind, headers=headers, data=data)
    format_response(r.text, "Rebind Request")

    wait_for_enter()



# 3. UNBIND EMAIL
def unbind_email():
    draw_header("UNBIND EMAIL")
    
    access_token = input_prompt("Enter Access Token")
    print("")
    check_bind_info(access_token, show_raw=False)
    
    # Silently fetch the current bound email
    try:
        url_info = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        info_payload = {'app_id': "100067", 'access_token': access_token}
        info_headers = {'User-Agent': "GarenaMSDK/4.0.30"}
        r_info = requests.get(url_info, params=info_payload, headers=info_headers, timeout=10)
        email = r_info.json().get("email", "")
    except:
        email = ""
        
    if not email:
        print_error("No currently bound email found! You cannot use 'Unbind' without an existing email.")
        return wait_for_enter()
    
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    print_step(1, 3, f"Sending OTP to {email}...")
    send_otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    send_otp_data = {"email": email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": access_token}
    resp = requests.post(send_otp_url, headers=headers, data=send_otp_data)
    format_response(resp.text, "Send OTP")
    
    otp = input_prompt(f"Enter OTP from {email}")
    
    print_step(2, 3, "Verifying Identity...")
    verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    verify_data = {"email": email, "app_id": "100067", "access_token": access_token, "otp": otp}
    resp = requests.post(verify_url, headers=headers, data=verify_data)
    format_response(resp.text, "Verify Identity")

    identity_token = None
    try:
        identity_token = resp.json().get("identity_token")
        if identity_token:
            print_success("Identity Token Extracted!")
        else:
            print_error("Identity verification failed!")
            return wait_for_enter()
    except:
        return wait_for_enter()

    print_step(3, 3, "Creating Unbind Request...")
    unbind_url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
    unbind_data = {"app_id": "100067", "access_token": access_token, "identity_token": identity_token}
    resp = requests.post(unbind_url, headers=headers, data=unbind_data)
    format_response(resp.text, "Unbind Request")
    
    wait_for_enter()



# 4. CANCEL BIND REQUEST
def cancel_bind():
    draw_header("CANCEL BIND REQUEST")
    
    access_token = input_prompt("Enter Access Token")
    print("")
    check_bind_info(access_token, show_raw=False)
    
    print_step(1, 1, "Creating Cancel Request...")
    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data = {"app_id": "100067", "access_token": access_token}
    response = requests.post(url, headers=headers, data=data)
    
    format_response(response.text, "Cancel Request")
    wait_for_enter()

# 5. CHECK BIND INFO
def bind_info():
    draw_header("CHECK BIND INFO")
    access_token = input_prompt("Enter Access Token")
    print("")
    check_bind_info(access_token, show_raw=False)
    wait_for_enter()


# 6. SECURITY CODE INFO ★★★ NEW FEATURE ★★★
def security_code_info():
    """
    ★ SECURITY CODE INFO - Direct निकालना ★
    Access Token → Garena API → Security Code Status
    """
    draw_header("SECURITY CODE INFO")
    
    access_token = input_prompt("Enter Access Token")
    print("")
    
    print_step(1, 1, "Fetching Security Code from Garena...")
    
    headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }
    
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    params = {
        'app_id': "100067",
        'access_token': access_token
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            result_code = data.get("result", -1)
            
            if result_code == 0:
                # Extract data
                email = data.get("email", "")
                secondary_password = data.get("secondary_password", False)
                
                print(f"\n  {Colors.GREEN}{Colors.BOLD}≡ Account Information{Colors.END}")
                print(f"    {Colors.CYAN}● Email:{Colors.END} {Colors.WHITE}{email if email else 'Not Bound'}{Colors.END}")
                
                print(f"\n  {Colors.GREEN}{Colors.BOLD}≡ Security Code Status{Colors.END}")
                
                if secondary_password:
                    print(f"    {Colors.GREEN}✓ ACTIVE{Colors.END}")
                    print(f"    {Colors.CYAN}● Status:{Colors.END} {Colors.WHITE}Security Code is SET{Colors.END}")
                    print(f"    {Colors.YELLOW}● Protection:{Colors.END} {Colors.WHITE}HIGH - Account Protected{Colors.END}")
                    print(f"    {Colors.MAGENTA}● Format:{Colors.END} {Colors.WHITE}6-Digit Numeric Code{Colors.END}")
                else:
                    print(f"    {Colors.RED}✗ NO SECURITY CODE{Colors.END}")
                    print(f"    {Colors.CYAN}● Status:{Colors.END} {Colors.WHITE}Not Set{Colors.END}")
                    print(f"    {Colors.YELLOW}● Protection:{Colors.END} {Colors.WHITE}LOW - Account Not Protected{Colors.END}")
                    print(f"    {Colors.MAGENTA}● Recommendation:{Colors.END} {Colors.WHITE}Add security code via Bind Email{Colors.END}")
                
                # Full response
                print(f"\n  {Colors.GREEN}{Colors.BOLD}≡ Full API Response{Colors.END}")
                print(f"    {Colors.DIM}{json.dumps(data, indent=6)}{Colors.END}")
                
            else:
                error_msg = data.get("error", "Unknown error")
                print_error(f"API Error: Code {result_code} | {error_msg}")
        else:
            print_error(f"API Error: HTTP {response.status_code}")
    
    except Exception as e:
        print_error(f"Connection Error: {str(e)}")
    
    wait_for_enter()


# 7. EAT TO ACCESS TOKEN
def eat_to_access_token():
    draw_header("EAT TO ACCESS TOKEN")
    
    user_input = input_prompt("Enter EAT Token OR Full EAT URL")
    
    # Extract token
    eat_token = None
    if "http" in user_input or "?" in user_input:
        parsed_url = urllib.parse.urlparse(user_input)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        if 'eat' in query_params:
            eat_token = query_params['eat'][0]
    else:
        eat_token = user_input.strip()
        
    if not eat_token:
        print_error("Could not find an EAT token in your input.")
        return wait_for_enter()
        
    print_step(1, 1, "Contacting Server & Following Redirects...")
    
    api_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
    }
    
    try:
        response = requests.get(api_url, headers=headers, allow_redirects=True, timeout=15)
        parsed_final = urllib.parse.urlparse(response.url)
        final_params = urllib.parse.parse_qs(parsed_final.query)
        
        if 'access_token' in final_params:
            access_token = final_params['access_token'][0]
            account_id = final_params.get('account_id', ['Unknown'])[0]
            nickname = final_params.get('nickname', ['Unknown'])[0]
            region = final_params.get('region', ['Unknown'])[0]
            
            # --- CUSTOM COLORED SUCCESS RESULTS ---
            print(f"\n{Colors.GREEN}●{'═' * 19} {Colors.WHITE}{Colors.BOLD}SUCCESS{Colors.END} {Colors.GREEN}{'═' * 20}●{Colors.END}")
            print(f" {Colors.CYAN}Nickname    :{Colors.END} {Colors.WHITE}{urllib.parse.unquote(nickname)}{Colors.END}")
            print(f" {Colors.CYAN}Account ID  :{Colors.END} {Colors.WHITE}{account_id}{Colors.END}")
            print(f" {Colors.CYAN}Region      :{Colors.END} {Colors.WHITE}{region}{Colors.END}")
            print(f" {Colors.CYAN}Access Token:{Colors.END}\n {Colors.YELLOW}{access_token}{Colors.END}") # Token is Yellow so it pops!
            print(f"{Colors.GREEN}●{'═' * 48}●{Colors.END}")
            
        else:
            print_error("Access token not found. The token might be expired or invalid.")
            
    except Exception as e:
        print_error(f"Failed to generate access token: {str(e)}")
        
    wait_for_enter()




# 8. REVOKE ACCESS TOKEN
def revoke_access_token():
    draw_header("REVOKE ACCESS TOKEN")
    
    access_token = input_prompt("Enter Access Token to Revoke")
    if not access_token:
        print_error("Token cannot be empty.")
        return wait_for_enter()
        
    print_step(1, 2, "Checking Token Status & Fetching Info...")
    
    # Use api-otrss to fetch info and verify if the token is still alive
    api_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    nickname = "Unknown"
    account_id = "Unknown"
    region = "Unknown"
    is_valid = False
    
    try:
        res = requests.get(api_url, headers=headers, allow_redirects=True, timeout=15)
        parsed = urllib.parse.urlparse(res.url)
        params = urllib.parse.parse_qs(parsed.query)
        
        if 'access_token' in params:
            is_valid = True
            nickname = urllib.parse.unquote(params.get('nickname', ['Unknown'])[0])
            account_id = params.get('account_id', ['Unknown'])[0]
            region = params.get('region', ['Unknown'])[0]
    except Exception:
        pass
        
    if not is_valid:
        print_error("Token is already invalid, expired, or revoked!")
        return wait_for_enter()
        
    print_success(f"Token is Valid!")
    
    print_step(2, 2, "Revoking Token Access (Logging Out)...")
    
    # Hit the Garena OAuth Logout endpoint to kill the token
    refresh_token = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
    logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={access_token}&refresh_token={refresh_token}"
    
    try:
        logout_res = requests.get(logout_url, headers=headers, timeout=15)
        
        if logout_res.status_code == 200 and "error" not in logout_res.text:
            # --- CUSTOM COLORED SUCCESS RESULTS ---
            print(f"\n{Colors.GREEN}●{'═' * 19} {Colors.WHITE}{Colors.BOLD}REVOKED{Colors.END} {Colors.GREEN}{'═' * 20}●{Colors.END}")
            print(f" {Colors.CYAN}Nickname    :{Colors.END} {Colors.WHITE}{nickname}{Colors.END}")
            print(f" {Colors.CYAN}Account ID  :{Colors.END} {Colors.WHITE}{account_id}{Colors.END}")
            print(f" {Colors.CYAN}Region      :{Colors.END} {Colors.WHITE}{region}{Colors.END}")
            print(f" {Colors.CYAN}Status      :{Colors.END} {Colors.GREEN}Successfully Logged Out & Revoked{Colors.END}")
            print(f"{Colors.GREEN}●{'═' * 48}●{Colors.END}\n")
        else:
            print_error("Failed to revoke token! Server responded with an error.")
            
    except Exception as e:
        print_error(f"Error while revoking token: {str(e)}")
        
    wait_for_enter()




# 9. OWNER DETAILS
def owner_details():
    draw_header("OWNER DETAILS")
    
    # Using Colors.CYAN for the lines to match the theme's accent color
    print(f"\n{Colors.CYAN}●{'═' * 16} {Colors.WHITE}{Colors.BOLD}DEVELOPER INFO{Colors.END} {Colors.CYAN}{'═' * 16}●{Colors.END}\n")
    
    # Text color is back to WHITE as you preferred
    print(f" {Colors.CYAN}⊛ Developer Name :{Colors.END} {Colors.WHITE}RAOSTAR{Colors.END}")
    print(f" {Colors.CYAN}⊛ Telegram       :{Colors.END} {Colors.WHITE}@raostarr{Colors.END}")
    print(f" {Colors.CYAN}⊛ Channel / Group:{Colors.END} {Colors.WHITE}https://t.me/raostarrr{Colors.END}")
    print(f" {Colors.CYAN}⊛ YouTube Channel:{Colors.END} {Colors.WHITE}https://youtube.com/@raostarrr?si=u2RyMP5BCZ4RGBzY{Colors.END}")
    print(f" {Colors.CYAN}⊛ GitHub Profile :{Colors.END} {Colors.WHITE}github.com/LuckDucapa{Colors.END}")
    print(f" {Colors.CYAN}⊛ Tool Version   :{Colors.END} {Colors.GREEN}v1.2 (Premium / Secure){Colors.END}")
    
    print(f"\n{Colors.CYAN}●{'═' * 18} {Colors.WHITE}{Colors.BOLD}SPECIAL NOTE{Colors.END} {Colors.CYAN}{'═' * 16}●{Colors.END}\n")
    
    print(f" {Colors.YELLOW}Thank you for using RaoStar Bind Tool!{Colors.END}")
    print(f" {Colors.WHITE}This tool was created to provide a fast, secure,{Colors.END}")
    print(f" {Colors.WHITE}and reliable way to manage Garena Bind Accounts.{Colors.END}")
    print(f" {Colors.WHITE}Please report any bugs directly on Telegram.{Colors.END}")
    
    print(f"\n{Colors.CYAN}●{'═' * 48}●{Colors.END}")
    
    wait_for_enter()



# ==========================================
# MAIN MENU LOOP
# ==========================================
def show_menu():
    draw_header()
    print(f" {Colors.CYAN}MENU OPTIONS:{Colors.END}")
    
    options = [
        ("1", "CHECK BIND INFO"),
        ("2", "BIND EMAIL"),
        ("3", "UNBIND EMAIL"),
        ("4", "CHANGE BIND EMAIL"),
        ("5", "CANCEL BIND REQUEST"),
        ("6", "SECURITY CODE INFO"),
        ("7", "EAT TO ACCESS TOKEN"),
        ("8", "REVOKE ACCESS TOKEN"),
        ("9", "OWNER DETAILS")
    ]
    
    for num, text in options:
        print(f" {Colors.MAGENTA}⊛ [{Colors.WHITE}{num}{Colors.MAGENTA}] {Colors.WHITE}{text}{Colors.END}")
    
    print(f" {Colors.MAGENTA}⊛ {Colors.RED}[0] EXIT{Colors.END}")
    
    print(f"\n{Colors.MAGENTA}●{'═' * 48}●{Colors.END}\n")

def main():
    while True:
        show_menu()
        choice = input_prompt("Select Option")
        
        if choice == "1":
            bind_info()
        elif choice == "2":
            bind_email()
        elif choice == "3":
            unbind_email()
        elif choice == "4":
            change_bind_email()
        elif choice == "5":
            cancel_bind()
        elif choice == "6":
            security_code_info()
        elif choice == "7":
            eat_to_access_token()
        elif choice == "8":
            revoke_access_token()
        elif choice == "9":
            owner_details()
        elif choice == "0":
            clear_screen()
            print(f"\n {Colors.MAGENTA}⊛ {Colors.GREEN}Safely Exited. JAI SHREE RAM 🙏{Colors.END}\n")
            sys.exit(0)
        else:
            print(f"\n {Colors.RED}⊛ Invalid option! Please try again.{Colors.END}")
            time.sleep(1.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n {Colors.MAGENTA}⊛ {Colors.GREEN}Safely Exited. JAI SHREE RAM 🙏{Colors.END}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n {Colors.RED}⊛ Error: {str(e)}{Colors.END}")
        input(f"\n {Colors.CYAN}» {Colors.WHITE}Press Enter to exit : {Colors.END}")
