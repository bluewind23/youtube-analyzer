// ===================================================================================
// [수정] 공통 광고 ID를 파일 상단으로 이동하여 중복 선언 오류 해결
// ===================================================================================
const AD_CLIENT_ID = "ca-pub-5809883478660758";
const AD_GRID_SLOT_ID = "3877365282"; // 그리드/수평 광고용 슬롯 ID
const AD_LIST_SLOT_ID = "3684991260"; // 리스트 뷰 전용 슬롯 ID

// ===================================================================================
// 헬퍼 함수 (Helper Functions)
// ===================================================================================

function escapeAttr(str) {
    if (typeof str !== 'string') return '';
    return str.replace(/"/g, '"').replace(/'/g, '\'');
}
function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    num = Number(num);
    if (isNaN(num)) return '-';
    if (num >= 100000000) return (num / 100000000).toFixed(1).replace('.0', '') + '억';
    if (num >= 10000) return (num / 10000).toFixed(1).replace('.0', '') + '만';
    return num.toLocaleString();
}

// ===================================================================================
// 툴팁 관련 함수 (Tooltip Functions)
// ===================================================================================

let channelDataCache = new Map();
let activeTooltip = null;

function hideAllTooltips() {
    if (activeTooltip) {
        activeTooltip.classList.add('hidden');
        activeTooltip.style.display = 'none';
        activeTooltip.style.visibility = 'hidden';
        activeTooltip.style.opacity = '0';
        activeTooltip = null;
    }
}

function createChannelTooltipHTML() {
    const html = `<div class="channel-tooltip hidden absolute z-[9999] bg-white border border-gray-200 rounded-md shadow-lg p-2 min-w-48 max-w-64" style="left: 100%; top: 0; transform: translateY(-100%); margin-left: 8px; pointer-events: auto;"><div class="flex items-center space-x-2 mb-2"><img class="w-8 h-8 rounded-full channel-thumbnail" src="" alt=""><div><h4 class="font-medium text-gray-900 text-xs channel-title">로딩 중...</h4></div></div><div class="space-y-1 text-xs"><div class="flex justify-between"><span class="text-gray-600">구독자:</span><span class="font-medium channel-subscribers">-</span></div><div class="flex justify-between"><span class="text-gray-600">총 영상:</span><span class="font-medium channel-videos">-</span></div><div class="flex justify-between"><span class="text-gray-600">평균 조회수:</span><span class="font-medium channel-avg-views">-</span></div></div><div class="mt-2 pt-2 border-t border-gray-100"><p class="text-xs text-gray-500">💡 채널 분석 기능은 준비 중입니다</p></div></div>`;
    return html;
}

function updateTooltipContent(tooltip, data) {
    tooltip.querySelector('.channel-title').textContent = data.title || '알 수 없는 채널';
    tooltip.querySelector('.channel-subscribers').textContent = formatNumber(data.subscriberCount);
    tooltip.querySelector('.channel-videos').textContent = formatNumber(data.videoCount);
    tooltip.querySelector('.channel-avg-views').textContent = formatNumber(data.avgViewsPerVideo);
    const thumbnail = tooltip.querySelector('.channel-thumbnail');
    if (data.thumbnailUrl) {
        thumbnail.src = data.thumbnailUrl;
        thumbnail.style.display = 'block';
    } else {
        thumbnail.style.display = 'none';
    }
}

function showTooltip(trigger, channelId) {
    // 더 강력한 툴팁 찾기 로직
    let tooltip = null;

    // 1. 트리거의 부모 .relative 컨테이너에서 찾기
    const relativeParent = trigger.closest('.relative');
    if (relativeParent) {
        tooltip = relativeParent.querySelector('.channel-tooltip');
    }

    // 2. 트리거의 직접 부모에서 찾기
    if (!tooltip && trigger.parentElement) {
        tooltip = trigger.parentElement.querySelector('.channel-tooltip');
    }

    // 3. 트리거 자신 안에서 찾기
    if (!tooltip) {
        tooltip = trigger.querySelector('.channel-tooltip');
    }

    // 4. 트리거의 다음 형제 요소에서 찾기
    if (!tooltip && trigger.nextElementSibling) {
        tooltip = trigger.nextElementSibling.classList.contains('channel-tooltip') ?
            trigger.nextElementSibling :
            trigger.nextElementSibling.querySelector('.channel-tooltip');
    }

    if (!tooltip) {
        console.error('No tooltip found for trigger:', trigger);
        return;
    }

    if (activeTooltip && activeTooltip !== tooltip) {
        hideAllTooltips();
    }

    // 모든 숨김 상태 제거 (!important로 강제)
    tooltip.classList.remove('hidden');
    tooltip.style.setProperty('display', 'block', 'important');
    tooltip.style.setProperty('visibility', 'visible', 'important');
    tooltip.style.setProperty('opacity', '1', 'important');
    tooltip.style.setProperty('z-index', '9999', 'important');
    tooltip.style.setProperty('position', 'absolute', 'important');

    // 뷰별 다른 포지셔닝 설정
    const isInGrid = trigger.closest('.grid');
    const isInList = trigger.closest('table');

    tooltip.style.setProperty('pointer-events', 'auto', 'important');

    if (isInGrid) {
        // 그리드뷰: 채널명 위쪽, 좌측 정렬
        tooltip.style.setProperty('left', '0', 'important');
        tooltip.style.setProperty('bottom', '100%', 'important');
        tooltip.style.setProperty('top', 'auto', 'important');
        tooltip.style.setProperty('transform', 'none', 'important');
        tooltip.style.setProperty('margin-bottom', '4px', 'important');
        tooltip.style.setProperty('margin-left', '0', 'important');

        // 상단 경계 체크 (뷰포트 상단에서 잘리지 않게)
        setTimeout(() => {
            const triggerRect = trigger.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();

            if (triggerRect.top - tooltipRect.height - 4 < 0) {
                // 상단에 공간이 부족하면 아래쪽으로 이동
                tooltip.style.setProperty('bottom', 'auto', 'important');
                tooltip.style.setProperty('top', '100%', 'important');
                tooltip.style.setProperty('margin-bottom', '0', 'important');
                tooltip.style.setProperty('margin-top', '4px', 'important');
            }
        }, 0);

    } else if (isInList) {
        // 리스트뷰: 채널명 아래쪽, 좌측 정렬
        tooltip.style.setProperty('left', '0', 'important');
        tooltip.style.setProperty('top', '100%', 'important');
        tooltip.style.setProperty('bottom', 'auto', 'important');
        tooltip.style.setProperty('transform', 'none', 'important');
        tooltip.style.setProperty('margin-top', '4px', 'important');
        tooltip.style.setProperty('margin-left', '0', 'important');

        // 하단 경계 체크 (뷰포트 하단에서 잘리지 않게)
        setTimeout(() => {
            const triggerRect = trigger.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();
            const viewportHeight = window.innerHeight;

            if (triggerRect.bottom + tooltipRect.height + 4 > viewportHeight) {
                // 하단에 공간이 부족하면 위쪽으로 이동
                tooltip.style.setProperty('top', 'auto', 'important');
                tooltip.style.setProperty('bottom', '100%', 'important');
                tooltip.style.setProperty('margin-top', '0', 'important');
                tooltip.style.setProperty('margin-bottom', '4px', 'important');
            }
        }, 0);
    }

    activeTooltip = tooltip;

    const cached = channelDataCache.get(channelId);
    if (cached && (Date.now() - cached.timestamp < 5 * 60 * 1000)) {
        updateTooltipContent(tooltip, cached.data);
        return;
    }

    tooltip.querySelector('.channel-title').textContent = '로딩 중...';

    fetch(`/channel-tooltip/${channelId}`)
        .then(response => {
            if (!response.ok) {
                return Promise.reject(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(result => {
            if (result.success) {
                channelDataCache.set(channelId, { data: result.data, timestamp: Date.now() });
                if (activeTooltip === tooltip) updateTooltipContent(tooltip, result.data);
            } else {
                if (activeTooltip === tooltip) tooltip.querySelector('.channel-title').textContent = result.error || '정보 로드 실패';
            }
        })
        .catch(error => {
            console.error('Error fetching channel tooltip:', error);
            if (activeTooltip === tooltip) tooltip.querySelector('.channel-title').textContent = '오류 발생';
        });
}

// 전역 변수로 이벤트 핸들러와 타이머 관리
let hideTimeout;
let showTimeout;
let tooltipEventHandlersAdded = false;

function handleTooltipMouseEnter(e) {
    if (!e.target || !e.target.classList) {
        return;
    }

    // 툴팁 내부에 마우스 진입 (우선 처리)
    if (e.target.closest && e.target.closest('.channel-tooltip')) {
        clearTimeout(hideTimeout);
        return;
    }

    // 채널 트리거에 마우스 진입 - 직접 타겟이거나 하위 요소일 경우 모두 처리
    let trigger = null;
    if (e.target.classList.contains('channel-tooltip-trigger')) {
        trigger = e.target;
    } else {
        // 이벤트 타겟이 트리거가 아니라면, 부모 중에서 트리거를 찾기
        trigger = e.target.closest('.channel-tooltip-trigger');
    }

    if (trigger) {
        const channelId = trigger.dataset.channelId;
        clearTimeout(hideTimeout);
        clearTimeout(showTimeout);
        showTimeout = setTimeout(() => showTooltip(trigger, channelId), 50); // 더 빠르게 표시
    } else {
        // 트리거가 아닌 요소에 마우스가 들어갔을 때, 툴팁과 관련된 영역인지 확인
        const relativeParent = e.target.closest('.relative');
        const cardContainer = e.target.closest('.bg-white.rounded-lg');

        if (relativeParent && relativeParent.querySelector('.channel-tooltip-trigger')) {
            clearTimeout(hideTimeout);
        } else if (cardContainer && cardContainer.querySelector('.channel-tooltip-trigger')) {
            clearTimeout(hideTimeout);
        } else {
            hideAllTooltips();
        }
    }
}

function handleTooltipClick(e) {
    if (!e.target || !e.target.classList) {
        return;
    }

    // 채널 트리거 클릭 - 직접 타겟이거나 하위 요소일 경우 모두 처리
    let trigger = null;
    if (e.target.classList.contains('channel-tooltip-trigger')) {
        trigger = e.target;
    } else {
        // 이벤트 타겟이 트리거가 아니라면, 부모 중에서 트리거를 찾기
        trigger = e.target.closest('.channel-tooltip-trigger');
    }

    if (trigger) {
        e.preventDefault();
        const channelId = trigger.dataset.channelId;
        clearTimeout(hideTimeout);
        clearTimeout(showTimeout);
        showTooltip(trigger, channelId);

        // 클릭 시에는 더 오래 유지되도록 설정
        setTimeout(() => {
            if (activeTooltip) {
                hideTimeout = setTimeout(hideAllTooltips, 3000); // 3초 후 자동 숨김
            }
        }, 100);
    } else {
    }
}

function handleTooltipMouseLeave(e) {
    if (!e.target || !e.target.classList) return;

    // 툴팁에서 마우스 이탈 (우선 처리)
    if (e.target.closest && e.target.closest('.channel-tooltip')) {
        hideTimeout = setTimeout(hideAllTooltips, 500); // 툴팁에서 이탈할 때도 여유 시간
        return;
    }

    // 채널 트리거에서 마우스 이탈 - 직접 타겟이거나 하위 요소일 경우 모두 처리
    let trigger = null;
    if (e.target.classList.contains('channel-tooltip-trigger')) {
        trigger = e.target;
    } else {
        trigger = e.target.closest('.channel-tooltip-trigger');
    }

    if (trigger) {
        clearTimeout(showTimeout);
        // 더 긴 지연으로 툴팁으로 마우스 이동할 시간 제공
        hideTimeout = setTimeout(hideAllTooltips, 800);
        return;
    }

    // 트리거 영역에서 마우스 이탈 시 관대하게 처리
    const relativeParent = e.target.closest('.relative');
    if (relativeParent && relativeParent.querySelector('.channel-tooltip-trigger')) {
        hideTimeout = setTimeout(hideAllTooltips, 500); // 더 긴 지연으로 관대하게
    }
}

// 스크롤 시 툴팁 숨김 처리
function handleScrollHideTooltip(e) {
    if (activeTooltip) {
        clearTimeout(hideTimeout);
        clearTimeout(showTimeout);
        hideAllTooltips();
    }
}

// [수정] 이벤트 위임을 사용하여 동적으로 생성된 요소에 대해서도 안정적으로 작동
function setupChannelTooltips() {
    // 중복 등록 방지
    if (tooltipEventHandlersAdded) {
        return;
    }

    // mouseover/mouseout 이벤트 사용 (버블링됨)
    document.addEventListener('mouseover', handleTooltipMouseEnter, true);
    document.addEventListener('mouseout', handleTooltipMouseLeave, true);
    // 클릭 이벤트 추가
    document.addEventListener('click', handleTooltipClick, true);
    // 스크롤 이벤트 추가 - 스크롤 시 툴팁 숨김
    document.addEventListener('scroll', handleScrollHideTooltip, true);

    // 추가 디버깅: 이벤트가 제대로 등록되었는지 확인

    // 기존 트리거 요소들 확인
    setTimeout(() => {
        const triggers = document.querySelectorAll('.channel-tooltip-trigger');
    }, 500);

    tooltipEventHandlersAdded = true;
}


// ===================================================================================
// 메인 로직 (Main Logic)
// ===================================================================================

class VideoManager {
    constructor() {
        this.allVideos = [];
        this.filteredVideos = [];
        this.currentFilters = { date: '전체', subs: 'all', type: 'all', sort: 'publishedAt', direction: 'desc' };
        this.isLoading = false;
        this.currentQuery = '';
        this.currentCategory = '0';
        this.recommendedTags = [];
        this.nextPageToken = null;

        this.initialize();
    }

    initialize() {
        if (window.pageData) {
            this.currentQuery = window.pageData.query || '';
            this.currentCategory = window.pageData.category || '0';
        }
        this.setupFilterListeners();
        this.setupSearchForm();
        setupChannelTooltips(); // 전역 이벤트 위임 설정


        this.loadInitialData();
    }

    async fetchData(maxResults, pageToken = null, isLoadMore = false) {
        if (this.isLoading) {
            return;
        }
        this.isLoading = true;
        this.showLoading(isLoadMore);

        try {
            const params = new URLSearchParams({
                query: this.currentQuery,
                category: this.currentCategory,
                max_results: maxResults,
            });
            if (pageToken) {
                params.set('page_token', pageToken);
            }
            const response = await fetch(`/api/videos?${params.toString()}`, { headers: { 'Accept': 'application/json' } });
            const data = await response.json();

            if (data.success) {
                const newVideos = data.videos || [];
                if (isLoadMore) {
                    const existingVideoIds = new Set(this.allVideos.map(v => v.id));
                    const uniqueNewVideos = newVideos.filter(v => !existingVideoIds.has(v.id));
                    this.allVideos = this.allVideos.concat(uniqueNewVideos);
                } else {
                    this.allVideos = newVideos;
                    this.recommendedTags = data.recommended_tags || [];
                }
                this.nextPageToken = data.next_page_token || null;

                this.filterAndSortVideos();
                this.renderVideos();
                if (!isLoadMore) this.renderRecommendedTags();
                this.renderLoadMoreButton();
            } else {
                showCustomAlert(data.error || "데이터 로딩에 실패했습니다.");
            }
        } catch (error) {
            console.error('Fetch data error:', error);
            showCustomAlert('비디오 데이터를 불러오는 중 네트워크 오류가 발생했습니다.');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    loadInitialData() {

        // 이미 데이터가 있고 같은 쿼리라면 중복 로드 방지
        if (this.allVideos.length > 0 && !this.isLoading) {
            return;
        }

        const initialLoadCount = this.currentQuery ? 100 : 50;
        this.fetchData(initialLoadCount, null, false);
    }

    loadMoreResults() {
        if (this.nextPageToken) {
            this.fetchData(50, this.nextPageToken, true);
        }
    }

    renderLoadMoreButton() {
        const container = document.getElementById('pagination-container');
        const topButton = document.getElementById('load-more-top-btn');

        if (this.nextPageToken) {
            // 하단 버튼
            if (container) {
                container.innerHTML = `
                    <button id="load-more-btn" class="px-6 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition">
                        결과 더보기
                    </button>
                `;
                document.getElementById('load-more-btn').addEventListener('click', () => this.loadMoreResults());
            }

            // 상단 버튼
            if (topButton) {
                topButton.classList.remove('hidden');
                topButton.onclick = () => this.loadMoreResults();
            }
        } else {
            // 하단 처리
            if (container) {
                if (this.allVideos.length > 0) {
                    container.innerHTML = '<p class="text-sm text-gray-500">마지막 결과입니다.</p>';
                } else {
                    container.innerHTML = '';
                }
            }

            // 상단 버튼 숨김
            if (topButton) {
                topButton.classList.add('hidden');
            }
        }
    }

    setupFilterListeners() {
        document.querySelectorAll('.date-filter-option, .subs-filter-option, .type-filter-option').forEach(option => {
            option.addEventListener('click', (e) => {
                e.preventDefault();
                const dropdown = e.target.closest('.filter-dropdown');
                let filterType = '';
                if (dropdown.querySelector('.date-filter-button')) filterType = 'date';
                else if (dropdown.querySelector('.subs-filter-button')) filterType = 'subs';
                else if (dropdown.querySelector('.type-filter-button')) filterType = 'type';

                if (filterType) this.applyFilter(filterType, e.target.dataset.value);
            });
        });
        document.querySelectorAll('.sort-option, .sortable-header').forEach(el => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                const sortBy = el.dataset.sort;
                let newDirection = 'desc';
                if (this.currentFilters.sort === sortBy && this.currentFilters.direction === 'desc') {
                    newDirection = 'asc';
                }
                this.applySorting(sortBy, newDirection);
            });
        });
    }

    setupSearchForm() {
        const searchForm = document.getElementById('searchForm');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const query = document.getElementById('searchInput').value.trim();
                if (query) {
                    if (window.pageData && !window.pageData.canSearch) {
                        showCustomAlert('검색 기능은 로그인 후 마이페이지에서 API 키를 등록해야 사용할 수 있습니다.');
                        return;
                    }
                    const url = new URL(window.location.origin + '/');
                    url.searchParams.set('query', query);
                    window.location.href = url.toString();
                }
            });
        }
    }

    applyFilter(filterType, value) {
        this.currentFilters[filterType] = value;
        this.updateFilterDisplay(filterType, value);
        this.filterAndSortVideos();
        this.renderVideos();
    }

    applySorting(sortBy, direction) {
        this.currentFilters.sort = sortBy;
        this.currentFilters.direction = direction;
        this.updateSortDisplay(sortBy, direction);
        this.filterAndSortVideos();
        this.renderVideos();
    }

    filterAndSortVideos() {
        let videos = [...this.allVideos];

        if (this.currentFilters.date !== '전체') {
            const daysAgo = parseInt(this.currentFilters.date.replace('일 전', ''));
            if (!isNaN(daysAgo)) {
                const cutoffDate = new Date();
                cutoffDate.setDate(cutoffDate.getDate() - daysAgo);
                videos = videos.filter(video => new Date(video.publishedAt) >= cutoffDate);
            }
        }

        if (this.currentFilters.subs !== 'all') {
            const subThresholds = { 'tiny': [0, 5000], 'micro': [0, 10000], 'small': [10000, 100000], 'medium': [100000, 1000000], 'large': [1000000, Infinity] };
            const threshold = subThresholds[this.currentFilters.subs];
            if (threshold) videos = videos.filter(video => (video.subscriberCount || 0) >= threshold[0] && (video.subscriberCount || 0) < threshold[1]);
        }

        if (this.currentFilters.type !== 'all') {
            videos = videos.filter(video => {
                const duration = this.parseDuration(video.duration);
                if (this.currentFilters.type === 'short') return duration > 0 && duration <= 60;
                if (this.currentFilters.type === 'video') return duration > 60;
                return true;
            });
        }

        videos.sort((a, b) => {
            let valueA, valueB;
            const sortKey = this.currentFilters.sort;
            if (sortKey === 'publishedAt') {
                valueA = new Date(a.publishedAt);
                valueB = new Date(b.publishedAt);
            } else {
                valueA = parseFloat(a[sortKey]) || 0;
                valueB = parseFloat(b[sortKey]) || 0;
            }

            if (this.currentFilters.direction === 'asc') {
                return valueA > valueB ? 1 : -1;
            } else {
                return valueA < valueB ? 1 : -1;
            }
        });

        videos.forEach((video, index) => {
            video.rank = index + 1;
        });

        this.filteredVideos = videos;
    }

    renderVideos() {
        const gridView = document.getElementById('grid-view');
        const listView = document.getElementById('list-view');
        const isListViewActive = listView && !listView.classList.contains('hidden');

        const gridContent = gridView ? gridView.querySelector('.grid') : null;
        if (isListViewActive) {
            this.renderListView(listView);
        } else if (gridContent) {
            this.renderGridView(gridContent);
        }

        this.updateVideoCount();

    }

    renderGridView(container) {
        const adHtml = `
            <div class="sm:col-span-2 lg:col-span-3 xl:col-span-4 py-4">
                <div class="bg-gray-50 rounded-lg flex items-center justify-center mx-auto" style="max-width: 728px; min-height: 90px;">
                    <ins class="adsbygoogle"
                         style="display:inline-block;width:728px;height:90px"
                         data-ad-client="${AD_CLIENT_ID}"
                         data-ad-slot="${AD_GRID_SLOT_ID}"></ins>
                </div>
            </div>
        `;

        const pd = (typeof window !== 'undefined' && window.pageData) ? window.pageData : {};
        const savedIds = new Set(Array.isArray(pd.savedChannelIds) ? pd.savedChannelIds : []);
        let adCount = 0;

        const htmlContent = this.filteredVideos.length ? this.filteredVideos.reduce((acc, video, index) => {
            const videoId = typeof video.id === 'object' ? video.id.videoId : video.id;
            const videoTitle = escapeAttr(video.title);
            const channelTitle = escapeAttr(video.channelTitle);

            // [복원] 누락되었던 비디오 카드 HTML 코드
            const videoHtml = `
                <div class="bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow duration-300 flex flex-col" style="overflow: visible;">
                    <div class="relative group">
                        <a href="https://www.youtube.com/watch?v=${videoId}" target="_blank" class="block"><img class="w-full h-48 object-cover rounded-t-lg" src="${video.thumbnail_url}" alt="${videoTitle}" onerror="this.src='/static/images/default-thumbnail.svg'"></a>
                        <button class="save-video-btn absolute top-2 left-2 p-2 bg-black bg-opacity-50 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-opacity-75" title="영상 저장" data-video-id="${videoId}" data-video-title="${videoTitle}" data-channel-id="${video.channelId}" data-channel-title="${channelTitle}" data-thumbnail-url="${video.thumbnail_url}">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.5 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" /></svg>
                        </button>
                        ${video.viewCount < 10000 && video.publishedAt ? `<span class="absolute top-2 right-2 px-2 py-1 bg-yellow-400 text-white text-xs font-semibold rounded-full shadow-md">💎 숨은 보석</span>` : ''}
                        <a href="/download-thumbnail?url=${encodeURIComponent(video.thumbnail_url)}&title=${encodeURIComponent(video.title)}" title="썸네일 다운로드" class="absolute ${video.viewCount < 10000 && video.publishedAt ? 'top-12 right-2' : 'top-2 right-2'} p-2 bg-black bg-opacity-50 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-opacity-75"><svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" /></svg></a>
                    </div>
                    <div class="p-4 flex flex-col flex-grow">
                        <h3 class="font-bold text-base mb-2 h-12 line-clamp-2"><a href="https://www.youtube.com/watch?v=${videoId}" target="_blank" class="hover:text-blue-600">${video.title}</a></h3>
                        <div class="text-sm text-gray-600 mb-3"><div class="flex items-center justify-between"><div class="flex items-center min-w-0"><button class="save-channel-btn flex-shrink-0 p-1 rounded-full hover:bg-gray-100 ${savedIds.has(video.channelId) ? 'text-blue-600' : 'text-gray-400'}" title="채널 저장/취소" data-channel-id="${video.channelId}" data-channel-title="${channelTitle}">${savedIds.has(video.channelId) ? `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M5 21V5q0-.825.588-1.413T7 3h10q.825 0 1.413.588T19 5v16l-7-3Z"/></svg>` : `<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" /></svg>`}</button><div class="relative min-w-0 ml-2"><span class="font-semibold hover:text-blue-600 cursor-pointer channel-tooltip-trigger block truncate" data-channel-id="${video.channelId}" style="pointer-events: auto; z-index: 1; position: relative;">${video.channelTitle}</span>${createChannelTooltipHTML()}</div><span class="mx-1.5 text-gray-400 flex-shrink-0">•</span><span class="text-xs text-gray-500 flex-shrink-0">${formatNumber(video.subscriberCount)}</span></div><span class="text-xs text-gray-500 flex-shrink-0">${video.publishedAtFormatted}</span></div></div>
                        <div class="grid grid-cols-3 gap-1 mt-auto"><div class="bg-gray-50 rounded p-1.5 text-center"><div class="text-xs font-medium text-gray-800">${formatNumber(video.viewCount)}</div><div class="text-xs text-gray-500">조회수</div></div><div class="bg-blue-50 rounded p-1.5 text-center"><div class="text-xs font-medium text-blue-700">${formatNumber(video.likeCount)}</div><div class="text-xs text-blue-600">좋아요</div></div><div class="bg-green-50 rounded p-1.5 text-center"><div class="text-xs font-medium text-green-700">${formatNumber(video.commentCount)}</div><div class="text-xs text-green-600">댓글</div></div></div>
                    </div>
                </div>
            `;
            acc += videoHtml;

            // 요청하신대로 3줄(12개)마다 광고 삽입
            if ((index + 1) % 12 === 0) {
                acc += adHtml;
                adCount++;
            }
            return acc;
        }, '') : this.renderEmptyState();

        container.innerHTML = htmlContent;

        if (adCount > 0) {
            setTimeout(() => {
                container.querySelectorAll('.adsbygoogle').forEach(() => {
                    (adsbygoogle = window.adsbygoogle || []).push({});
                });
            }, 100);
        }
    }

    renderListView(container) {
        const adHtml = `
           <tr class="bg-gray-50">
                <td colspan="7" class="px-2 py-2 text-center">
                    <ins class="adsbygoogle"
                         style="display:inline-block;width:728px;height:90px"
                         data-ad-client="${AD_CLIENT_ID}"
                         data-ad-slot="${AD_LIST_SLOT_ID}"></ins>
                </td>
            </tr>
        `;

        const pd = (typeof window !== 'undefined' && window.pageData) ? window.pageData : {};
        const savedIds = new Set(Array.isArray(pd.savedChannelIds) ? pd.savedChannelIds : []);
        const tbody = container.querySelector('tbody');
        if (!tbody) return;
        let adCount = 0;

        const htmlContent = this.filteredVideos.length ? this.filteredVideos.reduce((acc, video, index) => {
            const videoId = typeof video.id === 'object' ? video.id.videoId : video.id;
            const videoTitle = escapeAttr(video.title);
            const channelTitle = escapeAttr(video.channelTitle);
            const savedClass = savedIds.has(video.channelId) ? 'is-saved text-blue-600' : 'text-gray-400';
            const iconSvg = savedIds.has(video.channelId) ? `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M5 21V5q0-.825.588-1.413T7 3h10q.825 0 1.413.588T19 5v16l-7-3Z"/></svg>` : `<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" /></svg>`;

            // [복원] 누락되었던 비디오 행 HTML 코드
            const videoHtml = `
                <tr class="hover:bg-gray-50">
                    <td class="px-2 py-4 text-center"><span class="text-sm font-medium text-gray-700">${video.rank}</span></td>
                    <td class="px-6 py-4"><div class="flex items-center space-x-4"><div class="flex-shrink-0 relative group"><a href="https://www.youtube.com/watch?v=${videoId}" target="_blank"><img class="h-16 w-28 object-cover rounded-md shadow" src="${video.thumbnail_url_medium}" alt="${videoTitle} 썸네일" onerror="this.src='/static/images/default-thumbnail.svg'"></a><button class="save-video-btn absolute top-1 left-1 p-1 bg-black bg-opacity-50 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-opacity-75" title="영상 저장" data-video-id="${videoId}" data-video-title="${videoTitle}" data-channel-id="${video.channelId}" data-channel-title="${channelTitle}" data-thumbnail-url="${video.thumbnail_url_medium}"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.5 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" /></svg></button></div><div class="min-w-0"><a href="https://www.youtube.com/watch?v=${videoId}" target="_blank" class="block text-sm font-semibold text-gray-900 truncate hover:text-blue-600" title="${videoTitle}">${video.title}</a><div class="text-sm text-gray-500 mt-1"><div class="flex items-center"><button class="save-channel-btn flex-shrink-0 p-1 rounded-full hover:bg-gray-100 ${savedClass}" title="채널 저장/취소" data-channel-id="${video.channelId}" data-channel-title="${channelTitle}">${iconSvg}</button><div class="relative ml-2"><span class="hover:text-gray-800 cursor-pointer channel-tooltip-trigger" data-channel-id="${video.channelId}" title="${channelTitle}">${video.channelTitle}</span>${createChannelTooltipHTML()}</div>${video.subscriberCount ? `<span class="mx-1.5 text-gray-400">-</span><span class="text-xs">${formatNumber(video.subscriberCount)}</span>` : ''}</div></div></div></div></td>
                    <td class="px-4 py-4 text-center whitespace-nowrap"><p class="text-sm font-medium text-gray-900">${formatNumber(video.likeCount)}</p><p class="text-xs text-green-600">(${(video.likeRate || 0).toFixed(2)}%)</p></td>
                    <td class="px-4 py-4 text-center whitespace-nowrap"><p class="text-sm font-medium text-gray-900">${formatNumber(video.commentCount)}</p></td>
                    <td class="px-4 py-4 text-center whitespace-nowrap"><p class="text-sm font-medium text-gray-900">${formatNumber(video.viewCount)}</p><p class="text-xs text-gray-500">${formatNumber(video.viewsPerDay)}/일</p></td>
                    <td class="px-6 py-4 text-center whitespace-nowrap"><p class="text-sm text-gray-600">${video.publishedAtFormatted}</p></td>
                    <td class="px-6 py-4 whitespace-nowrap text-center text-sm font-medium"><a href="/download-thumbnail?url=${encodeURIComponent(video.thumbnail_url)}&title=${encodeURIComponent(videoTitle)}" title="썸네일 다운로드" class="inline-block p-2 text-gray-400 transition rounded-full hover:bg-gray-100 hover:text-blue-500"><svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" /></svg></a></td>
                </tr>
            `;
            acc += videoHtml;

            if ((index + 1) % 5 === 0) {
                acc += adHtml;
                adCount++;
            }
            return acc;
        }, '') : `<tr><td colspan="7">${this.renderEmptyState()}</td></tr>`;

        tbody.innerHTML = htmlContent;

        if (adCount > 0) {
            setTimeout(() => {
                tbody.querySelectorAll('.adsbygoogle').forEach(() => {
                    (adsbygoogle = window.adsbygoogle || []).push({});
                });
            }, 100);
        }
    }

    renderEmptyState() { return `<div class="text-center py-16"><p class="text-gray-500">표시할 영상이 없습니다.</p></div>`; }

    updateVideoCount() {
        const countElement = document.querySelector('.video-count');
        if (countElement) countElement.textContent = `총 ${this.filteredVideos.length.toLocaleString()}개 영상`;
    }

    showLoading(isLoadMore = false) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            const loadingText = document.getElementById('loading-text');
            if (loadingText) {
                loadingText.textContent = isLoadMore ? '결과 추가 중...' : '영상 데이터 분석 중';
            }
            overlay.classList.remove('hidden');
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.classList.add('hidden');
    }

    parseDuration(duration) {
        // [변경] 시간(H) 단위를 올바르게 처리하도록 수정
        if (!duration) return 0;
        const m = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
        if (!m) return 0;
        const h = parseInt(m[1] || '0', 10);
        const min = parseInt(m[2] || '0', 10);
        const s = parseInt(m[3] || '0', 10);
        return h * 3600 + min * 60 + s;
    }


    renderRecommendedTags() {
        const container = document.querySelector('.recommended-tags-container');
        if (!container) return;

        if (this.recommendedTags.length > 0) {
            const tagsHtml = this.recommendedTags.slice(0, 6).map(tag => {
                return `<button type="button" data-tag="${escapeAttr(tag)}" class="recommended-tag-btn text-xs bg-gray-100 text-gray-700 px-3 py-1 rounded-full hover:bg-gray-200 transition-colors cursor-pointer">#${tag}</button>`;
            }).join('');
            container.innerHTML = `<div class="flex flex-wrap gap-2 justify-center max-w-4xl mx-auto">${tagsHtml}</div>`;
            this.setupRecommendedTagsListener();
        } else {
            container.innerHTML = '';
        }
    }

    setupRecommendedTagsListener() {
        const container = document.querySelector('.recommended-tags-container');
        if (!container) return;

        container.addEventListener('click', (e) => {
            if (e.target.classList.contains('recommended-tag-btn')) {
                const searchInput = document.getElementById('searchInput');
                const tag = e.target.dataset.tag;
                if (searchInput && tag) {
                    searchInput.value = tag;
                    searchInput.focus();
                }
            }
        });
    }

    updateFilterDisplay(filterType, value) {
        const button = document.querySelector(`.${filterType}-filter-button`);
        if (button) {
            const displayValue = { date: { '전체': '기간', '1일 전': '1일 전', '7일 전': '1주일 전', '30일 전': '1개월 전' }, subs: { 'all': '구독자', 'tiny': '5천 미만', 'micro': '1만 미만', 'small': '1만-10만', 'medium': '10만-100만', 'large': '100만+' }, type: { 'all': '유형', 'short': '숏츠', 'video': '일반 영상' } }[filterType]?.[value] || value;
            button.querySelector('span').textContent = displayValue;
        }
    }

    updateSortDisplay(sortBy, direction) {
        document.querySelectorAll('.sortable-header .sort-indicator').forEach(ind => ind.textContent = '↕');
        const activeHeader = document.querySelector(`.sortable-header[data-sort="${sortBy}"] .sort-indicator`);
        if (activeHeader) {
            activeHeader.textContent = direction === 'asc' ? '↑' : '↓';
        }

        const button = document.querySelector('.sort-button');
        if (button) {
            const displayValue = { 'publishedAt': '최신순', 'viewCount': '조회수 높은순', 'likeCount': '좋아요 높은순', 'commentCount': '댓글 많은순' }[sortBy] || sortBy;
            button.querySelector('span').textContent = `${displayValue}`;
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    if (!window.pageData) window.pageData = {};

    if (window.videoManager) {
        return;
    }
    window.videoManager = new VideoManager();
});