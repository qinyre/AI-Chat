// ==================== 主题管理 ====================

const themeBtn = document.getElementById('theme-btn');

function toggleTheme() {
    const isLight = document.body.classList.contains('light-theme');
    applyTheme(isLight ? 'dark' : 'light');
}

function applyTheme(theme) {
    if (theme === 'light') {
        document.body.classList.add('light-theme');
    } else {
        document.body.classList.remove('light-theme');
    }
    localStorage.setItem('theme', theme);

    // 更新主题按钮图标
    const themeBtnIcon = themeBtn?.querySelector('path');
    if (themeBtnIcon) {
        if (theme === 'light') {
            // 太阳图标
            themeBtnIcon.setAttribute('d', 'M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z');
        } else {
            // 月亮图标
            themeBtnIcon.setAttribute('d', 'M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z');
        }
    }
}

// Init theme
applyTheme(localStorage.getItem('theme') || 'dark');

// 绑定主题按钮事件
themeBtn.addEventListener('click', toggleTheme);
