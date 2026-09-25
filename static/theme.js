(() => {
  const root = document.documentElement;
  const storageKey = 'exerxeye-color-mode-v1';
  const buttons = () => [...document.querySelectorAll('#dark-mode-toggle')];
  const read = () => { try { return localStorage.getItem(storageKey); } catch (_) { return null; } };
  const save = value => { try { localStorage.setItem(storageKey, value); } catch (_) {} };
  const preferred = () => window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';

  function syncButton(mode) {
    buttons().forEach(button => {
      const dark = mode === 'dark';
      button.setAttribute('aria-pressed', dark ? 'true' : 'false');
      button.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
      const label = button.querySelector('.mode-label');
      if (label) label.textContent = dark ? 'Light' : 'Dark';
    });
  }

  function apply(mode, persist = true) {
    const next = mode === 'dark' ? 'dark' : 'light';
    root.dataset.colorMode = next;
    if (persist) save(next);
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = next === 'dark' ? '#090b08' : '#f4f5ef';
    syncButton(next);
    window.dispatchEvent(new CustomEvent('exerxeye:color-mode', { detail: { mode: next } }));
    return next;
  }

  function toggle() { return apply(root.dataset.colorMode === 'dark' ? 'light' : 'dark'); }

  const saved = read();
  apply(saved || root.dataset.colorMode || preferred(), Boolean(saved));
  document.addEventListener('click', event => {
    if (event.target.closest('#dark-mode-toggle')) toggle();
  });
  window.ExerxEyeTheme = { apply, toggle, current: () => root.dataset.colorMode || 'light' };
})();
