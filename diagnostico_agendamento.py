from googleapiclient.discovery import build
from google.oauth2 import service_account
import pandas as pd

# Caminho do seu arquivo de credenciais
SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Substitua pelo ID da sua planilha
SPREADSHEET_ID = '1-1Ny1wnYVeBTo53s1bNSztdbhIXxmrvs-2mkLMLvhwQ'

# Autenticando com as credenciais
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

# Testar as abas existentes
abas = ['HorariosPorMedico', 'DiasDisponiveis', 'TurnosEspeciais', 'Pacientes']

for aba in abas:
    df = ler_planilha(aba)
