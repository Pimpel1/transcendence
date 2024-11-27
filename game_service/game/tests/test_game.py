from django.test import SimpleTestCase
from game.game import Game


class GameTests(SimpleTestCase):
    """Test game logic"""

    PITCH_WIDTH = 480		# Pixels
    PITCH_HEIGHT = 360		# Pixels
    BALL_SIZE = 5           # Pixels
    BALL_MOVES = 200        # Pixels per second
    START_AMPLITUDE = 60    # Degrees
    PADDLE_SIZE = 60        # Pixels
    PADDLE_MOVES = 300      # Pixels per second
    PADDLE_AMPLITUDE = 60   # Degrees
    PAUSE_TIME = 1.5        # Seconds
    UPDATE_TIME = 0.03      # Seconds

    def setUp(self):
        self.game = Game(
            self.PITCH_WIDTH,
            self.PITCH_HEIGHT,
            self.BALL_SIZE,
            self.BALL_MOVES,
            self.START_AMPLITUDE,
            self.PADDLE_SIZE,
            self.PADDLE_MOVES,
            self.PADDLE_AMPLITUDE,
            self.PAUSE_TIME
        )

    def test_handle_wall_collision(self):
        self.game.ball.move_at(self.game.pitch.left, self.game.pitch.top)
        self.game.ball.angle = 200
        self.game.ball.handle_wall_collisions(self.game.pitch)
        self.assertEqual(self.game.ball.angle, 160)
        self.game.ball.move_at(
            self.game.pitch.get_center_x(),
            self.game.pitch.bottom - (self.game.ball.height - 1)
        )
        self.game.ball.angle = 30
        self.game.ball.handle_wall_collisions(self.game.pitch)
        self.assertEqual(self.game.ball.angle, 330)

    def test_handle_paddle_collision(self):
        self.game.ball.move_at(self.game.pitch.left, self.game.pitch.top)
        self.game.player['left'].paddle.move_at(
            self.game.player['left'].paddle.left,
            self.game.pitch.top
        )
        self.game.ball.handle_paddle_collision(self.game.player['left'].paddle)
        self.assertEqual(self.game.ball.angle, (-27.5 * 60 / 33) % 360)
