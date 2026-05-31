(function () {
  const storageKey = 'theme';
  const root = document.documentElement;
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

  function getPreferredTheme() {
    const savedTheme = localStorage.getItem(storageKey);
    if (savedTheme === 'dark' || savedTheme === 'light') {
      return savedTheme;
    }
    return mediaQuery.matches ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    root.style.colorScheme = theme;
  }

  function updateToggleLabel(toggle, theme) {
    if (!toggle) return;
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    const label = `Switch to ${nextTheme} mode`;
    toggle.setAttribute('aria-label', label);
    toggle.setAttribute('title', label);
  }

  function syncTheme(toggle) {
    const theme = getPreferredTheme();
    applyTheme(theme);
    updateToggleLabel(toggle, theme);
  }

  document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('themeToggle');
    syncTheme(toggle);

    if (!toggle) return;

    toggle.addEventListener('click', () => {
      const currentTheme = root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
      const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
      localStorage.setItem(storageKey, nextTheme);
      applyTheme(nextTheme);
      updateToggleLabel(toggle, nextTheme);
    });

    const handleSystemThemeChange = (event) => {
      const savedTheme = localStorage.getItem(storageKey);
      if (savedTheme === 'dark' || savedTheme === 'light') return;
      const systemTheme = event.matches ? 'dark' : 'light';
      applyTheme(systemTheme);
      updateToggleLabel(toggle, systemTheme);
    };

    if (typeof mediaQuery.addEventListener === 'function') {
      mediaQuery.addEventListener('change', handleSystemThemeChange);
    } else if (typeof mediaQuery.addListener === 'function') {
      mediaQuery.addListener(handleSystemThemeChange);
    }
  });
})();
