(() => {
  const nav = document.querySelector('.dashboard-tabs');
  if (!nav) return;
  const links = [...nav.querySelectorAll('a'), ...document.querySelectorAll('[data-dashboard-section]')];
  const panels = links.map(link => document.querySelector(link.hash));
  const overview = document.querySelector('[data-dashboard-overview]');
  function select() {
    const index = Math.max(0, links.findIndex(link => link.hash === location.hash));
    links.forEach((link, i) => {
      if (i === index) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
      if (link.hasAttribute('data-dashboard-section')) link.classList.toggle('active', i === index);
      panels[i].hidden = i !== index;
    });
    const isOverview = !links[index].hasAttribute('data-dashboard-section');
    overview.classList.toggle('active', isOverview);
    if (isOverview) overview.setAttribute('aria-current', 'page');
    else overview.removeAttribute('aria-current');
  }
  links.forEach(link => link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    history.pushState(null, '', link.hash);
    select();
  }));
  window.addEventListener('hashchange', select);
  window.addEventListener('popstate', select);
  select();
})();
