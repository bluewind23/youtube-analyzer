document.addEventListener('DOMContentLoaded', function () {
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');

    // 검색 폼
    const searchForm = document.querySelector('form[action="/"]');
    if (searchForm) {
        searchForm.addEventListener('submit', function () {
            loadingText.textContent = '검색 중입니다...';
            loadingOverlay.classList.remove('hidden');
        });
    }

    // 로딩을 유발하는 모든 링크 (카테고리, 페이지네이션 등)
    const loadingLinks = document.querySelectorAll('a[href*="category="], a[href*="page_token="], a[href*="sort="]');
    loadingLinks.forEach(function (link) {
        link.addEventListener('click', function () {
            loadingText.textContent = '로딩 중입니다...';
            loadingOverlay.classList.remove('hidden');
        });
    });

    // 브라우저 뒤로가기/앞으로가기 시 로딩 화면 숨기기
    window.addEventListener('pageshow', function (event) {
        // bfcache (back-forward cache)에서 페이지가 로드될 때
        if (event.persisted) {
            loadingOverlay.classList.add('hidden');
        }
    });
});