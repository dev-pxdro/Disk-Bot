 Autor
Feito com carinho por Pedro Henrique Alves
💡 Estudante de Análise e Desenvolvimento de Sistemas
🔗 github.com/seu-usuario


# 🤖 Disk Saúde Bot - Agendamento via WhatsApp

Este projeto é um bot automatizado para o WhatsApp, criado para ajudar no agendamento de consultas médicas pelo município de Antonina. Ele interage com pacientes via WhatsApp, coleta dados e registra tudo automaticamente em uma planilha do Google Sheets.

📁 node-bot/
├── index.js (inicia o Venom)
├── handleMessage.js (lógica de atendimento)
└── package.json

📄 salvar_agendamento.py (processa e envia os dados para o Google Sheets)
📄 credentials.json (🔒 credenciais da API Google )

## 🚀 Funcionalidades

- 🧠 Atendimento automatizado por mensagens
- 🩺 Coleta dados do paciente
- 📊 Armazena informações diretamente em uma planilha
- 🕐 Encerra sessões após inatividade
- ℹ️ Oferece informações sobre transporte, vacinação, TFD e mais

## 🛠 Tecnologias Utilizadas

- [Node.js](https://nodejs.org)
- [venom-bot](https://github.com/orkestral/venom)
- [Python 3](https://www.python.org/)
- [Google Sheets API](https://developers.google.com/sheets/api)
- Google Cloud Console

## 🧰 Como usar

### 1. Instalar dependências

```bash
cd node-bot
npm install

#Crie o arquivo credentials.json na raiz do projeto (fora da pasta node-bot). Ele será usado pelo script Python para acessar a planilha.

# Dentro da pasta node-bot
node index.js