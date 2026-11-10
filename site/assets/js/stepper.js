/*
 * Reusable click-through stepper. No dependencies, no network calls.
 *
 * Markup:
 *   <div class="stepper" id="demo">
 *     <section class="step" data-title="The problem"> <h2>…</h2> … </section>
 *     … (5-7 sections)
 *   </div>
 *
 * Usage:
 *   const s = Stepper.init('#demo', {
 *     onEnter: { 3: (stepEl, state) => { … render results … } },   // 1-based step numbers
 *     canLeave: { 2: (stepEl, state) => state.choice ? true : 'Pick an option to continue.' },
 *   });
 *   s.state  // shared object your step hooks can read and write
 *
 * The stepper builds the progress bar, the "Step n of N" line, the Back/Next
 * buttons, keeps #step-n in the URL (so a step can be linked), and moves
 * focus to each step's heading for screen-reader and keyboard users.
 */
(function () {
  function init(root, opts) {
    opts = opts || {};
    const el = typeof root === 'string' ? document.querySelector(root) : root;
    const steps = Array.from(el.querySelectorAll(':scope > .step'));
    const n = steps.length;
    const state = opts.state || {};
    let current = 0;

    const progress = document.createElement('ol');
    progress.className = 'stepper-progress';
    progress.setAttribute('aria-hidden', 'true');
    steps.forEach(() => progress.appendChild(document.createElement('li')));

    const count = document.createElement('p');
    count.className = 'stepper-count';
    count.setAttribute('aria-live', 'polite');

    const hint = document.createElement('p');
    hint.className = 'stepper-hint';
    hint.setAttribute('role', 'alert');

    const nav = document.createElement('div');
    nav.className = 'stepper-nav';
    const back = button('Back', 'btn');
    const next = button('Next', 'btn primary');
    nav.append(back, next);

    el.prepend(progress, count);
    el.append(hint, nav);

    steps.forEach((s, i) => {
      s.id = s.id || 'step-' + (i + 1);
      s.setAttribute('role', 'group');
      s.setAttribute('aria-label', 'Step ' + (i + 1) + ' of ' + n + ': ' + (s.dataset.title || ''));
      const h = s.querySelector('h2');
      if (h) h.tabIndex = -1;
    });

    function button(label, cls) {
      const b = document.createElement('button');
      b.type = 'button'; b.className = cls; b.textContent = label;
      return b;
    }

    function show(i, focus) {
      current = Math.max(0, Math.min(n - 1, i));
      steps.forEach((s, j) => { s.hidden = j !== current; });
      Array.from(progress.children).forEach((li, j) => {
        li.className = j < current ? 'done' : j === current ? 'current' : '';
      });
      const title = steps[current].dataset.title;
      count.textContent = 'Step ' + (current + 1) + ' of ' + n + (title ? ': ' + title : '');
      back.disabled = current === 0;
      next.textContent = current === n - 1 ? 'Start over' : 'Next';
      hint.textContent = '';
      const hook = opts.onEnter && opts.onEnter[current + 1];
      if (hook) hook(steps[current], state);
      if (history.replaceState) history.replaceState(null, '', '#step-' + (current + 1));
      if (focus) {
        const h = steps[current].querySelector('h2');
        if (h) h.focus();
        el.scrollIntoView({ block: 'start', behavior: 'auto' });
      }
    }

    function tryLeave() {
      const guard = opts.canLeave && opts.canLeave[current + 1];
      if (!guard) return true;
      const r = guard(steps[current], state);
      if (r === true) return true;
      hint.textContent = typeof r === 'string' ? r : 'Complete this step to continue.';
      return false;
    }

    next.addEventListener('click', () => {
      if (current === n - 1) { show(0, true); return; }
      if (tryLeave()) show(current + 1, true);
    });
    back.addEventListener('click', () => show(current - 1, true));

    // Deep links only go as far as the first step that has an unmet guard.
    const m = /^#step-(\d+)$/.exec(location.hash);
    let start = m ? parseInt(m[1], 10) - 1 : 0;
    for (let i = 0; i < start; i++) {
      const g = opts.canLeave && opts.canLeave[i + 1];
      if (g && g(steps[i], state) !== true) { start = i; break; }
    }
    show(start, false);

    return { state, show: (i) => show(i - 1, true), get current() { return current + 1; } };
  }

  window.Stepper = { init };
})();
