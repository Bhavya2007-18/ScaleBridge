import pytest
from app.seed.demo_data import seed_demo_data
from app.services.assessment_service import AssessmentService

def test_end_to_end_assessment_workflow(db_session):
    seed_info = seed_demo_data(db_session)
    scenario_id = seed_info["scenario_id"]
    
    svc = AssessmentService()
    assessment = svc.run_assessment(db_session, scenario_id)
    
    assert assessment.id is not None
    assert assessment.status == "completed"
    assert len(assessment.calculations) > 0
    assert len(assessment.validation_tasks) > 0
