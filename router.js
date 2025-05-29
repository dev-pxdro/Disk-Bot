const { exec } = require('child_process');

const estados = {};
const tempoLimite = 10 * 60 * 1000; // 10 minutos
const expiracoes = {};

function resetarAtendimento(telefone, inativo = false) {
  delete estados[telefone];
  delete estados[telefone + '_especialidade'];
  delete estados[telefone + '_nome'];
  delete estados[telefone + '_sus'];
  delete estados[telefone + '_rua'];
  delete estados[telefone + '_bairro'];
  clearTimeout(expiracoes[telefone]);
  delete expiracoes[telefone];
  if (inativo) {
    console.log(`Sessão encerrada por inatividade: ${telefone}`);
  }
}

function agendarTimeout(telefone, resolve) {
  clearTimeout(expiracoes[telefone]);
  expiracoes[telefone] = setTimeout(() => {
    resetarAtendimento(telefone, true);
    if (resolve) {
      resolve('⏳ Atendimento encerrado automaticamente por inatividade. Envie "oi" para iniciar novamente.');
    }
  }, tempoLimite);
}

async function handleMessage(body, senderId) {
  const telefone = senderId.replace('@c.us', '');
  const mensagem = body.trim().toLowerCase();

  console.log(`[${telefone}] Mensagem recebida: "${mensagem}"`);

  if (mensagem === 'encerrar') {
    resetarAtendimento(telefone);
    return '✅ Atendimento encerrado manualmente. Envie "oi" se desejar começar novamente.';
  }

  const estado = estados[telefone] || null;
  const saudacoes = ['oi', 'olá', 'bom dia', 'boa tarde', 'boa noite'];

  if (!estado && saudacoes.some(s => mensagem.includes(s))) {
    estados[telefone] = 'aguardando_escolha';
    agendarTimeout(telefone);
    console.log(`[${telefone}] Iniciando atendimento`);
    return `Olá, bem-vindo ao Disk Saúde de Antonina. 🩺
Eu sou o Disk Bot e irei auxiliar você na marcação da sua consulta.

Escolha a especialidade desejada:
1️⃣ Clínico Geral
2️⃣ Odontologia
3️⃣ Fisioterapia
4️⃣ Nutricionista
5️⃣ Mais Informações`;
  }

  if (!estado) {
    return '👋 Olá! Para começarmos, envie "oi".';
  }

  return new Promise((resolve) => {
    agendarTimeout(telefone, resolve);

    if (estado === 'aguardando_escolha') {
      const especialidades = {
        '1': 'Clínico Geral',
        '2': 'Odontologia',
        '3': 'Fisioterapia',
        '4': 'Nutricionista'
      };
      if (mensagem in especialidades) {
        estados[telefone] = 'coletando_dados';
        estados[telefone + '_especialidade'] = especialidades[mensagem];
        console.log(`[${telefone}] Escolheu: ${especialidades[mensagem]}`);
        return resolve('Vamos começar! Por favor, informe seu nome completo:');
      }
      if (mensagem === '5') {
        estados[telefone] = 'info_opcoes';
        return resolve(`ℹ️ Abaixo você encontra informações úteis. Escolha uma opção:
1️⃣ Transporte
2️⃣ TFD
3️⃣ Vacinação
4️⃣ Outras informações
5️⃣ Voltar para o menu principal`);
      }
      return resolve('❌ Opção inválida. Por favor, envie 1, 2, 3, 4 ou 5.');
    }

    if (estado === 'info_opcoes') {
      if (mensagem === '1') return resolve('🚐 *Transporte*: Agende com 48h de antecedência na Secretaria de Saúde.');
      if (mensagem === '2') return resolve('📋 *TFD*: Leve os documentos ao setor de regulação com o encaminhamento.');
      if (mensagem === '3') return resolve('💉 *Vacinação*: Vá até a unidade de saúde mais próxima com seu cartão.');
      if (mensagem === '4') {
        estados[telefone] = 'info_outros';
        return resolve('📝 Por favor, envie qual informação você deseja e encaminharemos ao setor responsável.');
      }
      if (mensagem === '5') {
        estados[telefone] = 'aguardando_escolha';
        return resolve(`Voltando ao menu principal...

Escolha a especialidade desejada:
1️⃣ Clínico Geral
2️⃣ Odontologia
3️⃣ Fisioterapia
4️⃣ Nutricionista
5️⃣ Mais Informações`);
      }
      return resolve('❌ Opção inválida. Envie 1, 2, 3, 4 ou 5.');
    }

    if (estado === 'info_outros') {
      return resolve('📨 Obrigado! Sua solicitação será analisada por nossa equipe.');
    }

    if (estado === 'coletando_dados') {
      if (!estados[telefone + '_nome']) {
        estados[telefone + '_nome'] = body;
        return resolve('Agora informe o número do cartão SUS:');
      }
      if (!estados[telefone + '_sus']) {
        estados[telefone + '_sus'] = body;
        return resolve('Informe o nome da rua:');
      }
      if (!estados[telefone + '_rua']) {
        estados[telefone + '_rua'] = body;
        return resolve('Por fim, informe o bairro:');
      }
      if (!estados[telefone + '_bairro']) {
        estados[telefone + '_bairro'] = body;

        const nome = estados[telefone + '_nome'];
        const sus = estados[telefone + '_sus'];
        const rua = estados[telefone + '_rua'];
        const bairro = estados[telefone + '_bairro'];
        const especialidade = estados[telefone + '_especialidade'];

        estados[telefone] = 'confirmando_dados';
        return resolve(`📝 Por favor, confirme os dados informados:

👤 *Nome:* ${nome}  
🆔 *Cartão SUS:* ${sus}  
🏠 *Rua:* ${rua}  
📍 *Bairro:* ${bairro}  
📌 *Especialidade:* ${especialidade}

Deseja confirmar o agendamento com esses dados? (responda "sim" ou "não")`);
      }
    }

    if (estado === 'confirmando_dados') {
      if (mensagem === 'sim') {
        const nome = estados[telefone + '_nome'];
        const sus = estados[telefone + '_sus'];
        const rua = estados[telefone + '_rua'];
        const bairro = estados[telefone + '_bairro'];
        const especialidade = estados[telefone + '_especialidade'];
        const path = require('path');
        const scriptPath = path.resolve(__dirname, 'salvar_agendamento.py');
        const comando = `python "${scriptPath}" "${nome}" "${telefone}" "${sus}" "${rua}" "${bairro}" "${especialidade}"`;

        console.log(`[${telefone}] Dados confirmados. Executando: ${comando}`);

        exec(comando, (error, stdout, stderr) => {
          if (error) {
            console.error(`[${telefone}] Erro ao executar Python:`, stderr);
            return resolve('⚠️ Ocorreu um erro ao tentar agendar. Tente novamente mais tarde.');
          }

          resetarAtendimento(telefone);
          resolve(`✅ ${stdout.trim()}\n\nSe quiser agendar outro atendimento, envie "oi".`);
        });
      } else if (mensagem === 'não' || mensagem === 'nao') {
        resetarAtendimento(telefone);
        return resolve('❌ Dados descartados. Envie "oi" para iniciar novamente.');
      } else {
        return resolve('❓ Por favor, responda com "sim" para confirmar ou "não" para cancelar.');
      }
    }
  });
}

module.exports = handleMessage;
