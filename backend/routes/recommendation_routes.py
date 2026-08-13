"""
FastAPI Router for 4-Stage Multi-Objective Clinical Recommendation Engine.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from backend.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    FeedbackEvent
)
from backend.recommendation.engine import recommendation_pipeline

router = APIRouter(prefix="/v1/recommendations", tags=["Recommendation Engine"])


@router.post("/clinical-interventions", response_model=RecommendationResponse, summary="Generate Personalized Clinical Interventions")
async def recommend_clinical_interventions(request: RecommendationRequest) -> RecommendationResponse:
    """
    Executes the full 4-stage recommendation pipeline to generate evidence-based clinical interventions.
    """
    try:
        request.domain = "clinical_intervention"
        return await recommendation_pipeline.recommend(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate clinical recommendations: {str(e)}"
        )


@router.post("/lifestyle-pathways", response_model=RecommendationResponse, summary="Generate Personalized Lifestyle Pathways")
async def recommend_lifestyle_pathways(request: RecommendationRequest) -> RecommendationResponse:
    """
    Executes the full 4-stage recommendation pipeline to generate lifestyle, nutritional, and metabolic pathways.
    """
    try:
        request.domain = "lifestyle_pathway"
        return await recommendation_pipeline.recommend(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate lifestyle recommendations: {str(e)}"
        )


@router.post("/clinical-trials", response_model=RecommendationResponse, summary="Match Patient to Investigational Clinical Trials")
async def match_clinical_trials(request: RecommendationRequest) -> RecommendationResponse:
    """
    Executes the full 4-stage recommendation pipeline to match patients to eligible investigational clinical trials.
    """
    try:
        request.domain = "clinical_trial"
        return await recommendation_pipeline.recommend(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to match clinical trials: {str(e)}"
        )


@router.post("/generate", response_model=RecommendationResponse, summary="Generic Multi-Stage Recommendation Engine Entrypoint")
async def generate_recommendations(request: RecommendationRequest) -> RecommendationResponse:
    """
    Unified entrypoint for the 4-stage recommendation engine supporting any specified clinical domain.
    """
    try:
        return await recommendation_pipeline.recommend(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation pipeline execution failed: {str(e)}"
        )


@router.post("/feedback", summary="Record Clinician / Patient Feedback for Bandit Online Learning")
async def record_recommendation_feedback(feedback: FeedbackEvent) -> Dict[str, Any]:
    """
    Ingests online feedback (clicks, acceptances, rejections) to update Contextual Thompson Sampling Beta distributions.
    """
    try:
        return recommendation_pipeline.record_feedback(feedback)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record feedback: {str(e)}"
        )
