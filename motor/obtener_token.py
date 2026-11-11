"""Se ejecuta UNA vez por canal en tu ordenador para autorizar la subida.

Uso: python obtener_token.py client_secret.json
Abre el navegador, eliges la cuenta/canal y al final imprime el refresh token,
que se guarda como secreto del repositorio (YT_TOKEN_TONI_ES, YT_TOKEN_YSI_EN, ...).
Requiere: pip install google-auth-oauthlib
"""
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

flow= InstalledAppFlow.from_client_secrets_file(sys.argv[1], ['https://www.googleapis.com/auth/youtube.upload'])
cred= flow.run_local_server(port=0, prompt='consent', access_type='offline')
print('\nREFRESH TOKEN (guardalo como secreto, no lo compartas):\n')
print(cred.refresh_token)
