// [수정] 스택형 알림 표시 및 제거 로직 개선
function showStackedNotification(message, type = 'success') {
    const container = document.getElementById('notification-container');
    if (!container) return;

    // 1. 알림 요소 생성
    const notification = document.createElement('div');
    notification.className = 'flex items-center gap-3 bg-white text-gray-600 text-sm font-medium px-4 py-3 rounded-lg shadow-2xl border border-gray-200 w-full transform transition-all duration-300 ease-in-out opacity-0 translate-x-full';
    
    const iconHtml = type === 'success'
        ? `<svg class="w-5 h-5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>`
        : `<svg class="w-5 h-5 text-blue-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>`;

    notification.innerHTML = `${iconHtml}<span>${message}</span>`;
    container.appendChild(notification);

    // 2. 애니메이션 효과로 나타나기
    requestAnimationFrame(() => {
        notification.classList.remove('opacity-0', 'translate-x-full');
    });

    // 3. 3초 후 자동으로 제거 시작
    setTimeout(() => {
        notification.classList.add('opacity-0', 'translate-x-full');
        // 애니메이션 시간(300ms)이 지난 후 DOM에서 완전히 제거하여 버그 방지
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}


document.addEventListener('DOMContentLoaded', function() {
    
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;
    
    // 디버깅: 페이지 로드 시 로그인 상태 확인
    console.log('=== 페이지 로드 완료 ===');
    console.log('로그인 상태:', window.pageData?.isAuthenticated);
    console.log('현재 사용자:', window.pageData?.currentUser);
    console.log('페이지 데이터:', window.pageData);

    document.body.addEventListener('click', async function(e) {
        
        const saveChannelBtn = e.target.closest('.save-channel-btn');
        if (saveChannelBtn) {
            e.preventDefault();
            
            // 로그인 상태 확인
            if (!window.pageData?.isAuthenticated) {
                showCustomAlert('채널 저장은 로그인 후에 가능합니다.');
                return;
            }
            
            const channelId = saveChannelBtn.dataset.channelId;
            const channelTitle = saveChannelBtn.dataset.channelTitle;
            const isSaved = saveChannelBtn.classList.contains('is-saved');

            if (isSaved) {
                // 이미 저장된 채널인 경우 바로 삭제
                const endpoint = '/unsave-item';
                const body = { 
                    item_type: 'channel', 
                    item_value: channelId, 
                    item_display_name: channelTitle 
                };

                try {
                    const response = await fetch(endpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                        body: JSON.stringify(body)
                    });

                    if (response.status === 401) {
                        showCustomAlert('채널 저장은 로그인 후에 가능합니다.');
                        return;
                    }

                    const result = await response.json();

                    if (result.success) {
                        saveChannelBtn.classList.remove('is-saved');
                        saveChannelBtn.classList.remove('text-blue-600');
                        const icon = saveChannelBtn.querySelector('svg');
                        const isSmallIcon = icon.classList.contains('w-4');
                        const iconSizeClass = isSmallIcon ? 'w-4 h-4' : 'w-5 h-5';
                        icon.outerHTML = `<svg class="${iconSizeClass}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" /></svg>`;
                        showStackedNotification('채널 저장이 취소되었습니다.', 'info');
                    } else {
                        showCustomAlert(result.error || '요청에 실패했습니다.');
                    }
                } catch (error) {
                    console.error('Error toggling save state:', error);
                    showCustomAlert('요청 중 오류가 발생했습니다.');
                }
            } else {
                // 저장되지 않은 채널인 경우 카테고리 선택 모달 표시
                showChannelSaveModal({
                    channelId,
                    channelTitle
                });
            }
        }

        const saveQueryBtn = e.target.closest('#save-query-btn');
        if (saveQueryBtn) {
            e.preventDefault();
            const query = window.pageData?.query;
            if (!query) {
                showCustomAlert('저장할 검색어가 없습니다.');
                return;
            }

            const isSaved = saveQueryBtn.classList.contains('is-saved');
            const endpoint = isSaved ? '/unsave-item' : '/save-item';
            
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                    body: JSON.stringify({ item_type: 'query', item_value: query })
                });
                
                // 로그인이 필요한 상태 (401 Unauthorized) 처리
                if (response.status === 401) {
                    showCustomAlert('검색어 저장은 로그인 후에 가능합니다.');
                    return;
                }
                
                const result = await response.json();
                
                if (result.success) {
                    saveQueryBtn.classList.toggle('is-saved');
                    if (saveQueryBtn.classList.contains('is-saved')) {
                        saveQueryBtn.classList.add('text-blue-600');
                        saveQueryBtn.classList.remove('text-gray-500');
                        saveQueryBtn.innerHTML = `<svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor"><path d="M5 21V5q0-.825.588-1.413T7 3h10q.825 0 1.413.588T19 5v16l-7-3Z"/></svg>`;
                        showStackedNotification('검색어가 저장되었습니다.', 'success');
                    } else {
                        saveQueryBtn.classList.remove('text-blue-600');
                        saveQueryBtn.classList.add('text-gray-500');
                        saveQueryBtn.innerHTML = `<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.5 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" /></svg>`;
                        showStackedNotification('검색어 저장이 취소되었습니다.', 'info');
                    }
                } else {
                    showCustomAlert(result.error || '요청에 실패했습니다.');
                }
            } catch (error) {
                console.error('Error saving/unsaving query:', error);
                showCustomAlert('요청 중 오류가 발생했습니다.');
            }
        }

        // 영상 저장 버튼 처리
        const saveVideoBtn = e.target.closest('.save-video-btn');
        if (saveVideoBtn) {
            e.preventDefault();
            
            // 로그인 상태 확인
            if (!window.pageData?.isAuthenticated) {
                showCustomAlert('영상 저장은 로그인 후에 가능합니다.');
                return;
            }
            
            const videoId = saveVideoBtn.dataset.videoId;
            const videoTitle = saveVideoBtn.dataset.videoTitle;
            const channelId = saveVideoBtn.dataset.channelId;
            const channelTitle = saveVideoBtn.dataset.channelTitle;
            const thumbnailUrl = saveVideoBtn.dataset.thumbnailUrl;

            // 이미 저장된 영상인지 확인
            checkVideoSavedStatus(videoId).then(isSaved => {
                if (isSaved) {
                    // 이미 저장된 경우 삭제 확인 후 토글
                    if (confirm('이미 저장된 영상입니다. 저장을 취소하시겠습니까?')) {
                        toggleVideoSave(videoId, videoTitle, channelId, channelTitle, thumbnailUrl, saveVideoBtn);
                    }
                } else {
                    // 저장되지 않은 경우 카테고리 선택 모달 표시
                    showVideoSaveModal({
                        videoId,
                        videoTitle,
                        channelId,
                        channelTitle,
                        thumbnailUrl
                    });
                }
            });
        }

        const deleteBtn = e.target.closest('.delete-saved-item-btn');
        if (deleteBtn) {
            e.preventDefault();
            if (!confirm('정말로 이 항목을 삭제하시겠습니까?')) return;
            const itemId = deleteBtn.dataset.itemId;
            try {
                const response = await fetch('/delete-saved-item', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                    body: JSON.stringify({ item_id: itemId })
                });
                
                // 로그인이 필요한 상태 (401 Unauthorized) 처리
                if (response.status === 401) {
                    showCustomAlert('로그인 후에 이용할 수 있습니다.');
                    return;
                }
                
                const result = await response.json();
                if (result.success) {
                    deleteBtn.closest('li').remove();
                } else {
                    showCustomAlert(result.error || '삭제에 실패했습니다.');
                }
            } catch (error) {
                console.error('Error deleting item:', error);
                showCustomAlert('요청 중 오류가 발생했습니다.');
            }
        }
    });
});

// 영상 저장 모달 표시 함수
function showVideoSaveModal(videoData) {
    const modal = document.getElementById('video-save-modal');
    if (!modal) {
        createVideoSaveModal(videoData);
        return;
    }
    
    // 모달 데이터 업데이트
    document.getElementById('video-save-title').textContent = videoData.videoTitle;
    document.getElementById('video-save-channel').textContent = videoData.channelTitle;
    
    // 현재 비디오 데이터 저장
    modal.videoData = videoData;
    
    // 카테고리 목록 로드
    loadVideoCategories();
    
    modal.classList.remove('hidden');
}

// 영상 저장 모달 생성 함수
function createVideoSaveModal(videoData) {
    const modalHTML = `
        <div id="video-save-modal" class="hidden fixed inset-0 z-[10000] flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
            <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md mx-4 transform transition-all">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">영상 저장</h3>
                    <button id="video-save-close-btn" class="text-gray-400 hover:text-gray-600 transition-colors">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <div class="mb-4">
                    <h4 id="video-save-title" class="font-medium text-gray-900 truncate"></h4>
                    <p id="video-save-channel" class="text-sm text-gray-600"></p>
                </div>
                
                <form id="video-save-form">
                    <div class="mb-4">
                        <label for="video-category-select" class="block text-sm font-medium text-gray-700 mb-2">카테고리 선택</label>
                        <select id="video-category-select" name="category_id" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="">기본 카테고리</option>
                        </select>
                    </div>
                    
                    <div class="mb-4">
                        <div class="flex justify-between items-center mb-2">
                            <label for="video-notes" class="block text-sm font-medium text-gray-700">메모 (선택사항)</label>
                            <button type="button" id="new-category-btn" class="text-xs text-blue-600 hover:text-blue-800">새 카테고리</button>
                        </div>
                        <textarea id="video-notes" name="notes" rows="3" 
                                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  placeholder="이 영상에 대한 메모를 남겨주세요..."></textarea>
                    </div>
                    
                    <div class="flex justify-end gap-3">
                        <button type="button" id="video-save-cancel-btn" 
                                class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors">
                            취소
                        </button>
                        <button type="submit" 
                                class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors">
                            저장
                        </button>
                    </div>
                </form>
            </div>
        </div>
        
        <!-- 새 카테고리 생성 모달 -->
        <div id="new-category-modal" class="hidden fixed inset-0 z-[10001] flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
            <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-sm mx-4">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">새 카테고리 생성</h3>
                    <button id="new-category-close-btn" class="text-gray-400 hover:text-gray-600 transition-colors">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <form id="new-category-form">
                    <div class="mb-4">
                        <label for="category-name" class="block text-sm font-medium text-gray-700 mb-2">카테고리 이름</label>
                        <input type="text" id="category-name" name="name" required
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                               placeholder="예: 개발 강의, 요리 레시피...">
                    </div>
                    
                    <div class="mb-4">
                        <label for="category-description" class="block text-sm font-medium text-gray-700 mb-2">설명 (선택사항)</label>
                        <textarea id="category-description" name="description" rows="2"
                                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  placeholder="카테고리에 대한 간단한 설명..."></textarea>
                    </div>
                    
                    <div class="flex justify-end gap-3">
                        <button type="button" id="new-category-cancel-btn" 
                                class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors">
                            취소
                        </button>
                        <button type="submit" 
                                class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors">
                            생성
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    const modal = document.getElementById('video-save-modal');
    modal.videoData = videoData;
    
    // 모달 데이터 설정
    document.getElementById('video-save-title').textContent = videoData.videoTitle;
    document.getElementById('video-save-channel').textContent = videoData.channelTitle;
    
    // 이벤트 리스너 설정
    setupVideoSaveModalEvents();
    
    // 카테고리 목록 로드
    loadVideoCategories();
    
    modal.classList.remove('hidden');
}

// 비디오 저장 모달 이벤트 설정
function setupVideoSaveModalEvents() {
    const modal = document.getElementById('video-save-modal');
    const newCategoryModal = document.getElementById('new-category-modal');
    
    // 모달 닫기
    document.getElementById('video-save-close-btn').addEventListener('click', () => {
        modal.classList.add('hidden');
    });
    
    document.getElementById('video-save-cancel-btn').addEventListener('click', () => {
        modal.classList.add('hidden');
    });
    
    // 새 카테고리 버튼
    document.getElementById('new-category-btn').addEventListener('click', () => {
        newCategoryModal.classList.remove('hidden');
    });
    
    // 새 카테고리 모달 닫기
    document.getElementById('new-category-close-btn').addEventListener('click', () => {
        newCategoryModal.classList.add('hidden');
    });
    
    document.getElementById('new-category-cancel-btn').addEventListener('click', () => {
        newCategoryModal.classList.add('hidden');
    });
    
    // 영상 저장 폼 제출
    document.getElementById('video-save-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveVideo();
    });
    
    // 새 카테고리 폼 제출
    document.getElementById('new-category-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await createVideoCategory();
    });
    
    // ESC 키로 모달 닫기
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (!newCategoryModal.classList.contains('hidden')) {
                newCategoryModal.classList.add('hidden');
            } else if (!modal.classList.contains('hidden')) {
                modal.classList.add('hidden');
            }
        }
    });
    
    // 실시간 카테고리 이름 중복 확인
    const categoryNameInput = document.getElementById('category-name');
    if (categoryNameInput) {
        categoryNameInput.addEventListener('input', function() {
            const name = this.value.trim();
            const submitButton = document.querySelector('#new-category-form button[type="submit"]');
            
            if (name) {
                // 기존 카테고리와 중복 확인
                const existingCategories = Array.from(document.querySelectorAll('#video-category-select option'))
                    .map(option => option.textContent.split(' (')[0])
                    .filter(categoryName => categoryName !== '기본 카테고리');
                
                if (existingCategories.includes(name)) {
                    this.style.borderColor = '#ef4444'; // 빨간색
                    submitButton.disabled = true;
                    submitButton.classList.add('opacity-50', 'cursor-not-allowed');
                    
                    // 중복 메시지 표시
                    let errorMsg = document.getElementById('category-name-error');
                    if (!errorMsg) {
                        errorMsg = document.createElement('p');
                        errorMsg.id = 'category-name-error';
                        errorMsg.className = 'text-xs text-red-500 mt-1';
                        this.parentNode.appendChild(errorMsg);
                    }
                    errorMsg.textContent = '같은 이름의 카테고리가 이미 존재합니다.';
                } else {
                    this.style.borderColor = '#10b981'; // 초록색
                    submitButton.disabled = false;
                    submitButton.classList.remove('opacity-50', 'cursor-not-allowed');
                    
                    // 에러 메시지 제거
                    const errorMsg = document.getElementById('category-name-error');
                    if (errorMsg) {
                        errorMsg.remove();
                    }
                }
            } else {
                this.style.borderColor = '#d1d5db'; // 기본색
                submitButton.disabled = false;
                submitButton.classList.remove('opacity-50', 'cursor-not-allowed');
                
                // 에러 메시지 제거
                const errorMsg = document.getElementById('category-name-error');
                if (errorMsg) {
                    errorMsg.remove();
                }
            }
        });
    }
}

// 카테고리 목록 로드
async function loadVideoCategories() {
    try {
        // 로그인 상태 확인
        if (!window.pageData?.isAuthenticated) {
            console.log('로그인되지 않은 상태 - 카테고리 로드 건너뛰기');
            return;
        }
        
        console.log('현재 사용자:', window.pageData?.currentUser);
        
        const response = await fetch('/api/video-categories');
        console.log('카테고리 로드 응답 상태:', response.status);
        
        if (response.status === 401) {
            showCustomAlert('영상 저장은 로그인 후에 가능합니다.');
            return;
        }
        
        if (response.status === 500) {
            console.error('서버 오류 발생 (500)');
            const text = await response.text();
            console.error('서버 응답:', text);
            showCustomAlert('서버 오류가 발생했습니다. 다시 시도해주세요.');
            return;
        }
        
        const result = await response.json();
        if (result.success) {
            const select = document.getElementById('video-category-select');
            select.innerHTML = '<option value="">기본 카테고리</option>';
            
            result.categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = `${category.name} (${category.video_count})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('카테고리 로드 실패:', error);
    }
}

// 새 카테고리 생성
async function createVideoCategory() {
    const form = document.getElementById('new-category-form');
    const formData = new FormData(form);
    
    const name = formData.get('name')?.trim();
    const description = formData.get('description')?.trim();
    
    // 클라이언트 측 유효성 검사
    if (!name) {
        showCustomAlert('카테고리 이름을 입력해주세요.');
        return;
    }
    
    // 기존 카테고리와 중복 확인
    const existingCategories = Array.from(document.querySelectorAll('#video-category-select option'))
        .map(option => option.textContent.split(' (')[0])
        .filter(categoryName => categoryName !== '기본 카테고리');
    
    if (existingCategories.includes(name)) {
        showCustomAlert('같은 이름의 카테고리가 이미 존재합니다.');
        return;
    }
    
    try {
        const response = await fetch('/api/video-categories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                description: description
            })
        });
        
        if (response.status === 401) {
            showCustomAlert('카테고리 생성은 로그인 후에 가능합니다.');
            return;
        }
        
        if (response.status === 400) {
            const result = await response.json();
            showCustomAlert(result.error || '카테고리 생성에 실패했습니다.');
            return;
        }
        
        if (response.status === 500) {
            console.error('서버 오류 발생 (500)');
            const text = await response.text();
            console.error('서버 응답:', text);
            showCustomAlert('서버 오류가 발생했습니다. 다시 시도해주세요.');
            return;
        }
        
        const result = await response.json();
        if (result.success) {
            showStackedNotification('카테고리가 생성되었습니다.', 'success');
            document.getElementById('new-category-modal').classList.add('hidden');
            form.reset();
            
            // 카테고리 목록 다시 로드
            await loadVideoCategories();
            
            // 새로 생성된 카테고리 선택
            document.getElementById('video-category-select').value = result.category.id;
        } else {
            showCustomAlert(result.error || '카테고리 생성에 실패했습니다.');
        }
    } catch (error) {
        console.error('카테고리 생성 실패:', error);
        showCustomAlert('카테고리 생성 중 오류가 발생했습니다.');
    }
}

// 영상 저장
async function saveVideo() {
    const modal = document.getElementById('video-save-modal');
    const videoData = modal.videoData;
    
    // 로그인 상태 확인
    if (!window.pageData?.isAuthenticated) {
        showCustomAlert('영상 저장은 로그인 후에 가능합니다.');
        return;
    }
    
    const categoryId = document.getElementById('video-category-select').value;
    const notes = document.getElementById('video-notes').value;
    
    console.log('영상 저장 요청 데이터:', {
        video_id: videoData.videoId,
        video_title: videoData.videoTitle,
        channel_id: videoData.channelId,
        channel_title: videoData.channelTitle,
        thumbnail_url: videoData.thumbnailUrl,
        category_id: categoryId || null,
        notes: notes || null
    });
    
    try {
        const response = await fetch('/api/save-video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                video_id: videoData.videoId,
                video_title: videoData.videoTitle,
                channel_id: videoData.channelId,
                channel_title: videoData.channelTitle,
                thumbnail_url: videoData.thumbnailUrl,
                category_id: categoryId || null,
                notes: notes || null
            })
        });
        
        console.log('영상 저장 응답 상태:', response.status);
        console.log('응답 헤더:', response.headers);
        
        if (response.status === 401) {
            showCustomAlert('영상 저장은 로그인 후에 가능합니다.');
            return;
        }
        
        if (response.status === 500) {
            console.error('서버 오류 발생 (500)');
            const text = await response.text();
            console.error('서버 응답:', text);
            showCustomAlert('서버 오류가 발생했습니다. 다시 시도해주세요.');
            return;
        }
        
        const result = await response.json();
        console.log('영상 저장 응답 데이터:', result);
        
        if (result.success) {
            showStackedNotification(result.message || '영상이 저장되었습니다.', 'success');
            modal.classList.add('hidden');
            
            // 저장 버튼 UI 업데이트
            const videoBtn = document.querySelector(`[data-video-id="${videoData.videoId}"]`);
            if (videoBtn) {
                updateVideoSaveButtonUI(videoBtn, result.action || 'saved');
            }
        } else {
            showCustomAlert(result.error || '영상 저장에 실패했습니다.');
        }
    } catch (error) {
        console.error('영상 저장 실패:', error);
        showCustomAlert('영상 저장 중 오류가 발생했습니다.');
    }
}

// 영상 저장 상태 확인
async function checkVideoSavedStatus(videoId) {
    try {
        // 로그인 상태 확인
        if (!window.pageData?.isAuthenticated) {
            console.log('로그인되지 않은 상태 - 저장 상태 확인 건너뛰기');
            return false;
        }
        
        const response = await fetch(`/api/check-saved-video/${videoId}`);
        console.log('저장 상태 확인 응답 상태:', response.status);
        
        if (response.status === 401) return false;
        
        if (response.status === 500) {
            console.error('서버 오류 발생 (500)');
            const text = await response.text();
            console.error('서버 응답:', text);
            return false;
        }
        
        const result = await response.json();
        return result.success && result.is_saved;
    } catch (error) {
        console.error('저장 상태 확인 실패:', error);
        return false;
    }
}

// 영상 저장/해제 토글
async function toggleVideoSave(videoId, videoTitle, channelId, channelTitle, thumbnailUrl, buttonElement) {
    
    try {
        const response = await fetch('/api/save-video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                video_id: videoId,
                video_title: videoTitle,
                channel_id: channelId,
                channel_title: channelTitle,
                thumbnail_url: thumbnailUrl
            })
        });
        
        if (response.status === 401) {
            showCustomAlert('영상 저장은 로그인 후에 가능합니다.');
            return;
        }
        
        const result = await response.json();
        if (result.success) {
            updateVideoSaveButtonUI(buttonElement, result.action);
            showStackedNotification(result.message, 'success');
        } else {
            showCustomAlert(result.error || '요청에 실패했습니다.');
        }
    } catch (error) {
        console.error('영상 저장 토글 실패:', error);
        showCustomAlert('요청 중 오류가 발생했습니다.');
    }
}

// 영상 저장 버튼 UI 업데이트
function updateVideoSaveButtonUI(buttonElement, action) {
    const icon = buttonElement.querySelector('svg');
    
    if (action === 'saved') {
        // 저장됨 상태로 변경
        buttonElement.classList.add('saved');
        buttonElement.classList.add('text-blue-600');
        icon.outerHTML = `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M5 21V5q0-.825.588-1.413T7 3h10q.825 0 1.413.588T19 5v16l-7-3Z"/></svg>`;
        buttonElement.title = '영상 저장 취소';
    } else if (action === 'removed') {
        // 저장 안됨 상태로 변경
        buttonElement.classList.remove('saved');
        buttonElement.classList.remove('text-blue-600');
        icon.outerHTML = `<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.5 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" /></svg>`;
        buttonElement.title = '영상 저장';
    }
}

// 채널 저장 모달 표시 함수
function showChannelSaveModal(channelData) {
    const modal = document.getElementById('channel-save-modal');
    if (!modal) {
        createChannelSaveModal(channelData);
        return;
    }
    
    // 모달 데이터 업데이트
    document.getElementById('channel-save-title').textContent = channelData.channelTitle;
    
    // 현재 채널 데이터 저장
    modal.channelData = channelData;
    
    // 카테고리 목록 로드
    loadChannelCategories();
    
    modal.classList.remove('hidden');
}

// 채널 저장 모달 생성 함수
function createChannelSaveModal(channelData) {
    const modalHTML = `
        <div id="channel-save-modal" class="hidden fixed inset-0 z-[10000] flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
            <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md mx-4 transform transition-all">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">채널 저장</h3>
                    <button id="channel-save-close-btn" class="text-gray-400 hover:text-gray-600 transition-colors">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <div class="mb-4">
                    <h4 id="channel-save-title" class="font-medium text-gray-900 truncate"></h4>
                </div>
                
                <form id="channel-save-form">
                    <div class="mb-4">
                        <label for="channel-category-select" class="block text-sm font-medium text-gray-700 mb-2">카테고리 선택</label>
                        <select id="channel-category-select" name="category_id" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="">기본 카테고리</option>
                        </select>
                    </div>
                    
                    <div class="mb-4">
                        <div class="flex justify-between items-center mb-2">
                            <label class="block text-sm font-medium text-gray-700">채널 저장</label>
                            <button type="button" id="new-channel-category-btn" class="text-xs text-blue-600 hover:text-blue-800">새 카테고리</button>
                        </div>
                    </div>
                    
                    <div class="flex justify-end gap-3">
                        <button type="button" id="channel-save-cancel-btn" 
                                class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors">
                            취소
                        </button>
                        <button type="submit" 
                                class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors">
                            저장
                        </button>
                    </div>
                </form>
            </div>
        </div>
        
        <!-- 새 채널 카테고리 생성 모달 -->
        <div id="new-channel-category-modal" class="hidden fixed inset-0 z-[10001] flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
            <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-sm mx-4">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">새 채널 카테고리 생성</h3>
                    <button id="new-channel-category-close-btn" class="text-gray-400 hover:text-gray-600 transition-colors">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <form id="new-channel-category-form">
                    <div class="mb-4">
                        <label for="channel-category-name" class="block text-sm font-medium text-gray-700 mb-2">카테고리 이름</label>
                        <input type="text" id="channel-category-name" name="name" required
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                               placeholder="예: 요리 채널, 게임 채널...">
                    </div>
                    
                    <div class="mb-4">
                        <label for="channel-category-description" class="block text-sm font-medium text-gray-700 mb-2">설명 (선택사항)</label>
                        <textarea id="channel-category-description" name="description" rows="2"
                                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  placeholder="카테고리에 대한 간단한 설명..."></textarea>
                    </div>
                    
                    <div class="flex justify-end gap-3">
                        <button type="button" id="new-channel-category-cancel-btn" 
                                class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors">
                            취소
                        </button>
                        <button type="submit" 
                                class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors">
                            생성
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    const modal = document.getElementById('channel-save-modal');
    modal.channelData = channelData;
    
    // 모달 데이터 설정
    document.getElementById('channel-save-title').textContent = channelData.channelTitle;
    
    // 이벤트 리스너 설정
    setupChannelSaveModalEvents();
    
    // 카테고리 목록 로드
    loadChannelCategories();
    
    modal.classList.remove('hidden');
}

// 채널 저장 모달 이벤트 설정
function setupChannelSaveModalEvents() {
    const modal = document.getElementById('channel-save-modal');
    const newCategoryModal = document.getElementById('new-channel-category-modal');
    
    // 모달 닫기
    document.getElementById('channel-save-close-btn').addEventListener('click', () => {
        modal.classList.add('hidden');
    });
    
    document.getElementById('channel-save-cancel-btn').addEventListener('click', () => {
        modal.classList.add('hidden');
    });
    
    // 새 카테고리 버튼
    document.getElementById('new-channel-category-btn').addEventListener('click', () => {
        newCategoryModal.classList.remove('hidden');
    });
    
    // 새 카테고리 모달 닫기
    document.getElementById('new-channel-category-close-btn').addEventListener('click', () => {
        newCategoryModal.classList.add('hidden');
    });
    
    document.getElementById('new-channel-category-cancel-btn').addEventListener('click', () => {
        newCategoryModal.classList.add('hidden');
    });
    
    // 채널 저장 폼 제출
    document.getElementById('channel-save-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveChannel();
    });
    
    // 새 카테고리 폼 제출
    document.getElementById('new-channel-category-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await createChannelCategory();
    });
    
    // 실시간 카테고리 이름 중복 확인
    const categoryNameInput = document.getElementById('channel-category-name');
    if (categoryNameInput) {
        categoryNameInput.addEventListener('input', function() {
            const name = this.value.trim();
            const submitButton = document.querySelector('#new-channel-category-form button[type="submit"]');
            
            if (name) {
                // 기존 카테고리와 중복 확인
                const existingCategories = Array.from(document.querySelectorAll('#channel-category-select option'))
                    .map(option => option.textContent.split(' (')[0])
                    .filter(categoryName => categoryName !== '기본 카테고리');
                
                if (existingCategories.includes(name)) {
                    this.style.borderColor = '#ef4444'; // 빨간색
                    submitButton.disabled = true;
                    submitButton.classList.add('opacity-50', 'cursor-not-allowed');
                    
                    // 중복 메시지 표시
                    let errorMsg = document.getElementById('channel-category-name-error');
                    if (!errorMsg) {
                        errorMsg = document.createElement('p');
                        errorMsg.id = 'channel-category-name-error';
                        errorMsg.className = 'text-xs text-red-500 mt-1';
                        this.parentNode.appendChild(errorMsg);
                    }
                    errorMsg.textContent = '같은 이름의 카테고리가 이미 존재합니다.';
                } else {
                    this.style.borderColor = '#10b981'; // 초록색
                    submitButton.disabled = false;
                    submitButton.classList.remove('opacity-50', 'cursor-not-allowed');
                    
                    // 에러 메시지 제거
                    const errorMsg = document.getElementById('channel-category-name-error');
                    if (errorMsg) {
                        errorMsg.remove();
                    }
                }
            } else {
                this.style.borderColor = '#d1d5db'; // 기본색
                submitButton.disabled = false;
                submitButton.classList.remove('opacity-50', 'cursor-not-allowed');
                
                // 에러 메시지 제거
                const errorMsg = document.getElementById('channel-category-name-error');
                if (errorMsg) {
                    errorMsg.remove();
                }
            }
        });
    }
}

// 채널 카테고리 목록 로드
async function loadChannelCategories() {
    try {
        if (!window.pageData?.isAuthenticated) {
            console.log('로그인되지 않은 상태 - 채널 카테고리 로드 건너뛰기');
            return;
        }
        
        const response = await fetch('/api/channel-categories');
        console.log('채널 카테고리 로드 응답 상태:', response.status);
        
        if (response.status === 401) {
            showCustomAlert('채널 저장은 로그인 후에 가능합니다.');
            return;
        }
        
        if (response.status === 500) {
            console.error('서버 오류 발생 (500)');
            const text = await response.text();
            console.error('서버 응답:', text);
            showCustomAlert('서버 오류가 발생했습니다. 다시 시도해주세요.');
            return;
        }
        
        const result = await response.json();
        if (result.success) {
            const select = document.getElementById('channel-category-select');
            select.innerHTML = '<option value="">기본 카테고리</option>';
            
            result.categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = `${category.name} (${category.channel_count})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('채널 카테고리 로드 실패:', error);
    }
}

// 새 채널 카테고리 생성
async function createChannelCategory() {
    const form = document.getElementById('new-channel-category-form');
    const formData = new FormData(form);
    
    const name = formData.get('name')?.trim();
    const description = formData.get('description')?.trim();
    
    if (!name) {
        showCustomAlert('카테고리 이름을 입력해주세요.');
        return;
    }
    
    // 기존 카테고리와 중복 확인
    const existingCategories = Array.from(document.querySelectorAll('#channel-category-select option'))
        .map(option => option.textContent.split(' (')[0])
        .filter(categoryName => categoryName !== '기본 카테고리');
    
    if (existingCategories.includes(name)) {
        showCustomAlert('같은 이름의 카테고리가 이미 존재합니다.');
        return;
    }
    
    try {
        const response = await fetch('/api/channel-categories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                description: description
            })
        });
        
        if (response.status === 401) {
            showCustomAlert('카테고리 생성은 로그인 후에 가능합니다.');
            return;
        }
        
        if (response.status === 400) {
            const result = await response.json();
            showCustomAlert(result.error || '카테고리 생성에 실패했습니다.');
            return;
        }
        
        if (response.status === 500) {
            console.error('서버 오류 발생 (500)');
            const text = await response.text();
            console.error('서버 응답:', text);
            showCustomAlert('서버 오류가 발생했습니다. 다시 시도해주세요.');
            return;
        }
        
        const result = await response.json();
        if (result.success) {
            showStackedNotification('카테고리가 생성되었습니다.', 'success');
            document.getElementById('new-channel-category-modal').classList.add('hidden');
            form.reset();
            
            // 카테고리 목록 다시 로드
            await loadChannelCategories();
            
            // 새로 생성된 카테고리 선택
            document.getElementById('channel-category-select').value = result.category.id;
        } else {
            showCustomAlert(result.error || '카테고리 생성에 실패했습니다.');
        }
    } catch (error) {
        console.error('채널 카테고리 생성 실패:', error);
        showCustomAlert('카테고리 생성 중 오류가 발생했습니다.');
    }
}

// 채널 저장
async function saveChannel() {
    const modal = document.getElementById('channel-save-modal');
    const channelData = modal.channelData;
    
    if (!window.pageData?.isAuthenticated) {
        showCustomAlert('채널 저장은 로그인 후에 가능합니다.');
        return;
    }
    
    const categoryId = document.getElementById('channel-category-select').value;
    
    try {
        const response = await fetch('/save-item', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                item_type: 'channel',
                item_value: channelData.channelId,
                item_display_name: channelData.channelTitle,
                category_id: categoryId || null
            })
        });
        
        if (response.status === 401) {
            showCustomAlert('채널 저장은 로그인 후에 가능합니다.');
            return;
        }
        
        if (response.status === 500) {
            console.error('서버 오류 발생 (500)');
            const text = await response.text();
            console.error('서버 응답:', text);
            showCustomAlert('서버 오류가 발생했습니다. 다시 시도해주세요.');
            return;
        }
        
        const result = await response.json();
        if (result.success) {
            showStackedNotification('채널이 저장되었습니다.', 'success');
            modal.classList.add('hidden');
            
            // 저장 버튼 UI 업데이트
            const channelBtn = document.querySelector(`[data-channel-id="${channelData.channelId}"]`);
            if (channelBtn) {
                channelBtn.classList.add('is-saved');
                channelBtn.classList.add('text-blue-600');
                const icon = channelBtn.querySelector('svg');
                const isSmallIcon = icon.classList.contains('w-4');
                const iconSizeClass = isSmallIcon ? 'w-4 h-4' : 'w-5 h-5';
                icon.outerHTML = `<svg class="${iconSizeClass}" viewBox="0 0 24 24" fill="currentColor"><path d="M5 21V5q0-.825.588-1.413T7 3h10q.825 0 1.413.588T19 5v16l-7-3Z"/></svg>`;
            }
        } else {
            showCustomAlert(result.error || '채널 저장에 실패했습니다.');
        }
    } catch (error) {
        console.error('채널 저장 실패:', error);
        showCustomAlert('채널 저장 중 오류가 발생했습니다.');
    }
}