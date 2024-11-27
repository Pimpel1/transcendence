import json
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from .utils import mock_jwt_validate


class TournamentFlowTestCase(TestCase):

    def setUp(self):
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)

    @patch('matchmaker_app.utils.decorators.jwt_validate')
    @patch('matchmaker_app.utils.game.request_game_start')
    @patch('matchmaker_app.utils.game.request_game_create')
    def test_tournament_flow(
        self,
        mock_request_game_service_creation,
        mock_request_game_start,
        mock_validate
    ):
        mock_validate.side_effect = lambda request: mock_jwt_validate(
            request, 'TestPlayer1'
        )

        # Step 1: Create a tournament with the initial player
        create_tournament_url = reverse('tournaments')
        create_tournament_data = {
            "pool_size": 4,
            "tournament_name": "TestTournament",
            "players": ['TestPlayer1']
        }
        response = self.client.post(
            create_tournament_url,
            data=json.dumps(create_tournament_data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        tournament_id = response.json().get('tournament_id')
        self.assertIsNotNone(tournament_id)
        # Step 2: Verify that the tournament exists
        tournament_detail_url = reverse(
            'tournaments-detail',
            args=[tournament_id]
        )
        response = self.client.get(tournament_detail_url)
        self.assertEqual(response.status_code, 200)
        tournament_data = response.json()
        self.assertEqual(tournament_data['name'], "TestTournament")
        self.assertIn("TestPlayer1", tournament_data['players'])

        # Step 3: Add more players to fill the pool size
        update_tournament_url = reverse(
            'tournaments-detail',
            args=[tournament_id]
        )
        for i in range(2, 5):
            update_data = {"player": f"TestPlayer{i}"}
            mock_validate.side_effect = lambda request: mock_jwt_validate(
                request, f'TestPlayer{i}'
            )
            response = self.client.post(
                update_tournament_url,
                data=json.dumps(update_data),
                content_type="application/json"
            )
            self.assertEqual(response.status_code, 200)

            response = self.client.get(tournament_detail_url)
            self.assertEqual(response.status_code, 200)
            tournament_data = response.json()
            self.assertIn(f"TestPlayer{i}", tournament_data['players'])

            players_url = reverse('players')
            response = self.client.get(players_url)
            players_data = response.json().get('players', [])
            player_names = [
                player['name'] for player in players_data
            ]
            self.assertIn(f"TestPlayer{i}", player_names)

        # Step 4: Verify the games have been scheduled
        # and the first round is in progress
        # and that the game service has been called
        response = self.client.get(tournament_detail_url)
        self.assertEqual(response.status_code, 200)
        tournament_data = response.json()
        rounds = tournament_data['games']
        self.assertEqual(len(rounds), 3)
        round_1_games = rounds[0]['games']
        round_2_games = rounds[1]['games']
        round_3_games = rounds[2]['games']
        self.assertTrue(
            all(game['status'] == 'in_progress' for game in round_1_games)
        )
        self.assertTrue(
            all(game['status'] == 'scheduled' for game in round_2_games)
        )
        self.assertTrue(
            all(game['status'] == 'scheduled' for game in round_3_games)
        )
        self.assertEqual(mock_request_game_service_creation.call_count, 6)
        self.assertEqual(mock_request_game_start.call_count, 2)

        # Step 5: Submit results for round 1
        submit_result_url = reverse('game-result')
        round_1_game_ids = [game['id'] for game in round_1_games]
        for game_id in round_1_game_ids:
            result_data = {
                "game_id": game_id,
                "left_score": 2,
                "right_score": 1
            }
            response = self.client.post(
                submit_result_url,
                data=json.dumps(result_data),
                content_type="application/json",
                **{'HTTP_X_API_KEY': settings.MATCHMAKER_SERVICE_API_KEY}
            )
            self.assertEqual(response.status_code, 200)

        # Step 6: Verify that round 1 is completed and round 2 is in progress
        response = self.client.get(tournament_detail_url)
        self.assertEqual(response.status_code, 200)
        tournament_data = response.json()
        rounds = tournament_data['games']
        self.assertEqual(len(rounds), 3)
        round_1_games = rounds[0]['games']
        round_2_games = rounds[1]['games']
        round_3_games = rounds[2]['games']
        self.assertTrue(
            all(game['status'] == 'finished' for game in round_1_games)
        )
        self.assertTrue(
            all(game['status'] == 'in_progress' for game in round_2_games)
        )
        self.assertTrue(
            all(game['status'] == 'scheduled' for game in round_3_games)
        )
        self.assertEqual(mock_request_game_service_creation.call_count, 6)
        self.assertEqual(mock_request_game_start.call_count, 4)

        # Step 7: Submit results for round 2
        round_2_game_ids = [game['id'] for game in round_2_games]
        for game_id in round_2_game_ids:
            result_data = {
                "game_id": game_id,
                "left_score": 2,
                "right_score": 1
            }
            response = self.client.post(
                submit_result_url,
                data=json.dumps(result_data),
                content_type="application/json",
                **{'HTTP_X_API_KEY': settings.MATCHMAKER_SERVICE_API_KEY}
            )
            self.assertEqual(response.status_code, 200)

        # Step 8: Verify that round 2 is completed and round 3 is in progress
        response = self.client.get(tournament_detail_url)
        self.assertEqual(response.status_code, 200)
        tournament_data = response.json()
        rounds = tournament_data['games']
        self.assertEqual(len(rounds), 3)
        round_1_games = rounds[0]['games']
        round_2_games = rounds[1]['games']
        round_3_games = rounds[2]['games']
        self.assertTrue(
            all(game['status'] == 'finished' for game in round_1_games)
        )
        self.assertTrue(
            all(game['status'] == 'finished' for game in round_2_games)
        )
        self.assertTrue(
            all(game['status'] == 'in_progress' for game in round_3_games)
        )
        self.assertEqual(mock_request_game_service_creation.call_count, 6)
        self.assertEqual(mock_request_game_start.call_count, 6)

        # Step 9: Submit results for round 3
        round_3_game_ids = [game['id'] for game in round_3_games]
        for game_id in round_3_game_ids:
            result_data = {
                "game_id": game_id,
                "left_score": 2,
                "right_score": 1
            }
            response = self.client.post(
                submit_result_url,
                data=json.dumps(result_data),
                content_type="application/json",
                **{'HTTP_X_API_KEY': settings.MATCHMAKER_SERVICE_API_KEY}
            )
            self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_request_game_service_creation.call_count, 6)
        self.assertEqual(mock_request_game_start.call_count, 6)

        # Step 10: Verify that all games are completed
        response = self.client.get(tournament_detail_url)
        self.assertEqual(response.status_code, 200)
        tournament_data = response.json()
        rounds = tournament_data['games']
        self.assertEqual(len(rounds), 3)
        round_1_games = rounds[0]['games']
        round_2_games = rounds[1]['games']
        round_3_games = rounds[2]['games']
        self.assertTrue(
            all(game['status'] == 'finished' for game in round_1_games)
        )
        self.assertTrue(
            all(game['status'] == 'finished' for game in round_2_games)
        )
        self.assertTrue(
            all(game['status'] == 'finished' for game in round_3_games)
        )
        self.assertEqual(mock_request_game_service_creation.call_count, 6)
        self.assertEqual(mock_request_game_start.call_count, 6)

        # Step 11: Verify the tournament status is 'finished'
        response = self.client.get(tournament_detail_url)
        self.assertEqual(response.status_code, 200)
        tournament_data = response.json()
        self.assertEqual(tournament_data['status'], 'finished')
