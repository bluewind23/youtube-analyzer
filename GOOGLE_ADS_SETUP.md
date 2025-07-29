# 🎯 Google Ads 설정 가이드

YouTube 분석기에 Google Ads를 통합하는 방법을 안내합니다.

## 📋 설정 단계

### 1. Google AdSense 계정 준비

1. **Google AdSense 계정** 생성 (https://www.google.com/adsense)
2. **사이트 추가** 및 승인 대기
3. **광고 단위 생성**

### 2. 광고 배치 전략

현재 준비된 광고 배치:
- **그리드 뷰**: 6개 영상마다 1개 광고 (336x280 추천)
- **리스트 뷰**: 8개 영상마다 1개 광고 (728x90 추천)

### 3. AdSense 코드 추가

#### A. 자동 광고 방식 (추천)

`templates/base.html`의 `<head>` 섹션에 추가:

```html
<!-- Google AdSense 자동 광고 -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-YOUR_PUBLISHER_ID"
     crossorigin="anonymous"></script>
```

#### B. 수동 광고 배치 방식

1. **base.html에 AdSense 스크립트 추가**:
```html
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-YOUR_PUBLISHER_ID"
     crossorigin="anonymous"></script>
```

2. **광고 단위 생성 후 코드 교체**:

`templates/components/ad_placeholder.html` 수정:

```html
<!-- Grid View Ad -->
<div class="ad-container">
    <ins class="adsbygoogle"
         style="display:inline-block;width:336px;height:280px"
         data-ad-client="ca-pub-YOUR_PUBLISHER_ID"
         data-ad-slot="YOUR_AD_SLOT_ID"></ins>
</div>

<!-- List View Ad -->
<tr class="ad-container">
    <td colspan="7" class="px-6 py-4 text-center">
        <ins class="adsbygoogle"
             style="display:inline-block;width:728px;height:90px"
             data-ad-client="ca-pub-YOUR_PUBLISHER_ID"
             data-ad-slot="YOUR_AD_SLOT_ID"></ins>
    </td>
</tr>

<script>
(adsbygoogle = window.adsbygoogle || []).push({});
</script>
```

### 4. 현재 구현 상태

#### ✅ 준비 완료
- 광고 배치 위치 마크업 완료
- 반응형 광고 지원 준비
- 그리드/리스트 뷰 모두 대응
- 광고 식별 표시 (AdSense 정책 준수)

#### 🔧 설정 필요
- AdSense 계정의 Publisher ID
- 각 광고 위치별 Slot ID
- 광고 크기 최적화

### 5. 권장 광고 크기

#### 그리드 뷰
- **중간 직사각형**: 336x280 (가장 수익성 높음)
- **대형 직사각형**: 336x280
- **반응형**: 자동 크기 조정

#### 리스트 뷰
- **리더보드**: 728x90
- **대형 리더보드**: 970x90
- **반응형**: 자동 크기 조정

### 6. 자동 광고 vs 수동 광고

#### 자동 광고 (추천)
**장점**:
- 설정 간단 (스크립트 1개만 추가)
- Google이 최적 위치 자동 선택
- 수익 최적화 자동화
- 새로운 광고 형식 자동 적용

**단점**:
- 광고 위치 제어 제한
- 사용자 경험에 영향 가능

**설정 방법**:
```html
<!-- base.html의 <head>에 추가 -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-YOUR_PUBLISHER_ID"
     crossorigin="anonymous"></script>

<!-- AdSense에서 자동 광고 활성화 -->
```

#### 수동 광고
**장점**:
- 정확한 위치 제어
- 사용자 경험 최적화
- 디자인과의 조화

**단점**:
- 설정 복잡
- 광고 단위별 개별 관리
- 최적화 수동 필요

### 7. 성능 모니터링

Google AdSense 대시보드에서 확인:
- **수익**: 일/월별 수익 추이
- **페이지뷰**: 광고 노출 횟수
- **클릭률**: CTR 최적화 지표
- **eCPM**: 효과적인 수익 측정

### 8. 정책 준수사항

#### 필수 준수
- ✅ 광고와 콘텐츠 명확히 구분
- ✅ "광고" 또는 "스폰서" 라벨 표시
- ✅ 모바일 최적화
- ✅ 페이지 로딩 속도 유지
- ✅ 사용자 경험 저해 금지

#### 금지사항
- ❌ 광고 클릭 유도 금지
- ❌ 광고 위치 오해 유도 금지
- ❌ 과도한 광고 밀도
- ❌ 팝업/팝언더 광고

### 9. 실제 적용 순서

#### 단계 1: 자동 광고로 시작 (권장)
1. AdSense 계정 생성 및 승인
2. `base.html`에 자동 광고 스크립트 추가
3. AdSense에서 자동 광고 설정
4. 2-3주 수익 데이터 수집

#### 단계 2: 수동 최적화 (옵션)
1. 자동 광고 성과 분석
2. 저성과 위치 식별
3. 수동 광고 단위로 교체
4. A/B 테스트 실시

### 10. 예상 수익

일반적인 YouTube 관련 사이트:
- **페이지뷰당**: $0.001 - $0.005
- **클릭률**: 1-3%
- **월 10만 PV**: $100 - $500 예상

### 📞 지원

- **Google AdSense 고객센터**: https://support.google.com/adsense
- **정책 가이드**: https://support.google.com/adsense/answer/48182
- **최적화 가이드**: https://support.google.com/adsense/answer/9183549