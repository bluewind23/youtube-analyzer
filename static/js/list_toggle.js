document.addEventListener('DOMContentLoaded', function () {
    const gridViewBtn = document.getElementById('view-grid-btn');
    const listViewBtn = document.getElementById('view-list-btn');

    if (!gridViewBtn || !listViewBtn) {
        return;
    }

    const handleViewChange = (event, viewMode) => {
        event.preventDefault();

        const currentUrl = new URL(window.location.href);

        // [수정] 'view' 파라미터 값만 새로운 모드로 설정합니다.
        currentUrl.searchParams.set('view', viewMode);

        // [삭제] 페이지를 1로 초기화하는 코드를 제거하여, 현재 페이지 상태를 유지합니다.
        // currentUrl.searchParams.set('page', '1'); 

        window.location.href = currentUrl.href;
    };

    gridViewBtn.addEventListener('click', (event) => handleViewChange(event, 'grid'));
    listViewBtn.addEventListener('click', (event) => handleViewChange(event, 'list'));
});