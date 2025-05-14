import gspread  
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import sys
import os
import io  # Para corrigir problemas de emoji no terminal do Windows

# Força o terminal a aceitar UTF-8 (corrige erro com emojis no Windows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Mapeamento de médicos por bairro e especialidade
def obter_medico(bairro, especialidade):
    bairro = bairro.lower()

    if especialidade.lower() == "clínico geral":
        if bairro in ["batel 1", "tucunduva"]:
            return "Doutor Gustavo"
        elif bairro in ["batel 2", "caixa d'água", "jardim maria luiza"]:
            return "Doutora Leticia"
        elif bairro == "portinho":
            return "Doutora Elenir"
        elif bairro in ["centro", "penha"]:
            return "Doutora Valéria"

    elif especialidade.lower() == "nutricionista":
        return "Danielle de Oliveira"

    elif especialidade.lower() == "odontologia":
        if bairro in ["batel 2", "caixa d'água", "jardim maria luiza"]:
            return "Doutora Eduarda"
        elif bairro in ["batel 1", "tucunduva"]:
            return "Doutora Maria Paula"
        elif bairro == "portinho":
            return "Doutora Patrícia"
        elif bairro in ["centro", "penha"]:
            return "Doutor Claudio"

    elif especialidade.lower() == "fisioterapia":
        return "Jonatan Calemi"

    return None

# Consulta a aba "HorariosPorMedico" para obter o limite
def obter_limite_por_medico(sheet_limites, medico, data_str):
    registros = sheet_limites.get_all_records()
    for r in registros:
        if r["Médico"].strip().lower() == medico.strip().lower() and r["Data"] == data_str:
            try:
                return int(r["Limite"])
            except:
                return 20
    return 20  # valor padrão caso não encontre

def agendar(nome, telefone, cartao_sus, rua, bairro, especialidade):
    endereco = f"{rua}, {bairro}"
    medico = obter_medico(bairro, especialidade)

    if not medico:
        return f"⚠️ Não encontramos um médico disponível para *{especialidade}* no bairro *{bairro.title()}*. Por favor, verifique e tente novamente."

    # Caminho absoluto para o arquivo de credenciais
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(current_dir, "credentials.json")

    creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
    client = gspread.authorize(creds)
    sheet_agendamentos = client.open("AgendaMedica").worksheet("Agendamentos")
    sheet_limites = client.open("AgendaMedica").worksheet("HorariosPorMedico")

    registros = sheet_agendamentos.get_all_records()

    hoje = datetime.today()
    quinzena = [hoje + timedelta(days=x) for x in range(0, 15)]

    for data in quinzena:
        data_str = data.strftime("%d/%m/%Y")
        agendados = [r for r in registros if r["Médico"] == medico and r["Data"] == data_str]
        limite = obter_limite_por_medico(sheet_limites, medico, data_str)

        if len(agendados) < limite:
            sheet_agendamentos.append_row([nome, telefone, cartao_sus, endereco, especialidade, medico, data_str])
            return f"✅ Consulta agendada com *{medico}* para o dia *{data_str}*. Compareça com antecedência. Obrigado!"

    return f"⚠️ Sem vagas com *{medico}* nos próximos 15 dias. Tente novamente em breve."

# Execução via linha de comando (usado pelo bot)
if __name__ == "__main__":
    if len(sys.argv) < 7:
        print("⚠️ Argumentos insuficientes. Esperado: nome telefone cartao_sus rua bairro especialidade")
        sys.exit(1)

    nome = sys.argv[1]
    telefone = sys.argv[2]
    cartao_sus = sys.argv[3]
    rua = sys.argv[4]
    bairro = sys.argv[5]
    especialidade = sys.argv[6]

    resultado = agendar(nome, telefone, cartao_sus, rua, bairro, especialidade)
    print(resultado)
