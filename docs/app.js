// ----------
// High smell nudge (≥60%)
// ----------

function showHighSmellNote() {
  const note = document.createElement('div');
  note.className = 'nudge high-smell-nudge';
  note.innerHTML = `
    <span>⚠️</span>
    <span class="high-smell-text">Este texto suena bastante a IA. Si lo escribiste tú y quieres que suene más humano, los hallazgos arriba te orientan.</span>
    <a href="https://intelecta.cl" target="_blank" rel="noopener" class="intelecta-link">📚 Edición profesional con Intelecta</a>
    <button class="dismiss">×</button>
  `;
  els.resultPanel.parentNode.insertBefore(note, els.resultPanel.nextSibling);
  
  note.querySelector('.dismiss').addEventListener('click', () => {
    note.style.opacity = '0';
    note.style.transform = 'translateY(8px)';
    setTimeout(() => note.remove(), 300);
  });
}

// ----------
// Fake bibliography warning
// ----------

function showBiblioFakeWarning(fakes, total) {
  const note = document.createElement('div');
  note.className = 'nudge biblio-fake-warning';
  note.innerHTML = `
    <span>🚨</span>
    <span class="biblio-fake-text">${fakes}/${total} referencias no existen — esto es grave si es tesis.</span>
    <a href="https://intelecta.cl/revision-academica" target="_blank" rel="noopener" class="intelecta-link">🔍 Revisión de bibliografía con Intelecta</a>
    <button class="dismiss">×</button>
  `;
  document.getElementById('resultPanel').parentNode.insertBefore(note, document.getElementById('resultPanel').nextSibling);
  
  note.querySelector('.dismiss').addEventListener('click', () => {
    note.style.opacity = '0';
    note.style.transform = 'translateY(8px)';
    setTimeout(() => note.remove(), 300);
  });
}

// ----------
// Main app (rest unchanged)
// ----------