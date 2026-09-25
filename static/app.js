(() => {
  const $ = (s, root=document) => root.querySelector(s);
  const $$ = (s, root=document) => [...root.querySelectorAll(s)];
  const prefersReduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  function toast(message, type='success') {
    const stack = $('#toast-stack');
    if (!stack) return;
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = message;
    stack.appendChild(el);
    setTimeout(() => el.remove(), 2800);
  }
  window.exerxToast = toast;

  // Keep desktop and mobile navigation in sync with the current route.
  const currentPath = location.pathname;
  $$('[data-path]').forEach(link => {
    const target = link.dataset.path || '/';
    const active = target === '/' ? currentPath === '/' : currentPath === target || currentPath.startsWith(target + '/');
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page');
  });

  // Motion and animated analytics
  const revealObserver = !prefersReduced && 'IntersectionObserver' in window ? new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      revealObserver.unobserve(entry.target);
    });
  }, {threshold:.08}) : null;
  $$('.reveal').forEach(el => revealObserver ? revealObserver.observe(el) : el.classList.add('is-visible'));
  $$('.animated-bar').forEach(el => revealObserver ? revealObserver.observe(el) : el.classList.add('is-visible'));

  if (!prefersReduced) {
    $$('.count-up').forEach(el => {
      const target = Number(el.dataset.count || el.textContent || 0);
      if (!Number.isFinite(target) || target <= 0) return;
      const start = performance.now();
      const duration = 550;
      const tick = now => {
        const p = Math.min(1, (now-start)/duration);
        el.textContent = Math.round(target * (1 - Math.pow(1-p, 3))).toLocaleString();
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }

  // AJAX favorites
  $$('.js-favorite-form').forEach(form => form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = $('button', form);
    button.disabled = true;
    try {
      const response = await fetch(form.action, {method:'POST', headers:{'X-Requested-With':'fetch','Accept':'application/json'}});
      if (!response.ok) throw new Error('Favorite update failed');
      const data = await response.json();
      button.classList.toggle('active', data.favorite);
      button.classList.add('just-saved');
      setTimeout(() => button.classList.remove('just-saved'), 420);
      if (button.matches('[data-favorite-label]')) {
        button.textContent = data.favorite ? '★ Saved exercise' : '☆ Save exercise';
        button.classList.toggle('btn-primary', data.favorite);
        button.classList.toggle('btn-secondary', !data.favorite);
      } else {
        button.textContent = data.favorite ? '★' : '☆';
      }
      const total = $('#favorite-total');
      if (total) total.textContent = data.favorites;
      toast(data.favorite ? 'Saved to favorites' : 'Removed from favorites');
    } catch (error) {
      toast(error.message, 'error');
    } finally { button.disabled = false; }
  }));

  // Confirm destructive forms
  $$('form[data-confirm]').forEach(form => form.addEventListener('submit', event => {
    if (!confirm(form.dataset.confirm || 'Are you sure?')) event.preventDefault();
  }));

  // Copy exercise summary
  $$('[data-copy-exercise]').forEach(button => button.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(button.dataset.copyText || ''); toast('Exercise details copied'); }
    catch { toast('Could not copy details', 'error'); }
  }));

  // Compare tray (localStorage; up to 3)
  const compareKey = 'exerxeye-compare-v1';
  const readCompare = () => { try { return JSON.parse(localStorage.getItem(compareKey) || '[]'); } catch { return []; } };
  const writeCompare = value => { try { localStorage.setItem(compareKey, JSON.stringify(value)); } catch {} };
  const tray = $('#compare-tray');
  const count = $('#compare-count');
  function renderCompareState() {
    const selected = readCompare();
    if (tray) tray.hidden = selected.length === 0;
    if (count) count.textContent = `${selected.length} of 3 selected`;
    $$('.compare-button').forEach(button => {
      const on = selected.some(item => String(item.id) === String(button.dataset.compareId));
      button.classList.toggle('selected', on);
    });
  }
  $$('.compare-button').forEach(button => button.addEventListener('click', () => {
    let selected = readCompare();
    const id = Number(button.dataset.compareId);
    const found = selected.findIndex(item => item.id === id);
    if (found >= 0) selected.splice(found, 1);
    else if (selected.length >= 3) return toast('Compare up to 3 exercises', 'error');
    else selected.push({id, name:button.dataset.compareName});
    writeCompare(selected); renderCompareState();
  }));
  $('#compare-clear')?.addEventListener('click', () => { writeCompare([]); renderCompareState(); });
  const compareModal = $('#compare-modal');
  const closeCompare = () => { if (compareModal) compareModal.hidden = true; };
  $$('[data-modal-close]').forEach(el => el.addEventListener('click', closeCompare));
  $('#compare-open')?.addEventListener('click', async () => {
    const selected = readCompare();
    if (selected.length < 2) return toast('Choose at least 2 exercises to compare', 'error');
    const content = $('#compare-content');
    compareModal.hidden = false;
    content.innerHTML = '<div class="compare-empty">Loading comparison…</div>';
    try {
      const data = await Promise.all(selected.map(item => fetch(`/api/exercises/${item.id}`).then(r => r.json())));
      content.innerHTML = data.map(raw => {
        const e = raw.exercise || raw;
        const esc = value => String(value ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
        return `<article class="compare-column"><span class="eyebrow">${esc(e.main_muscle || 'Exercise')}</span><h3>${esc(e.exercise_name)}</h3><div class="compare-spec"><span>Equipment</span><strong>${esc(e.equipment || 'Bodyweight')}</strong></div><div class="compare-spec"><span>Difficulty</span><strong>${esc(e.difficulty)}/5</strong></div><div class="compare-spec"><span>Mechanics</span><strong>${esc(e.mechanics)}</strong></div><div class="compare-spec"><span>Force</span><strong>${esc(e.force)}</strong></div><div class="compare-spec"><span>Target muscles</span><strong>${esc(e.target_muscles)}</strong></div><div class="compare-spec"><span>Utility</span><strong>${esc(e.utility)}</strong></div><a class="btn btn-secondary btn-small" href="/exercise/${e.id}">Open exercise</a></article>`;
      }).join('');
    } catch { content.innerHTML = '<div class="compare-empty">Could not load comparison.</div>'; }
  });
  renderCompareState();

  // Command palette + keyboard navigation
  const commandModal = $('#command-modal');
  const commandInput = $('#command-input');
  const openCommand = () => { commandModal.hidden = false; setTimeout(() => commandInput?.focus(), 20); };
  const closeCommand = () => { commandModal.hidden = true; if (commandInput) commandInput.value=''; $$('[data-command-item]').forEach(x => x.hidden=false); };
  $$('[data-command-open]').forEach(x => x.addEventListener('click', openCommand));
  $$('[data-command-close]').forEach(x => x.addEventListener('click', closeCommand));
  commandInput?.addEventListener('input', () => {
    const q = commandInput.value.trim().toLowerCase();
    $$('[data-command-item]').forEach(item => item.hidden = q && !(item.dataset.label || '').includes(q));
  });
  $('#command-theme')?.addEventListener('click', () => {
    const mode = window.ExerxEyeTheme?.toggle?.();
    closeCommand();
    toast(mode === 'dark' ? 'Dark mode on' : 'Light mode on');
  });
  document.addEventListener('keydown', event => {
    const typing = /INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName || '');
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); openCommand(); return; }
    if (event.key === 'Escape') { closeCommand(); closeCompare(); }
    if (!typing && event.key === '/') { event.preventDefault(); $('#global-search-input')?.focus(); }
    if (!typing && event.key.toLowerCase() === 'r' && !event.metaKey && !event.ctrlKey) location.href='/random';
  });

  // Persistent rest timer
  const timerRoot = $('[data-rest-timer]');
  if (timerRoot) {
    const display = $('#timer-display');
    const toggle = $('#timer-toggle');
    const initialRest = Math.max(15, Math.min(600, Number(timerRoot.dataset.defaultRest || 60)));
    let duration = initialRest, remaining = initialRest, interval = null, deadline = null;
    const key = `exerxeye-rest-${location.pathname}-${new URLSearchParams(location.search).get('session') || 'active'}`;
    const fmt = n => `${String(Math.floor(n/60)).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`;
    const draw = () => { display.textContent=fmt(Math.max(0,remaining)); };
    const stop = (finished=false) => { clearInterval(interval); interval=null; deadline=null; toggle.textContent='Start'; toggle.classList.remove('running'); try{localStorage.removeItem(key)}catch{} if(finished){toast('Rest complete'); if(navigator.vibrate) navigator.vibrate([120,80,120]);} };
    const tick = () => { remaining=Math.max(0,Math.ceil((deadline-Date.now())/1000)); draw(); if(remaining<=0) stop(true); };
    const start = () => { if(remaining<=0) remaining=duration; deadline=Date.now()+remaining*1000; interval=setInterval(tick,250); toggle.textContent='Pause'; toggle.classList.add('running'); try{localStorage.setItem(key, JSON.stringify({deadline,duration}))}catch{} };
    $$('[data-rest]', timerRoot).forEach(btn => btn.addEventListener('click', () => { duration=Number(btn.dataset.rest); remaining=duration; $$('[data-rest]',timerRoot).forEach(x=>x.classList.toggle('active',x===btn)); if(interval) stop(); draw(); }));
    toggle.addEventListener('click', () => interval ? stop() : start());
    try { const saved=JSON.parse(localStorage.getItem(key)||'null'); if(saved?.deadline>Date.now()){ duration=saved.duration||60; remaining=Math.ceil((saved.deadline-Date.now())/1000); deadline=saved.deadline; interval=setInterval(tick,250); toggle.textContent='Pause'; toggle.classList.add('running'); draw(); } } catch {}
    draw();
  }
})();

// ExerxEye v5: richer motion, auth helpers, and export feedback.
(() => {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $$ = (selector, root=document) => Array.from(root.querySelectorAll(selector));
  const $ = (selector, root=document) => root.querySelector(selector);

  // Password visibility + signup strength feedback.
  $$('[data-password-toggle]').forEach(button => button.addEventListener('click', () => {
    const input = $(button.dataset.passwordToggle);
    if (!input) return;
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    button.textContent = show ? 'Hide' : 'Show';
  }));
  const password = $('#signup-password');
  const confirm = $('#signup-confirm');
  const strengthBar = $('#password-strength-bar');
  const strengthCopy = $('#password-strength-copy');
  const match = $('#password-match');
  const scorePassword = value => {
    let score = 0;
    if (value.length >= 8) score++;
    if (value.length >= 12) score++;
    if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score++;
    if (/\d/.test(value)) score++;
    if (/[^A-Za-z0-9]/.test(value)) score++;
    return Math.min(score, 4);
  };
  const drawPassword = () => {
    if (!password || !strengthBar) return;
    const score = scorePassword(password.value);
    const widths = ['0%','28%','52%','76%','100%'];
    const colors = ['var(--danger)','var(--danger)','var(--accent-strong)','var(--accent)','var(--accent)'];
    const labels = ['Use 8+ characters.','Weak — add length and variety.','Fair — keep going.','Strong password.','Very strong password.'];
    strengthBar.style.width = widths[score];
    strengthBar.style.background = colors[score];
    if (strengthCopy) strengthCopy.textContent = labels[score];
    if (confirm && match) {
      if (!confirm.value) match.textContent = '';
      else if (confirm.value === password.value) { match.textContent = '✓'; match.style.color='var(--accent)'; }
      else { match.textContent = '×'; match.style.color='var(--danger)'; }
    }
  };
  password?.addEventListener('input', drawPassword);
  confirm?.addEventListener('input', drawPassword);

  // Visual motion is intentionally restrained in the V9 design.

  // Export cards give immediate download feedback without delaying downloads.
  $$('[data-download]').forEach(link => link.addEventListener('click', () => {
    window.exerxToast?.('Preparing download…');
  }));

  // Celebration burst after completing a workout.
  if (document.body.dataset.celebrate === '1' && !prefersReduced) {
    const layer = $('#celebration-layer');
    if (layer) {
      const tones = ['var(--accent)','var(--accent-strong)','var(--text)','var(--muted)'];
      for (let i=0; i<42; i++) {
        const p = document.createElement('i');
        p.className = 'celebration-particle';
        const angle = Math.random() * Math.PI * 2;
        const distance = 110 + Math.random()*260;
        p.style.setProperty('--dx', `${Math.cos(angle)*distance}px`);
        p.style.setProperty('--dy', `${Math.sin(angle)*distance - 80}px`);
        p.style.setProperty('--rot', `${Math.floor(Math.random()*720-360)}deg`);
        p.style.setProperty('--particle', tones[i % tones.length]);
        p.style.animationDelay = `${Math.random()*.16}s`;
        layer.appendChild(p);
      }
      setTimeout(() => layer.replaceChildren(), 1600);
    }
  }

})();

// ExerxEye v6: installable shell + small training UX upgrades.
(() => {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => navigator.serviceWorker.register('/service-worker.js').catch(() => {}));
  }

  // Auto-start the selected rest timer after a successful set form submit on the next page load.
  document.querySelectorAll('.session-log-form').forEach(form => {
    form.addEventListener('submit', () => {
      try { sessionStorage.setItem('exerxeye-auto-rest', '1'); } catch (_) {}
    });
  });
  try {
    if (sessionStorage.getItem('exerxeye-auto-rest') === '1') {
      sessionStorage.removeItem('exerxeye-auto-rest');
      setTimeout(() => document.querySelector('#timer-toggle')?.click(), 180);
    }
  } catch (_) {}
})();

// Install prompt when the browser exposes PWA installation.
(() => {
  let installPrompt = null;
  const button = document.querySelector('#pwa-install');
  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    installPrompt = event;
    if (button) button.hidden = false;
  });
  button?.addEventListener('click', async () => {
    if (!installPrompt) return;
    installPrompt.prompt();
    await installPrompt.userChoice.catch(() => null);
    installPrompt = null;
    button.hidden = true;
  });
  window.addEventListener('appinstalled', () => { if (button) button.hidden = true; });
})();

// ExerxEye V10: organized navigation, generator helpers, recent history, session focus.
(() => {
  const $ = (s, root=document) => root.querySelector(s);
  const $$ = (s, root=document) => Array.from(root.querySelectorAll(s));

  // Highlight grouped navigation based on the current route and close menus after selection.
  $$('.nav-menu').forEach(menu => {
    const prefixes = (menu.dataset.navPrefix || '').split(',').filter(Boolean);
    menu.classList.toggle('route-active', prefixes.some(prefix => location.pathname.startsWith(prefix)));
    $$('a', menu).forEach(link => link.addEventListener('click', () => menu.removeAttribute('open')));
  });
  document.addEventListener('click', event => {
    $$('.nav-menu[open]').forEach(menu => {
      if (!menu.contains(event.target)) menu.removeAttribute('open');
    });
  });

  // Workout generator preset shortcuts and conditional custom-muscle control.
  const generatorPreset = $('#generator-preset');
  const customField = $('#generator-custom');
  const syncGenerator = () => {
    if (!generatorPreset || !customField) return;
    customField.hidden = generatorPreset.value !== 'custom';
  };
  generatorPreset?.addEventListener('change', syncGenerator);
  $$('[data-generator-preset]').forEach(button => button.addEventListener('click', () => {
    if (!generatorPreset) return;
    generatorPreset.value = button.dataset.generatorPreset;
    syncGenerator();
    $('#generator-form')?.scrollIntoView({behavior:'smooth', block:'center'});
  }));
  syncGenerator();

  // Recently viewed exercises live only in this browser and never affect account data.
  const recentKey = 'exerxeye-recent-exercises-v1';
  const recentRoot = $('#recently-viewed');
  const recentStrip = $('#recent-exercise-strip');
  const drawRecent = () => {
    if (!recentRoot || !recentStrip) return;
    let rows = [];
    try { rows = JSON.parse(localStorage.getItem(recentKey) || '[]'); } catch (_) {}
    recentRoot.hidden = rows.length === 0;
    recentStrip.innerHTML = rows.map(item => {
      const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
      return `<a class="recent-exercise-card" href="/exercise/${Number(item.id)}"><span>${esc(item.muscle || 'Exercise')}</span><strong>${esc(item.name)}</strong><small>${esc(item.equipment || 'Bodyweight')} · Open ↗</small></a>`;
    }).join('');
  };
  $('#recent-clear')?.addEventListener('click', () => {
    try { localStorage.removeItem(recentKey); } catch (_) {}
    drawRecent();
  });
  drawRecent();

  // Quick rep/weight adjustment buttons during an active session.
  $$('.workout-exercise-card').forEach(card => {
    $$('[data-adjust]', card).forEach(button => button.addEventListener('click', () => {
      const input = $(`input[name="${button.dataset.adjust}"]`, card);
      if (!input) return;
      const step = Number(button.dataset.step || 0);
      const current = Number(input.value || 0);
      const min = Number(input.min || 0);
      input.value = Math.max(min, current + step);
      input.dispatchEvent(new Event('change', {bubbles:true}));
    }));
  });

  // Move directly to the first exercise that has not reached its planned set count.
  $('#jump-next-exercise')?.addEventListener('click', () => {
    const next = $$('[data-session-exercise]').find(card => Number(card.dataset.loggedSets || 0) < Number(card.dataset.plannedSets || 0));
    if (!next) {
      window.exerxToast?.('All planned sets are complete');
      return;
    }
    next.scrollIntoView({behavior:'smooth', block:'center'});
    next.classList.remove('session-focus-highlight');
    requestAnimationFrame(() => next.classList.add('session-focus-highlight'));
    setTimeout(() => next.classList.remove('session-focus-highlight'), 900);
  });

  // Keep keyboard focus sensible after an AJAX-style favorite / modal interaction.
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') $$('.nav-menu[open]').forEach(menu => menu.removeAttribute('open'));
  });
})();
