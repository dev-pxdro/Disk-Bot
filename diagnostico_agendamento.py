from googleapiclient.discovery import build
from google.oauth2 import service_account
import pandas as pd
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Caminho e escopos do serviço
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Autenticação com as credenciais
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

def ler_planilha(nome_aba):
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=nome_aba
    ).execute()
    values = result.get('values', [])
    if not values:
        print(f"❌ Aba '{nome_aba}' vazia ou não encontrada.")
        return pd.DataFrame()
    else:
        df = pd.DataFrame(values[1:], columns=values[0])
        print(f"✅ Leitura da aba '{nome_aba}' concluída com sucesso. {len(df)} linhas.")
        return df

# Abas a serem lidas
abas = ['HorariosPorMedico', 'DiasDisponiveis', 'TurnosEspeciais', 'Pacientes']

for aba in abas:
    df = ler_planilha(aba)
