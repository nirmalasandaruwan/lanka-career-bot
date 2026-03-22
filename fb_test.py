import requests

# 1. අර කොපි කරගත්ත Page Access Token එක මෙතනට දාන්න
access_token = 'EAAU4hyMkW0IBRKWkzyoJbBI4tPEN3JwurxOrzkZA2UNLwrDcpuPhc0UnF8qBpFfwb5ya1z4p5aAOaZBDaMMPqjlYNxL8WeNC2OZBhDpkGzq11l91VmMZCbterZBk2jaJhA21jieJzbZABOAqLZBBLWgb82T4CulFsJd5fjAIVZBR54ykmcfrprjdmQ15ZBSAv6OQMpw8XIjDZAFZCBM13eapBBnQHUNYBMAqIXXQrtfGV0ZD'

# 2. පේජ් එකට යවන මැසේජ් එක
message = "අඩෝ මචංලා! මේක තමයි මගේ පළවෙනි Automated Job Post එක. Lanka Career Hub Bot එක දැන් ලයිව්! 🚀 #Python #Automation #LankaCareerHub"

# 3. Facebook Graph API URL
url = f"https://graph.facebook.com/v25.0/me/feed"

payload = {
    'message': message,
    'access_token': access_token
}

try:
    print("පෝස්ට් එක යවමින් පවතිනවා... පොඩ්ඩක් ඉන්න මචං...")
    response = requests.post(url, data=payload)
    result = response.json()

    if response.status_code == 200:
        print("\n🎯 නියමයි මචං! පෝස්ට් එක සාර්ථකව පේජ් එකට වැටුණා.")
        print("Post ID:", result.get('id'))
    else:
        print("\n❌ අයියෝ අවුලක් වුණා මචං:", result.get('error', {}).get('message'))
except Exception as e:
    print("\n⚠️ Error එකක් ආවා:", str(e))