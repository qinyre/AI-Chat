// ==================== UI 交互 ====================

// 帮助模态框
const helpBtnSidebar = document.getElementById('help-btn-sidebar');
const helpBtnTop = document.getElementById('help-btn-top');
const helpModal = document.getElementById('help-modal');
const closeModal = document.getElementById('close-modal');

function openModal() {
    helpModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModalFn() {
    helpModal.classList.remove('active');
    document.body.style.overflow = '';
}

// 绑定帮助按钮事件
helpBtnSidebar.addEventListener('click', openModal);
helpBtnTop.addEventListener('click', openModal);
closeModal.addEventListener('click', closeModalFn);

// Modal events
helpModal.addEventListener('click', (e) => {
    if (e.target === helpModal) closeModalFn();
});

// FAQ accordion
document.querySelectorAll('.faq-question').forEach(q => {
    q.addEventListener('click', () => {
        const item = q.parentElement;
        const isOpen = item.classList.contains('open');
        document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
        if (!isOpen) item.classList.add('open');
    });
});

// ESC 键关闭帮助模态框
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModalFn();
});
