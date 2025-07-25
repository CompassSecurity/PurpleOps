document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById('themeToggleBtn');
  if (!toggleBtn) return;

  toggleBtn.addEventListener('click', () => {
    const currentTheme = getCookie('theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.cookie = `theme=${newTheme}; path=/; max-age=31536000; Secure; SameSite=Strict`; // 1 year
    location.reload();
  });

  function getCookie(name) {
    return document.cookie.split('; ').find(row => row.startsWith(name + '='))?.split('=')[1];
  }
});
