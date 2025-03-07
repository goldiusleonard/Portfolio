"""API router."""

from fastapi import APIRouter

from routing.healthz_api import app
from routing.keyword_trend_fetching import keyword_fetching
from routing.keyword_trend_generator import keyword_generator

router = APIRouter()

router.include_router(keyword_generator)
router.include_router(keyword_fetching)
router.include_router(app)
