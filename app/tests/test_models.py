"""
Test runner for the Intikhab election application.

This file imports all model tests to ensure they are discovered by Django's test runner.
"""

from .test_election_model import ElectionModelTest
from .test_party_model import PartyModelTest  
from .test_candidate_model import CandidateModelTest
from .test_vote_model import VoteModelTest

__all__ = [
    'ElectionModelTest',
    'PartyModelTest', 
    'CandidateModelTest',
    'VoteModelTest',
]