const venom = require('venom-bot');
const { exec } = require('child_process');
const handleMessage = require('../router'); // <-- Importa o seu router.js

venom
  .create({
    session: 'diskbot-whatsapp',
    multidevice: true
  })
  .then((client) => start(client))
  .catch((error) => {
    console.log('Erro ao iniciar o Venom:', error);
  });

function start(client) {
  client.onMessage(async (message) => {
    if (message.isGroupMsg === false && message.body) {
      const resposta = await handleMessage(message.body, message.from);
      if (resposta) {
        client.sendText(message.from, resposta);
      }
    }
  });
}
