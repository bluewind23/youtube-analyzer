// 커스텀 경고창을 위한 전역 함수
function showCustomAlert(message) {
    const overlay = document.getElementById('custom-alert-overlay');
    const box = document.getElementById('custom-alert-box');
    const messageP = document.getElementById('custom-alert-message');
    const closeBtn = document.getElementById('custom-alert-close-btn');

    if (!overlay || !messageP || !closeBtn || !box) {
        alert(message); // Fallback to default alert
        return;
    }

    messageP.textContent = message;
    overlay.classList.remove('hidden');
    
    setTimeout(() => {
        box.classList.remove('opacity-0', 'scale-95');
        box.classList.add('opacity-100', 'scale-100');
    }, 10);
    
    closeBtn.onclick = () => {
        box.classList.add('opacity-0', 'scale-95');
        setTimeout(() => {
            overlay.classList.add('hidden');
        }, 200);
    };
}

document.addEventListener('DOMContentLoaded', function () {
    // 피드백 모달 기능
    setupFeedbackModal();
    
    // 기능 1: 필터 드롭다운
    document.querySelectorAll('.filter-dropdown .dropdown-toggle').forEach(toggle => {
        toggle.addEventListener('click', (event) => {
            event.stopPropagation();
            const menu = toggle.nextElementSibling;
            
            document.querySelectorAll('.dropdown-menu').forEach(otherMenu => {
                if (otherMenu !== menu) { otherMenu.classList.add('hidden'); }
            });
            menu.classList.toggle('hidden');
        });
    });

    // 기능 2: 페이지 다른 곳을 클릭하면 메뉴 닫기
    document.addEventListener('click', (event) => {
        if (!event.target.closest('.filter-dropdown')) {
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                menu.classList.add('hidden');
            });
        }
    });
});

// 피드백 모달 설정 함수
function setupFeedbackModal() {
    const feedbackBtn = document.getElementById('feedback-btn');
    const feedbackModal = document.getElementById('feedback-modal');
    const feedbackCloseBtn = document.getElementById('feedback-close-btn');
    const feedbackCancelBtn = document.getElementById('feedback-cancel-btn');
    const feedbackForm = document.getElementById('feedback-form');

    if (!feedbackBtn || !feedbackModal || !feedbackForm) return;

    // 피드백 버튼 클릭 시 모달 열기
    feedbackBtn.addEventListener('click', () => {
        feedbackModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // 스크롤 방지
    });

    // 모달 닫기 함수
    function closeFeedbackModal() {
        feedbackModal.classList.add('hidden');
        document.body.style.overflow = ''; // 스크롤 복원
        feedbackForm.reset(); // 폼 초기화
    }

    // 닫기 버튼들
    if (feedbackCloseBtn) {
        feedbackCloseBtn.addEventListener('click', closeFeedbackModal);
    }
    if (feedbackCancelBtn) {
        feedbackCancelBtn.addEventListener('click', closeFeedbackModal);
    }

    // 모달 배경 클릭 시 닫기
    feedbackModal.addEventListener('click', (e) => {
        if (e.target === feedbackModal) {
            closeFeedbackModal();
        }
    });

    // ESC 키로 닫기
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !feedbackModal.classList.contains('hidden')) {
            closeFeedbackModal();
        }
    });

    // 폼 제출 처리
    feedbackForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(feedbackForm);
        const feedbackData = {
            feedback_type: formData.get('feedback_type'),
            message: formData.get('message')
        };

        try {
            const response = await fetch('/submit-feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(feedbackData)
            });

            const result = await response.json();

            if (result.success) {
                showCustomAlert('피드백이 성공적으로 전송되었습니다. 감사합니다!');
                closeFeedbackModal();
            } else {
                showCustomAlert('피드백 전송 중 오류가 발생했습니다. 다시 시도해 주세요.');
            }
        } catch (error) {
            console.error('Feedback submission error:', error);
            showCustomAlert('네트워크 오류가 발생했습니다. 다시 시도해 주세요.');
        }
    });
}