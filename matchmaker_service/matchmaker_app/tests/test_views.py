import json
from unittest.mock import patch

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from matchmaker_app.models import Game, Player, Tournament
from .utils import mock_jwt_validate


class ViewTests(TestCase):
    """Tests for views."""

    def setUp(self):
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)
        self.player1 = Player.objects.create(name="Player One")
        self.player2 = Player.objects.create(name="Player Two")
        self.player3 = Player.objects.create(name="Player Three")
        self.game1 = Game.objects.create(
            id='game_id_1',
            player1=self.player1,
            player2=self.player2,
            player1_name='Player One',
            player2_name='Player Two',
            status='waiting_for_players',
            player1_score=3,
            player2_score=2,
            finished_at=None
        )
        self.game2 = Game.objects.create(
            id='game_id_2',
            player1=self.player1,
            player2=self.player3,
            player1_name='Player One',
            player2_name='Player Three',
            status='in_progress',
            player1_score=4,
            player2_score=3,
            finished_at=None
        )
        self.game3 = Game.objects.create(
            id='game_id_3',
            player1=self.player2,
            player2=self.player1,
            player1_name='Player Two',
            player2_name='Player One',
            status='finished',
            player1_score=2,
            player2_score=5,
            finished_at='2024-07-30 12:00:00'
        )
        self.game4 = Game.objects.create(
            id='game_id_4',
            player1=self.player3,
            player2=self.player1,
            player1_name='Player Three',
            player2_name='Player One',
            status='finished',
            player1_score=1,
            player2_score=2,
            finished_at='2024-07-31 14:00:00'
        )
        self.game5 = Game.objects.create(
            id='game_id_5',
            player1=self.player1,
            player2=self.player2,
            player1_name='Player One',
            player2_name='Player Two',
            status='finished',
            player1_score=3,
            player2_score=1,
            finished_at='2024-07-29 10:00:00'
        )
        self.game6 = Game.objects.create(
            id='game_id_6',
            player1=self.player1,
            player2=self.player3,
            player1_name='Player One',
            player2_name='Player Three',
            status='finished',
            player1_score=4,
            player2_score=3,
            finished_at='2024-07-28 16:00:00'
        )
        self.game7 = Game.objects.create(
            id='game_id_7',
            player1=self.player2,
            player2=self.player1,
            player1_name='Player Two',
            player2_name='Player One',
            status='finished',
            player1_score=2,
            player2_score=5,
            finished_at='2024-07-27 15:00:00'
        )
        self.game8 = Game.objects.create(
            id='game_id_8',
            player1=self.player1,
            player2=self.player2,
            player1_name='Player One',
            player2_name='Player Two',
            status='finished',
            player1_score=1,
            player2_score=2,
            finished_at='2024-07-26 11:00:00'
        )
        self.game9 = Game.objects.create(
            id='game_id_9',
            player1=self.player3,
            player2=self.player1,
            player1_name='Player Three',
            player2_name='Player One',
            status='waiting_for_players'
        )

        self.tournament1 = Tournament.objects.create(
            id='tournament_id_1',
            name='Tournament One',
            pool_size=8,
        )
        self.tournament1.players.add(self.player1, self.player2)

        self.tournament2 = Tournament.objects.create(
            id='tournament_id_2',
            name='Tournament Two',
            status='in_progress',
            pool_size=8,
        )
        self.tournament2.players.add(self.player1)

        self.tournament3 = Tournament.objects.create(
            id='tournament_id_3',
            name='Tournament Three',
            status='finished',
            pool_size=8,
        )
        self.tournament3.players.add(self.player2, self.player3)

        self.client = Client()

    def test_games_view_get(self):
        response = self.client.get(reverse('games'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('games', response.json())
        self.assertEqual(len(response.json()['games']), 9)

    @patch('matchmaker_app.views.games.Game.objects.all')
    def test_games_view_internal_server_error(self, mock_all):
        mock_all.side_effect = Exception('Simulated internal error')
        response = self.client.get(reverse('games'))
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json())

    @patch('matchmaker_app.utils.decorators.jwt_validate')
    def test_get_my_games_success(self, mock_validate):
        mock_validate.side_effect = lambda request: mock_jwt_validate(
            request, 'Player One'
        )

        response = self.client.get(reverse('my-games'))

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('games', response_data)
        self.assertEqual(len(response_data['games']), 9)
        self.assertEqual(response_data['games'][0]['id'], self.game1.id)
        self.assertEqual(response_data['games'][1]['id'], self.game2.id)

    @patch('matchmaker_app.utils.decorators.jwt_validate')
    def test_get_my_games_with_joined_filter(self, mock_validate):
        mock_validate.side_effect = lambda request: mock_jwt_validate(
            request, 'Player One'
        )
        response = self.client.get(
            reverse('my-games'), data={'joined': 'true'}
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('games', response_data)
        self.assertEqual(len(response_data['games']), 8)
        self.assertEqual(response_data['games'][0]['id'], self.game1.id)

    @patch('matchmaker_app.utils.decorators.jwt_validate')
    def test_get_my_games_with_status_filter(self, mock_validate):
        mock_validate.side_effect = lambda request: mock_jwt_validate(
            request, 'Player One'
        )
        response = self.client.get(
            reverse('my-games'), data={'status': 'waiting_for_players'}
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('games', response_data)
        self.assertEqual(len(response_data['games']), 2)
        self.assertEqual(response_data['games'][0]['id'], self.game1.id)
        self.assertEqual(response_data['games'][1]['id'], self.game9.id)

    def test_get_my_games_no_jwt(self):
        response = self.client.get(reverse('my-games'))

        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(
            response_data['error'], 'Invalid or missing JWT token'
        )

    def test_get_my_games_method_not_allowed(self):
        response = self.client.post(reverse('my-games'))

        self.assertEqual(response.status_code, 405)
        response_data = response.json()
        self.assertEqual(response_data['error'], 'Method not allowed')

    def test_game_detail_view_get(self):
        response = self.client.get(
            reverse('games-detail', args=['game_id_1'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.json())
        self.assertEqual(response.json()['id'], 'game_id_1')

    def test_game_detail_view_not_found(self):
        response = self.client.get(
            reverse('games-detail', args=['non_existent_id'])
        )
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json())

    def test_game_detail_view_method_not_allowed(self):
        response = self.client.post(
            reverse('games-detail', args=['game_id_1'])
        )
        self.assertEqual(response.status_code, 405)
        self.assertIn('error', response.json())

    @patch('matchmaker_app.utils.decorators.jwt_validate')
    def test_get_my_tournaments_no_status(self, mock_validate):
        """Test retrieving tournaments with no status filter."""

        mock_validate.side_effect = lambda request: mock_jwt_validate(
            request, 'Player One'
        )
        response = self.client.get(reverse('my-tournaments'))
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(len(response_data['tournaments']), 2)
        self.assertIn(
            'tournament_id_1', [t['id'] for t in response_data['tournaments']]
        )
        self.assertIn(
            'tournament_id_2', [t['id'] for t in response_data['tournaments']]
        )

    @patch('matchmaker_app.utils.decorators.jwt_validate')
    def test_get_my_tournaments_with_status(self, mock_validate):
        """Test retrieving tournaments with a status filter."""

        mock_validate.side_effect = lambda request: mock_jwt_validate(
            request, 'Player One'
        )
        response = self.client.get(
            reverse('my-tournaments') + '?status=in_progress'
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(len(response_data['tournaments']), 1)
        self.assertEqual(
            response_data['tournaments'][0]['id'], 'tournament_id_2'
        )

    @patch('matchmaker_app.utils.decorators.jwt_validate')
    def test_get_my_tournaments_player_filter(self, mock_validate):
        """Test retrieving tournaments where a specific player is involved."""

        mock_validate.side_effect = lambda request: mock_jwt_validate(
            request, 'Player One'
        )
        response = self.client.get(
            reverse('my-tournaments') + '?player=Player One'
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(len(response_data['tournaments']), 2)
        self.assertIn(
            'tournament_id_1', [t['id'] for t in response_data['tournaments']]
        )
        self.assertIn(
            'tournament_id_2', [t['id'] for t in response_data['tournaments']]
        )

    @patch('matchmaker_app.utils.decorators.jwt_validate')
    def test_get_my_tournaments_invalid_status(self, mock_validate):
        """Test retrieving tournaments with an invalid status filter."""

        mock_validate.side_effect = lambda request: mock_jwt_validate(
            request, 'Player One'
        )

        response = self.client.get(
            reverse('my-tournaments') + '?status=invalid_status'
        )
        self.assertEqual(response.status_code, 500)
        response_data = response.json()
        self.assertEqual(
            response_data['error'], 'An internal server error occurred'
        )

    def test_player_detail_view_patch_name(self):
        patch_data = json.dumps({'name': 'New Player One'})
        url = reverse('players-detail', kwargs={'player_name': 'Player One'})
        response = self.client.patch(
            url,
            data=patch_data,
            content_type='application/json',
            **{'HTTP_X_API_KEY': settings.MATCHMAKER_SERVICE_API_KEY}
        )

        self.assertEqual(response.status_code, 200)

        updated_player = Player.objects.get(name='New Player One')
        updated_game1 = Game.objects.get(id='game_id_1')
        updated_game2 = Game.objects.get(id='game_id_2')

        self.assertEqual(updated_player.name, 'New Player One')
        self.assertEqual(updated_game1.player1.name, 'New Player One')
        self.assertEqual(updated_game2.player1.name, 'New Player One')

    def test_player_stats_view_get(self):
        response = self.client.get(
            '/api/players/Player%20One/stats/',
            {
                'opponent': 'Player Two',
                'position': 'home',
                'status': 'finished',
                'limit': 3
            }
        )

        data = response.json()
        data = data['stats']

        self.assertEqual(response.status_code, 200)

        self.assertIn('win_rate', data)
        self.assertIn('total_wins', data)
        self.assertIn('total_losses', data)
        self.assertIn('goals_for', data)
        self.assertIn('goals_against', data)
        self.assertIn('games', data)

        self.assertEqual(data['total_wins'], 1)
        self.assertEqual(data['total_losses'], 1)
        self.assertEqual(data['win_rate'], 50)
        self.assertEqual(data['goals_for'], 4)
        self.assertEqual(data['goals_against'], 3)
        self.assertEqual(len(data['games']), 2)

        game_ids = [game['id'] for game in data['games']]
        self.assertIn('game_id_5', game_ids)
        self.assertIn('game_id_8', game_ids)

        for game in data['games']:
            if game['id'] == 'game_id_5':
                self.assertEqual(game['player1_name'], 'Player One')
                self.assertEqual(game['player2_name'], 'Player Two')
                self.assertEqual(game['player1_score'], 3)
                self.assertEqual(game['player2_score'], 1)
                self.assertEqual(game['winner_name'], 'Player One')
                self.assertEqual(game['date'], '2024-07-29T10:00:00Z')

            if game['id'] == 'game_id_8':
                self.assertEqual(game['player1_name'], 'Player One')
                self.assertEqual(game['player2_name'], 'Player Two')
                self.assertEqual(game['player1_score'], 1)
                self.assertEqual(game['player2_score'], 2)
                self.assertEqual(game['winner_name'], 'Player Two')
                self.assertEqual(game['date'], '2024-07-26T11:00:00Z')
