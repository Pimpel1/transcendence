import time
import logging
import random
import string

from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone


logger = logging.getLogger('matchmaker-service')


def generate_random_string():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(32))


class Player(models.Model):
    name = models.CharField(max_length=100, unique=True)
    channel_name = models.CharField(max_length=255, null=True, blank=True)
    message_queue = models.JSONField(default=list, null=True, blank=True)

    def __str__(self):
        return self.name

    def channel(self):
        return self.channel_name

    def add_message(self, message):
        try:
            with transaction.atomic():
                player = Player.objects.get(pk=self.pk)
                player.message_queue.append(message)
                player.save()
        except Exception as e:
            logger.warning(
                f'Error adding message for player {self.name} [{e}]'
            )
            raise

    def flush_messages(self):
        try:
            with transaction.atomic():
                player = Player.objects.get(pk=self.pk)
                messages = player.message_queue
                player.message_queue = []
                player.save()
            return messages
        except Exception as e:
            logger.warning(
                f'Error flushing messages for player {self.name} [{e}]'
            )
            raise

    def to_dict(self):
        return {
            'name': self.name,
            'connected': self.channel_name is not None,
            'total_games': self.total_games(),
            'total_wins': self.total_wins(),
            'total_losses': self.total_losses(),
            'win_rate': self.win_rate(),
            '# queued messages': len(self.message_queue)
        }

    def is_connected(self):
        return self.channel_name is not None

    def total_games(self):
        finished_games_as_player1 = self.games_as_player1.filter(
            status=Game.FINISHED
        ).count()
        finished_games_as_player2 = self.games_as_player2.filter(
            status=Game.FINISHED
        ).count()
        return finished_games_as_player1 + finished_games_as_player2

    def total_wins(self):
        wins_as_player1 = self.games_as_player1.filter(
            models.Q(status=Game.FINISHED) &
            models.Q(player1_score__gt=models.F('player2_score'))
        ).count()
        wins_as_player2 = self.games_as_player2.filter(
            models.Q(status=Game.FINISHED) &
            models.Q(player2_score__gt=models.F('player1_score'))
        ).count()
        return wins_as_player1 + wins_as_player2

    def total_losses(self):
        return self.total_games() - self.total_wins()

    def win_rate(self):
        total_games = self.total_games()
        return f"{int((self.total_wins() / total_games) * 100)}%" \
            if total_games > 0 else "0%"

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.warning(f'Issue saving player {self.name} [{e}]')
            raise


class Tournament(models.Model):
    ONLINE = 'online'
    LOCAL = 'local'

    TOURNAMENT_TYPES = [
        (ONLINE, 'Online'),
        (LOCAL, 'Local')
    ]

    WAITING_FOR_PLAYERS = 'waiting_for_players'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'

    TOURNAMENT_STATUSES = [
        (WAITING_FOR_PLAYERS, 'Waiting for Players'),
        (IN_PROGRESS, 'In Progress'),
        (FINISHED, 'Finished'),
    ]

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=generate_random_string,
        editable=False,
        unique=True
    )

    type = models.CharField(
        max_length=10,
        choices=TOURNAMENT_TYPES,
        default=ONLINE
    )

    name = models.CharField(max_length=100)

    players = models.ManyToManyField(
        Player,
        related_name='tournaments',
        blank=True
    )

    player_names = models.JSONField(default=list, null=True, blank=True)
    pool_size = models.IntegerField()

    status = models.CharField(
        choices=TOURNAMENT_STATUSES,
        default=WAITING_FOR_PLAYERS
    )

    current_round_number = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def to_dict(self):
        rounds = Round.objects.filter(
            tournament=self
        ).order_by('round_number')
        return {
            'name': self.name,
            'id': self.id,
            'type': self.type,
            'pool_size': self.pool_size,
            'players': self.player_names,
            'status': self.status,
            'current_round': (
                self.get_current_round().round_number
                if self.get_current_round()
                else None
            ),
            'winner': self.get_winner(),
            'ranking': self.get_ranking(),
            'leaderboard': self.get_leaderboard(),
            'games': [
                {
                    'round': round.round_number,
                    'games': [
                        game.to_dict()
                        for game in Game.objects.filter(round=round)
                    ]
                }
                for round in rounds
            ]
        }

    def get_current_round(self):
        return Round.objects.filter(
            tournament=self,
            round_number=self.current_round_number
        ).first() if Round.objects.filter(tournament=self).exists() else None

    def get_winner(self):
        if self.status != self.FINISHED:
            return None
        else:
            ranking = self.get_ranking()
            return ranking[0] if ranking else None

    def _get_leaderboard_entries(self):
        return LeaderboardEntry.objects.filter(tournament=self).order_by(
            '-points', '-games_won', '-goal_difference', '-goals_for', '?'
        )

    def get_leaderboard(self):
        return [
            entry.to_dict()
            for entry in self._get_leaderboard_entries()
        ]

    def get_ranking(self):
        return [
            entry.player_name
            for entry in self._get_leaderboard_entries()
        ]


class Round(models.Model):
    ONLINE = 'online'
    LOCAL = 'local'

    ROUND_TYPES = [
        (ONLINE, 'Online'),
        (LOCAL, 'Local')
    ]

    tournament = models.ForeignKey(
        Tournament,
        related_name='rounds',
        on_delete=models.CASCADE
    )
    round_number = models.IntegerField()
    type = models.CharField(
        max_length=10,
        choices=ROUND_TYPES,
        default=ONLINE
    )

    class Meta:
        unique_together = ['tournament', 'round_number']

    def __str__(self):
        return f'{self.tournament.name} - Round {self.round_number}'

    def to_dict(self):
        return {
            'tournament': self.tournament.name,
            'type': self.type,
            'round_number': self.round_number,
            'games': [game.id for game in self.games.all()]
        }


class LeaderboardEntry(models.Model):
    player_name = models.CharField(max_length=100)

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE
    )

    games_played = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)
    goals_for = models.IntegerField(default=0)
    goals_against = models.IntegerField(default=0)
    goal_difference = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        self.goal_difference = self.goals_for - self.goals_against
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.player_name} - {self.tournament.name}'

    def to_dict(self):
        return {
            'player_name': self.player_name,
            'games_played': self.games_played,
            'games_won': self.games_won,
            'goals_for': self.goals_for,
            'goals_against': self.goals_against,
            'goal_difference': self.goals_for - self.goals_against,
            'points': self.points
        }


class Game(models.Model):
    ONLINE = 'online'
    LOCAL = 'local'

    GAME_TYPES = [
        (ONLINE, 'Online'),
        (LOCAL, 'Local')
    ]

    WAITING_FOR_PLAYERS = 'waiting_for_players'
    SCHEDULED = 'scheduled'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'

    GAME_STATUSES = [
        (WAITING_FOR_PLAYERS, 'Waiting for Players'),
        (SCHEDULED, 'Scheduled'),
        (IN_PROGRESS, 'In Progress'),
        (FINISHED, 'Finished'),
    ]

    id = models.CharField(
        primary_key=True,
        max_length=32,
        default=generate_random_string,
        editable=False,
        unique=True
    )

    type = models.CharField(
        max_length=10,
        choices=GAME_TYPES,
        default=ONLINE
    )

    player1 = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='games_as_player1',
        null=True,
        blank=True
    )

    player2 = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='games_as_player2',
        null=True,
        blank=True
    )

    player1_name = models.CharField(max_length=100, null=True, blank=True)
    player2_name = models.CharField(max_length=100, null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=GAME_STATUSES,
        default=WAITING_FOR_PLAYERS
    )

    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    tournament = models.ForeignKey(
        Tournament,
        related_name='games',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    round = models.ForeignKey(
        Round,
        related_name='games',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    player1_position = models.CharField(max_length=10, default='left')
    player2_position = models.CharField(max_length=10, default='right')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finished_at = models.DateTimeField(null=True, blank=True, default=None)

    def __str__(self):
        return self.id

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.get_name(),
            'type': self.type,
            'status': self.status,
            'Tournament': self.tournament.name if self.tournament else None,
            'round': self.round.round_number if self.round else None,
            'player1': self.player1_name,
            'player2': self.player2_name,
            'player1_position': self.player1_position,
            'player2_position': self.player2_position,
            'player1_score': self.player1_score,
            'player2_score': self.player2_score,
            'date': str(self.created_at),
            'created_at': int(time.mktime(self.created_at.timetuple())),
            'winner': self.get_winner()
        }

    def get_winner(self):
        if self.status != self.FINISHED:
            return None
        if self.player1_score > self.player2_score:
            return self.player1_name
        elif self.player2_score > self.player1_score:
            return self.player2_name
        else:
            return None

    def get_player_position(self, player_name):
        if player_name == self.player1_name:
            return self.player1_position
        else:  # player2
            return self.player2_position

    def get_score(self, player_name):
        if player_name == self.player1_name:
            return self.player1_score
        else:
            return self.player2_score

    def get_opponent(self, player_name):
        if player_name == self.player1_name:
            return self.player2_name
        else:
            return self.player1_name

    def get_name(self):
        return f'{self.player1_name} vs {self.player2_name}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['player1', 'player2'],
                condition=Q(status='waiting_for_players'),
                name='unique_private_waiting_game'
            ),
            models.UniqueConstraint(
                fields=['status', 'player2'],
                condition=Q(
                    status='waiting_for_players', player2__isnull=True
                ),
                name='unique_open_waiting_game'
            ),
            models.CheckConstraint(
                check=~Q(player1=models.F('player2')),
                name='player1_not_equal_to_player2'
            )
        ]

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.warning(f'Issue saving game {self.id} [{e}]')
            raise


class Lock(models.Model):
    name = models.CharField(max_length=255, unique=True)
    acquired_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name
