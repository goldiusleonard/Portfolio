"""API router."""

from fastapi import APIRouter

from app.api.routers.agent import agent_router
from app.api.routers.batch_routes import batch_router
from app.api.routers.category import category_router
from app.api.routers.category_sub_category_data import catsubcat_router
from app.api.routers.comment import comment_router
from app.api.routers.comment_recording import comment_recording_router
from app.api.routers.content import content_router
from app.api.routers.creator_details import creator_details_router
from app.api.routers.cross_category_insight import cross_category_insight_router
from app.api.routers.direct_link_analysis import direct_link_analysis_router
from app.api.routers.engagement import engagement_router
from app.api.routers.engagement_risk import engagement_risk_router
from app.api.routers.extraction_law_pdf import extraction_law_router
from app.api.routers.law_violation import law_violation_router
from app.api.routers.live_stream import live_stream_router
from app.api.routers.login_authentication import login_authentication_router
from app.api.routers.mindmap import filter_label_router
from app.api.routers.news import news_router
from app.api.routers.notification import notification_router
from app.api.routers.profile import profile_router
from app.api.routers.role import role_router
from app.api.routers.similarity_agent import similarity_agent_router
from app.api.routers.user import user_router
from app.api.routers.user_role import user_role_router
from app.api.routers.watchlist_tracker import router as watchlist_tracker_router

router = APIRouter()

router.include_router(user_router)
router.include_router(role_router)
router.include_router(user_role_router)
router.include_router(login_authentication_router)
router.include_router(category_router)
router.include_router(agent_router)
router.include_router(news_router)
router.include_router(profile_router)
router.include_router(content_router)
router.include_router(creator_details_router)
router.include_router(comment_router)
router.include_router(cross_category_insight_router)
router.include_router(engagement_router)
router.include_router(engagement_risk_router)
router.include_router(batch_router)
router.include_router(direct_link_analysis_router)
router.include_router(law_violation_router)
router.include_router(filter_label_router)
router.include_router(catsubcat_router)
router.include_router(comment_recording_router)
router.include_router(live_stream_router)
router.include_router(notification_router)
router.include_router(watchlist_tracker_router)
router.include_router(similarity_agent_router)
router.include_router(extraction_law_router)
