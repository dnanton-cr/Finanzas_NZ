// parser.js — Port a JavaScript de parse_bac.py (parser BAC → transacciones).
// Funciona en navegador (global) y en Node (module.exports).
// Dos modos:
//   - parseBac():          texto con un campo por línea (salida de pymupdf).
//   - parseBacFromPdfjs(): texto con una transacción por línea (salida de pdf.js).
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.FinanzasParser = factory();
}(typeof self !== 'undefined' ? self : this, function () {

  const MESES = { ENE:1,FEB:2,MAR:3,ABR:4,MAY:5,JUN:6,JUL:7,AGO:8,SEP:9,OCT:10,NOV:11,DIC:12 };
  const PAISES = { DEU:'Alemania',CRI:'Costa Rica',USA:'Estados Unidos',SGP:'Singapur',LUX:'Luxemburgo',LTU:'Lituania',HKG:'Hong Kong',NLD:'Países Bajos',GBR:'Reino Unido' };
  const NOISE = new Set(['TARJETA DE CREDITO','N. Referencia','Fecha de pago','Concepto/Descripción','Lugar','Moneda','Monto en colones','Monto en dólares','Movimientos de la tarjeta de crédito']);
  const CARD_RE = /^\*{6,}(\d{4})$/;
  const REF_RE = /^\d{9,14}$/;
  const DATE_RE = /^(\d{1,2})-(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)-(\d{2})$/i;
  const PAD = n => String(n).padStart(2, '0');

  function parseMonto(s) {
    s = String(s).trim().replace(/,/g, '');
    const neg = s.endsWith('-');
    if (neg) s = s.slice(0, -1);
    const v = parseFloat(s);
    return isNaN(v) ? null : (neg ? -v : v);
  }

  function parseFecha(s) {
    const m = DATE_RE.exec(String(s).trim());
    if (!m) return null;
    return (2000 + parseInt(m[3], 10)) + '-' + PAD(MESES[m[2].toUpperCase()]) + '-' + PAD(parseInt(m[1], 10));
  }

  function extraerLugar(desc) {
    const c = desc.match(/\b([A-Z]{3})\b/g) || [];
    for (let i = c.length - 1; i >= 0; i--) if (PAISES[c[i]]) return c[i];
    return null;
  }

  function categorizar(desc, cfg) {
    const d = desc.toLowerCase();
    for (const cat of (cfg.categorias || [])) {
      for (const kw of (cat.keywords || [])) {
        if (d.includes(kw.toLowerCase())) return cat.nombre;
      }
    }
    return cfg.otros_nombre || 'Otros';
  }

  function aUsd(moneda, monto, cfg) {
    if (moneda === 'CRC') return Math.round(monto / (cfg.tasa_usd_crc || 445) * 100) / 100;
    if (moneda === 'EUR') return Math.round(monto * (cfg.tasa_eur_usd || 1.08) * 100) / 100;
    return monto;
  }

  function buildTx(descCompleta, cfg, extra) {
    const lugar = extraerLugar(descCompleta);
    return Object.assign({
      descripcion: descCompleta,
      lugar: PAISES[lugar] || lugar || null,
      categoria: categorizar(descCompleta, cfg)
    }, extra);
  }

  // ── parseo del texto "un campo por línea" (pymupdf) ──
  function parseBac(texto, cfg) {
    const lines = String(texto).split('\n');
    let start = -1, end = -1;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('Detalle de compras del periodo') && start === -1) start = i;
      if (lines[i].includes('Total de compras del periodo') && start !== -1) { end = i; break; }
    }
    if (start === -1 || end === -1) throw new Error("No se encontró la sección 'Detalle de compras del periodo'.");

    const section = lines.slice(start, end);
    const segmentos = [];
    for (let i = 0; i < section.length; i++) {
      const m = CARD_RE.exec(section[i].trim());
      if (m) {
        let j = i + 1;
        while (j < section.length) { const s = section[j].trim(); if (s && !NOISE.has(s)) break; j++; }
        segmentos.push([m[1], j < section.length ? section[j].trim() : '', j]);
      }
    }

    const personas = cfg.personas || {};
    const nombrePersona = (card, crudo) => personas[card] || (crudo ? crudo.split('/')[0].trim() : card);

    const tx = [];
    for (let idx = 0; idx < segmentos.length; idx++) {
      const card = segmentos[idx][0], nombreCrudo = segmentos[idx][1], nombreIdx = segmentos[idx][2];
      const fin = idx + 1 < segmentos.length ? segmentos[idx + 1][2] : section.length;
      const limpio = section.slice(nombreIdx + 1, fin)
        .map(l => l.trim())
        .filter(l => l && !NOISE.has(l) && !l.startsWith('B) Detalle') && !l.startsWith('Movimientos') && !l.startsWith('Página'));
      const persona = nombrePersona(card, nombreCrudo);

      let i = 0; const n = limpio.length;
      while (i < n) {
        if (!REF_RE.test(limpio[i])) { i++; continue; }
        const ref = limpio[i]; i++;
        if (i >= n) break;
        const fecha = parseFecha(limpio[i]); i++;
        const descParts = [];
        while (i < n && limpio[i] !== 'USD' && limpio[i] !== 'CRC' && limpio[i] !== 'EUR' && !REF_RE.test(limpio[i])) { descParts.push(limpio[i]); i++; }
        if (i >= n) break;
        const moneda = limpio[i]; i++;
        if (i >= n) break;
        const monto = parseMonto(limpio[i]); i++;
        const desc = descParts.join(' ').trim();
        tx.push(buildTx(desc, cfg, { fecha, mes: fecha ? fecha.slice(0, 7) : null, persona, tarjeta: card, referencia: ref, moneda, monto, monto_usd: aUsd(moneda, monto || 0, cfg) }));
      }
    }
    return tx;
  }

  // ── parseo del texto "una transacción por línea" (pdf.js) ──
  function parseBacFromPdfjs(texto, cfg) {
    const lines = String(texto).split('\n');
    let start = -1, end = -1;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('Detalle de compras del periodo') && start === -1) start = i;
      if (lines[i].includes('Total de compras del periodo') && start !== -1) { end = i; break; }
    }
    if (start === -1 || end === -1) throw new Error("No se encontró la sección 'Detalle de compras del periodo'.");

    const personas = cfg.personas || {};
    const tx = [];
    let card = null, persona = null, noReconocidas = 0;

    for (let i = start + 1; i < end; i++) {
      const l = lines[i].trim();
      if (!l) continue;
      const cm = /^\*{6,}(\d{4})\s+(.+)$/.exec(l);
      if (cm) { card = cm[1]; persona = personas[card] || cm[2].split('/')[0].trim(); continue; }
      if (/^(B\) Detalle|N\. Referencia|Fecha de pago|Concepto\/Descripción|Movimientos|TARJETA DE CREDITO|Página|colones|dólares)/.test(l)) continue;

      const parts = l.split(/\s{2,}/);
      if (parts.length >= 5 && REF_RE.test(parts[0])) {
        const ref = parts[0];
        const fecha = parseFecha(parts[1]);
        const moneda = parts[parts.length - 2];
        const monto = parseMonto(parts[parts.length - 1]);
        const desc = (parts[2] + ' ' + parts.slice(3, parts.length - 2).join(' ')).trim();
        tx.push(buildTx(desc, cfg, { fecha, mes: fecha ? fecha.slice(0, 7) : null, persona, tarjeta: card, referencia: ref, moneda, monto, monto_usd: aUsd(moneda, monto || 0, cfg) }));
      } else {
        noReconocidas++;
      }
    }
    return { transacciones: tx, noReconocidas };
  }

  return { parseBac, parseBacFromPdfjs, parseMonto, parseFecha, categorizar, aUsd };
}));
