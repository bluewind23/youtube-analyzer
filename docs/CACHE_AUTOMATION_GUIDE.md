# 캐시 자동 갱신 설정 가이드

Render.com 무료 플랜에서 인기동향 영상 캐시를 자동으로 갱신하는 방법들입니다.

## 방법 1: GitHub Actions (추천) 🌟

### 1. 환경변수 설정
Render 대시보드에서 다음 환경변수를 추가하세요:

```
CACHE_WARM_TOKEN=your-secret-token-here-make-it-random-and-secure-12345
```

### 2. GitHub Secrets 설정
GitHub 리포지토리에서 Settings → Secrets and variables → Actions에서 다음을 추가:

```
APP_URL: https://your-app-name.onrender.com
CACHE_WARM_TOKEN: your-secret-token-here-make-it-random-and-secure-12345
```

### 3. 자동 실행 확인
- `.github/workflows/warm-cache.yml` 파일이 이미 추가되어 있습니다
- 3시간마다 자동으로 캐시를 갱신합니다
- GitHub Actions 탭에서 실행 상태를 확인할 수 있습니다

### 4. 수동 실행
필요시 GitHub Actions 탭에서 "Warm Trending Cache" 워크플로우를 수동으로 실행할 수 있습니다.

## 방법 2: EasyCron (외부 서비스)

### 1. EasyCron 가입
- https://www.easycron.com/ 에 가입 (무료 플랜 20개 작업)

### 2. Cron Job 생성
```
URL: https://your-app-name.onrender.com/api/warm-cache
Method: POST
Headers: Authorization: Bearer your-secret-token
Interval: Every 3 hours
```

## 방법 3: UptimeRobot (모니터링 + 캐시)

### 1. UptimeRobot 가입
- https://uptimerobot.com/ 에 가입 (무료 플랜 50개 모니터)

### 2. HTTP(s) 모니터 생성
```
Monitor Type: HTTP(s)
URL: https://your-app-name.onrender.com/api/warm-cache
Monitoring Interval: 3 hours
Custom HTTP Headers: Authorization: Bearer your-secret-token
```

## 캐시 시스템 효과

### Before vs After
| 구분 | Before | After (캐시 적용) |
|------|--------|------------------|
| 첫 방문자 로딩 시간 | 3-5초 | 0.1초 ⚡ |
| API 호출 횟수 | 매 요청마다 | 3시간마다 1회 |
| 사용자 경험 | 느림, 로딩 화면 | 부드럽고 빠름 🚀 |
| 서버 부하 | 높음 | 낮음 |

### 캐시되는 데이터
- 15개 주요 카테고리별 인기동향 영상
- 각 카테고리당 50개 영상 = 총 750개 영상 데이터
- 6시간 캐시 유지 (현재 설정)

## 트러블슈팅

### 캐시 갱신 실패 시
1. Render 로그 확인
2. GitHub Actions 로그 확인 
3. API 키 상태 확인 (admin panel)
4. 수동으로 `/api/warm-cache` 호출 테스트

### 모니터링
- Render 대시보드에서 앱 상태 확인
- GitHub Actions에서 실행 결과 확인
- 실제 사이트에서 로딩 속도 체감