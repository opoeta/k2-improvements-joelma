const { chromium } = require('playwright');
(async () => {
  const SP = process.argv[2], MODO = process.argv[3];
  const b = await chromium.launch();
  for (const [nome, vp, mob] of [['cel', {width:390,height:844}, true], ['pc', {width:1280,height:900}, false]]) {
    const p = await (await b.newContext({ viewport: vp, deviceScaleFactor: mob ? 2 : 1, isMobile: mob, hasTouch: mob })).newPage();
    const erros = []; p.on('pageerror', e => erros.push(e.message));
    await p.goto('http://127.0.0.1:8080/calibra.html'); await p.waitForTimeout(8000);
    const vis = id => p.$eval(id, e => e.hidden ? '(oculto)' : e.innerText.replace(/\n/g,' '));
    console.log(MODO, nome, 'vivo:', await vis('#cfs-vivo'));
    console.log(MODO, nome, 'erro:', await vis('#cfs-erro'));
    console.log(MODO, nome, 'alerta arquivo:', await vis('#cfs-alerta'));
    console.log(MODO, nome, 'status:', await p.$eval('#fb-status', e => e.textContent));
    console.log(MODO, nome, 'slots:', await p.$$eval('.fb-slot', es => es.map(e => e.querySelector('.fb-tnn').textContent.split(' ')[0] + ':' + (e.querySelector('.fb-state') || {}).textContent).join(' ')));
    await p.screenshot({ path: `${SP}/w9_${MODO}_${nome}.png` });
    if (nome === 'pc') { await p.click('#cfs-erro-x'); await p.waitForTimeout(6000); console.log(MODO, 'erro apos fechar:', await vis('#cfs-erro')); }
    console.log(MODO, nome, 'erros JS:', erros.join(' | ') || 'nenhum');
  }
  await b.close();
})();
