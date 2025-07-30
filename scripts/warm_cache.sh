#!/bin/bash
# 인기동향 캐시 갱신 스크립트

cd /opt/render/project/src
python background_jobs.py warm_trending_cache

echo "Trending cache warmed at $(date)"