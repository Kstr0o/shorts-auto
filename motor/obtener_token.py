"""Se ejecuta UNA vez por canal en tu ordenador para autorizar la subida.

Uso: python obtener_token.py client_secret.json
Abre el navegador, eliges la cuenta/canal y al final imprime el refresh token,
que se guarda como secreto del repositorio (YT_TOKEN_TONI_ES, YT_TOKEN_YSI_EN, ...).
Pide permiso para subir y para LEER comentarios y estadisticas (motor/estadisticas.py).
En la pantalla de consentimiento de Google Cloud hay que anadir esos tres alcances.
Requiere: pip install google-auth-oauthlib
"""
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

flow= InstalledAppFlow.from_client_secrets_file(sys.argv[1], ['https://www.googleapis.com/auth/youtube.upload',
                                                       'https://www.googleapis.com/auth/youtube.readonly',  # leer comentarios
                                                       'https://www.googleapis.com/auth/yt-analytics.readonly'])  # leer estadisticas
cred= flow.run_local_server(port=0, prompt='consent', access_type='offline')
print('\nREFRESH TOKEN (guardalo como secreto, no lo compartas):\n')
print(cred.refresh_token)
