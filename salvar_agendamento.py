import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from unidecode import unidecode
from pymongo import MongoClient
import sys
import os
import io

# Conexão com MongoDB
MONGO_URI = "mongodb+srv://Admin:Toparatu20@cluster0.xqhpmhw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client_mongo = MongoClient(MONGO_URI)
db = client_mongo["agendamento_db"]
colecao_agendamentos = db["agendamentos"]

# Suporte a caracteres especiais no terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Data mínima para agendamentos
DATA_MINIMA = datetime.strptime("2025-05-15", "%Y-%m-%d").date()

# Mapeamento dias da semana inglês -> português
DIAS_PT = {
    "monday": "Segunda",
    "tuesday": "Terça",
    "wednesday": "Quarta",
    "thursday": "Quinta",
    "friday": "Sexta",
    "saturday": "Sábado",
    "sunday": "Domingo"
}

# ---------------- FUNÇÕES AUXILIARES ---------------- #

def converter_data_planilha(data):
    """Converte datas do formato float (serial Excel) para string dd/mm/yyyy"""
    if isinstance(data, float) or isinstance(data, int):
        data_convertida = datetime.fromordinal(datetime(1899, 12, 30).toordinal() + int(data))
        return data_convertida.strftime("%d/%m/%Y")
    elif isinstance(data, str):
        return data.strip()
    elif isinstance(data, datetime):
        return data.strftime("%d/%m/%Y")
    else:
        return ""

def calcular_idade(data_nascimento):
    hoje = datetime.today()
    nascimento = datetime.strptime(data_nascimento, "%d/%m/%Y")
    return hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))

def obter_dados_paciente(sheet_pacientes, cartao_sus):
    pacientes = sheet_pacientes.get_all_records()
    input_sus = cartao_sus.strip().replace(" ", "")
    for paciente in pacientes:
        # Normalize keys para evitar erros com espaços e acentos
        paciente_keys = {unidecode(k.lower().strip()): v for k, v in paciente.items()}
        valor_sus = str(paciente_keys.get("cartao sus", "")).strip().replace(" ", "")
        if valor_sus == input_sus:
            return paciente_keys
    return None

def obter_turnos_disponiveis(sheet_horarios, medico, data_str, tipo_paciente):
    registros = sheet_horarios.get_all_records()
    for r in registros:
        data_planilha = converter_data_planilha(r.get("Data", ""))
        if r.get("Médico", "").strip().lower() == medico.lower() and data_planilha == data_str:
            tipo = r.get("Tipo de Paciente", "").strip().lower()
            if tipo_paciente.lower() in tipo or tipo == "qualquer":
                turnos = r.get("Turnos Disponíveis", "")
                return [t.strip().capitalize() for t in turnos.split(",") if t.strip()]
    return []

def obter_limite_turno(sheet_horarios, medico, data_str, turno):
    registros = sheet_horarios.get_all_records()
    for r in registros:
        data_planilha = converter_data_planilha(r.get("Data", ""))
        if r.get("Médico", "").strip().lower() == medico.lower() and data_planilha == data_str:
            turnos = [t.strip().capitalize() for t in r.get("Turnos Disponíveis", "").split(",")]
            if turno.capitalize() in turnos:
                try:
                    return int(r.get("Limite por Turno", 20))
                except ValueError:
                    return 20
    return 20

def medico_atende_dia(sheet_dias, medico, dia_semana):
    dia_pt = DIAS_PT.get(dia_semana, "")
    registros = sheet_dias.get_all_records()
    for r in registros:
        if r.get("Médico", "").strip().lower() == medico.lower():
            return r.get(dia_pt, "").strip().lower() == "sim"
    return False

# ---------------- FUNÇÃO PRINCIPAL ---------------- #

def agendar(nome, telefone, cartao_sus, rua, bairro, especialidade):
    endereco = f"{rua}, {bairro}"

    # Autenticação com a planilha
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
    creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
    client = gspread.authorize(creds)

    planilha = client.open("AgendaMedica")
    sheet_agendamentos = planilha.worksheet("Agendamentos")
    sheet_horarios = planilha.worksheet("HorariosPorMedico")
    sheet_pacientes = planilha.worksheet("Pacientes")
    sheet_dias = planilha.worksheet("DiasDisponiveis")

    paciente_info = obter_dados_paciente(sheet_pacientes, cartao_sus)
    if not paciente_info:
        return f"⚠️ O cartão SUS *{cartao_sus}* não está cadastrado na base de pacientes."

    medico = paciente_info.get("medico", "").strip()
    if not medico:
        return f"⚠️ O cartão SUS *{cartao_sus}* está com cadastro incompleto (sem médico vinculado)."

    idade = calcular_idade(paciente_info.get("data de nascimento", "01/01/1900"))
    tipo_paciente = "Pediátrico" if idade < 12 else "Adulto"
    
    registros = sheet_agendamentos.get_all_records()
    data_inicio = max(datetime.today().date(), DATA_MINIMA)
    datas_validas = [data_inicio + timedelta(days=i) for i in range(15)]

    for data in datas_validas:
        data_str = data.strftime("%d/%m/%Y")
        dia_semana = data.strftime("%A").lower()

        # Verifica se médico atende no dia
        if not medico_atende_dia(sheet_dias, medico, dia_semana):
            continue

        turno_escolhido = None
        if especialidade.lower() == "clínico geral":
            if tipo_paciente == "Pediátrico":
                # Pediátrico só segunda à tarde
                if dia_semana == "monday":
                    turnos = obter_turnos_disponiveis(sheet_horarios, medico, data_str, "Pediátrico")
                    if "Tarde" in turnos:
                        turno_escolhido = "Tarde"
                else:
                    continue  # Não atende pediátrico em outros dias
            else:
                # Adultos: qualquer dia, preferencialmente manhã
                turnos = obter_turnos_disponiveis(sheet_horarios, medico, data_str, "Adulto")
                if dia_semana == "monday":
                    if "Manhã" in turnos:
                        turno_escolhido = "Manhã"
                else:
                    if "Manhã" in turnos:
                        turno_escolhido = "Manhã"
                    elif "Tarde" in turnos:
                        turno_escolhido = "Tarde"
        else:
            # Para outras especialidades, qualquer turno disponível
            turnos = obter_turnos_disponiveis(sheet_horarios, medico, data_str, tipo_paciente)
            if "Manhã" in turnos:
                turno_escolhido = "Manhã"
            elif "Tarde" in turnos:
                turno_escolhido = "Tarde"

        if not turno_escolhido:
            continue

        limite = obter_limite_turno(sheet_horarios, medico, data_str, turno_escolhido)
        agendados = [r for r in registros if r.get("Médico", "").strip().lower() == medico.lower() and
                     r.get("Data", "") == data_str and r.get("Turno", "").capitalize() == turno_escolhido]

        if len(agendados) < limite:
            try:
                # Salva na planilha
                sheet_agendamentos.append_row([
                    nome, telefone, cartao_sus, endereco, especialidade, medico, data_str, turno_escolhido
                ])
                # Salva no MongoDB
                colecao_agendamentos.insert_one({
                    "nome": nome,
                    "telefone": telefone,
                    "cartao_sus": cartao_sus,
                    "endereco": endereco,
                    "especialidade": especialidade,
                    "medico": medico,
                    "data": data_str,
                    "turno": turno_escolhido,
                    "hora": "08:00" if turno_escolhido == "Manhã" else "13:00",
                    "data_criacao": datetime.now()
                })
                hora_consulta = "08:00" if turno_escolhido == "Manhã" else "13:00"
                return (
                    f"✅ Consulta agendada com *{medico}* para o dia *{data_str} às {hora_consulta} horas*.\n"
                    f"Compareça com 15 minutos de antecedência. Obrigado!\n"
                    f"Se quiser agendar outro atendimento, envie 'oi'."
                )
            except Exception as e:
                return f"⚠️ Erro ao salvar agendamento: {e}"

    return f"⚠️ Sem vagas com *{medico}* nos próximos 15 dias."

# ---------------- EXECUÇÃO VIA TERMINAL ---------------- #

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
