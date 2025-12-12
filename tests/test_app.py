"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities

client = TestClient(app)


class TestGetActivities:
    """Test cases for retrieving activities"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_get_activities_contains_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data

    def test_get_activities_has_basketball(self):
        """Test that activities include Basketball"""
        response = client.get("/activities")
        data = response.json()
        assert "Basketball" in data

    def test_participants_is_list(self):
        """Test that participants field is always a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_data in data.values():
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Test cases for signing up participants"""

    def test_signup_new_participant_returns_200(self):
        """Test signing up a new participant returns status 200"""
        response = client.post(
            "/activities/Basketball/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200

    def test_signup_new_participant_adds_to_list(self):
        """Test that signup adds participant to the activity"""
        # Get initial count
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()["Basketball"]["participants"]
        initial_count = len(initial_participants)
        
        # Sign up new participant
        client.post("/activities/Basketball/signup?email=unique1@mergington.edu")
        
        # Check updated count
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()["Basketball"]["participants"]
        updated_count = len(updated_participants)
        
        assert updated_count == initial_count + 1

    def test_signup_returns_success_message(self):
        """Test that signup returns a success message"""
        response = client.post(
            "/activities/Basketball/signup?email=unique2@mergington.edu"
        )
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]

    def test_signup_invalid_activity_returns_404(self):
        """Test signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/InvalidActivity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404

    def test_signup_duplicate_participant_returns_400(self):
        """Test that signing up twice returns 400"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Tennis%20Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            f"/activities/Tennis%20Club/signup?email={email}"
        )
        assert response2.status_code == 400

    def test_signup_returns_error_detail_for_duplicate(self):
        """Test that duplicate signup returns appropriate error message"""
        email = "duplicate2@mergington.edu"
        
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]


class TestUnregister:
    """Test cases for unregistering participants"""

    def test_unregister_existing_participant_returns_200(self):
        """Test unregistering an existing participant returns 200"""
        # First sign up
        email = "unregister_test@mergington.edu"
        client.post(f"/activities/Art%20Class/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Art%20Class/unregister?email={email}"
        )
        assert response.status_code == 200

    def test_unregister_removes_participant(self):
        """Test that unregister removes participant from activity"""
        email = "remove_test@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Drama%20Club/signup?email={email}")
        
        # Get participants before unregister
        response_before = client.get("/activities")
        participants_before = response_before.json()["Drama Club"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Drama%20Club/unregister?email={email}")
        
        # Get participants after unregister
        response_after = client.get("/activities")
        participants_after = response_after.json()["Drama Club"]["participants"]
        
        assert email not in participants_after
        assert len(participants_after) == len(participants_before) - 1

    def test_unregister_invalid_activity_returns_404(self):
        """Test unregistering from non-existent activity returns 404"""
        response = client.delete(
            "/activities/InvalidActivity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_non_registered_participant_returns_400(self):
        """Test unregistering a non-registered participant returns 400"""
        response = client.delete(
            "/activities/Debate%20Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400

    def test_unregister_returns_success_message(self):
        """Test that unregister returns a success message"""
        email = "success_test@mergington.edu"
        
        # Sign up first
        client.post(f"/activities/Science%20Club/signup?email={email}")
        
        # Unregister
        response = client.delete(
            f"/activities/Science%20Club/unregister?email={email}"
        )
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]


class TestRootRedirect:
    """Test cases for root endpoint"""

    def test_root_redirects_to_static_index(self):
        """Test that GET / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
