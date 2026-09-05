/* Navigation and progressively enhanced, currency-aware wishlist filtering. */
(() => {
  'use strict';
  const header = document.querySelector('.site-header');
  const menu = document.querySelector('.menu-toggle');
  const navigation = document.querySelector('#site-navigation');
  if (header && menu && navigation) {
    header.classList.add('js-navigation');
    menu.hidden = false;
    const close = (restoreFocus = false) => {
      menu.setAttribute('aria-expanded', 'false');
      navigation.classList.remove('is-open');
      if (restoreFocus) menu.focus();
    };
    menu.addEventListener('click', () => {
      const open = menu.getAttribute('aria-expanded') !== 'true';
      menu.setAttribute('aria-expanded', String(open));
      navigation.classList.toggle('is-open', open);
    });
    header.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') close(true);
    });
    document.addEventListener('click', (event) => { if (!header.contains(event.target)) close(); });
    navigation.addEventListener('click', (event) => { if (event.target.closest('a')) close(); });
    window.matchMedia('(min-width: 761px)').addEventListener('change', () => close());
  }

  document.querySelectorAll('[data-wishlist]').forEach((root) => {
    const cards = [...root.querySelectorAll('[data-wish]')];
    const category = root.querySelector('[data-filter-category]');
    const status = root.querySelector('[data-filter-status]');
    const currency = root.querySelector('[data-filter-currency]');
    const budget = root.querySelector('[data-filter-budget]');
    const reset = root.querySelector('[data-filter-reset]');
    const count = root.querySelector('[data-filter-count]');
    const empty = root.querySelector('[data-filter-empty]');
    const toolbar = root.querySelector('.wishlist-toolbar');
    if (!category || !status || !currency || !budget || !toolbar) return;
    const selected = (control) => control.value === 'all' ? '' : control.value;
    if (count) { count.setAttribute('role', 'status'); count.setAttribute('aria-live', 'polite'); count.setAttribute('aria-atomic', 'true'); }
    const update = () => {
      const categoryValue = selected(category);
      const statusValue = selected(status);
      const currencyValue = selected(currency);
      budget.disabled = !currencyValue;
      budget.title = currencyValue ? 'Максимальная цена в выбранной валюте' : 'Сначала выберите валюту';
      const rawBudget = budget.value.trim();
      const numericBudget = Number(rawBudget);
      const hasBudget = Boolean(currencyValue && rawBudget !== '' && Number.isFinite(numericBudget) && numericBudget >= 0);
      let visible = 0;
      cards.forEach((card) => {
        const rawPrice = card.dataset.price || '';
        const price = Number(rawPrice);
        const hasPrice = rawPrice !== '' && Number.isFinite(price);
        const matches = (!categoryValue || card.dataset.category === categoryValue)
          && (!statusValue || card.dataset.status === statusValue)
          && (!currencyValue || !hasPrice || card.dataset.currency === currencyValue)
          && (!hasBudget || !hasPrice || price <= numericBudget);
        card.hidden = !matches;
        if (matches) visible += 1;
      });
      if (count) count.textContent = `Показано: ${visible} из ${cards.length}`;
      if (empty) empty.hidden = visible !== 0;
    };
    [category, status, currency].forEach((control) => control.addEventListener('change', update));
    budget.addEventListener('input', update);
    if (reset) reset.addEventListener('click', () => {
      [category, status, currency].forEach((control) => { control.selectedIndex = 0; });
      budget.value = '';
      update();
    });
    update();
    toolbar.hidden = false;
    root.classList.add('filters-ready');
  });
})();
