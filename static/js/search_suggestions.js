document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const suggestionsList = document.getElementById('suggestions-list');

    // 필수 요소들이 없으면 함수를 종료합니다.
    if (!searchForm || !searchInput || !suggestionsList) {
        // 검색 폼이 없는 페이지에서는 조용히 종료
        return;
    }

    // Debounce 함수: 과도한 API 호출을 방지하여 성능을 최적화합니다.
    // 사용자가 타이핑을 멈춘 후 300ms가 지나면 콜백 함수를 실행합니다.
    const debounce = (func, delay) => {
        let timeoutId;
        return (...args) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    };

    // 추천 목록을 화면에 표시하는 함수
    const renderSuggestions = (suggestions) => {
        // 이전에 표시된 목록을 초기화합니다.
        suggestionsList.innerHTML = '';

        if (suggestions.length === 0) {
            suggestionsList.classList.add('hidden');
            return;
        }

        // 서버에서 받은 추천 목록으로 새로운 리스트를 생성합니다.
        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'px-4 py-2 cursor-pointer hover:bg-gray-100';
            item.textContent = suggestion;
            
            // 추천 항목 클릭 시 동작 정의
            item.addEventListener('click', () => {
                searchInput.value = suggestion; // 검색창에 선택한 텍스트 채우기
                suggestionsList.classList.add('hidden'); // 추천 목록 숨기기
                searchForm.submit(); // 검색 فرم 제출
            });
            suggestionsList.appendChild(item);
        });

        // 추천 목록을 화면에 보여줍니다.
        suggestionsList.classList.remove('hidden');
    };
    
    // API를 호출하여 추천 데이터를 가져오는 비동기 함수
    const fetchSuggestions = async (query) => {
        if (query.trim().length === 0) {
            renderSuggestions([]);
            return;
        }

        try {
            // 백엔드의 /suggestions 엔드포인트에 GET 요청
            const response = await fetch(`/suggestions?q=${encodeURIComponent(query)}`);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            renderSuggestions(data.suggestions || []);
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            renderSuggestions([]); // 에러 발생 시 목록 숨기기
        }
    };

    // 300ms 지연 시간을 적용한 Debounce 버전의 fetch 함수 생성
    const debouncedFetch = debounce(fetchSuggestions, 300);

    // 검색창에 키보드 입력이 발생할 때마다 Debounce 처리된 함수를 호출
    searchInput.addEventListener('input', () => {
        debouncedFetch(searchInput.value);
    });

    // 검색창 외부를 클릭하면 추천 목록을 숨깁니다.
    document.addEventListener('click', (event) => {
        if (!searchForm.contains(event.target)) {
            suggestionsList.classList.add('hidden');
        }
    });
});