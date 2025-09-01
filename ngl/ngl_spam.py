const fs = require('fs');
const path = require('path');
const axios = require('axios');

// Load user-agents tu file
function loadUserAgents() {
  const filePath = path.join(__dirname, 'user_agents.txt');
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    return content.split('\n').filter(line => line.trim() !== '');
  } catch {
    console.warn('[!] Khong tim thay user_agents.txt — dung mac đinh.');
    return [
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)..."
    ];
  }
}

const userAgents = loadUserAgents();

// Ham gui spam đen NGL
async function nglSpam(username, count, message) {
  let success = 0, bad = 0;

  for (let i = 0; i < count; i++) {
    const headers = {
      'Host': 'ngl.link',
      'accept': '*/*',
      'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'user-agent': userAgents[Math.floor(Math.random() * userAgents.length)],
      'origin': 'https://ngl.link',
      'referer': `https://ngl.link/${username}`,
    };

    const data = new URLSearchParams({
      username,
      question: message,
      deviceId: 'ABCDEF1234567890',
      gameSlug: '',
      referrer: ''
    });

    try {
      const res = await axios.post('https://ngl.link/api/submit', data, { headers });
      if (res.status === 200) {
        success++;
      } else {
        bad++;
      }
    } catch (e) {
      bad++;
    }

    await new Promise(r => setTimeout(r, 1000)); // cho 1s
  }

  return { success, bad };
}

module.exports = nglSpam;
