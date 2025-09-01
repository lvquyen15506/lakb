const express = require('express');
const nglSpam = require('./ngl_spam');
const app = express();

const PORT = 3000;

app.get('/ngl/user=:username/count=:count/message=:message', async (req, res) => {
  const { username, count, message } = req.params;
  const countNum = parseInt(count, 10);

  if (!username || !message || isNaN(countNum) || countNum <= 0) {
    return res.status(400).json({
      error: '❌ Sai hoặc thiếu tham số!\nDạng đúng: /ngl/user=<username>/count=<số>/message=<nội dung>'
    });
  }

  // Gửi phản hồi ngay
  res.json({
    status: '🚀 Đang gửi spam...',
    username,
    count: countNum,
    message
  });

  // Bắt đầu gửi nền
  const result = await nglSpam(username, countNum, message);
  console.log(`✅ Xong: gửi ${countNum} tin đến @${username} — Thành công: ${result.success}, Thất bại: ${result.bad}`);
});

app.listen(PORT, () => {
  console.log(`✅ Server đang chạy tại: http://localhost:${PORT}`);
});
