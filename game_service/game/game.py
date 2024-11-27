import math
import random
import time


class Rectangle:
    def __init__(self, left, top, width, height):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.compute_rectangle()

    def compute_rectangle(self):
        self.right = self.left + self.width - 1
        self.bottom = self.top + self.height - 1

    def move_of(self, d_x, d_y):
        self.left += d_x
        self.top += d_y
        self.compute_rectangle()

    def move_at(self, x, y):
        self.left = x
        self.top = y
        self.compute_rectangle()

    def center_at(self, x, y):
        self.left = x - (self.width / 2)
        self.top = y - (self.height / 2)
        self.compute_rectangle()

    def get_center_x(self):
        return self.right - (self.width / 2)

    def get_center_y(self):
        return self.bottom - (self.height / 2)


class MovingRectangle(Rectangle):
    def __init__(
        self,
        left,
        top,
        width,
        height,
        px_per_sec,
        angle,
        accelerate_factor_per_sec=None,
        px_per_sec_max=None
    ):
        super().__init__(left, top, width, height)
        self.px_per_sec = px_per_sec
        self.px_per_sec_orig = px_per_sec
        self.px_per_sec_max = px_per_sec_max
        if not self.px_per_sec_max:
            self.px_per_sec_max = px_per_sec
        self.accelerate_factor_per_sec = accelerate_factor_per_sec
        self.angle = angle

    def update_position(self, elapsed_time):
        if self.accelerate_factor_per_sec:
            acceleration = self.accelerate_factor_per_sec * elapsed_time
            self.px_per_sec = self.px_per_sec + acceleration
            if self.px_per_sec > self.px_per_sec_max:
                self.px_per_sec = self.px_per_sec_max

        self.move_of(
            (math.cos(math.radians(self.angle))
                * self.px_per_sec * elapsed_time),
            (math.sin(math.radians(self.angle))
                * self.px_per_sec * elapsed_time)
        )

    def reset(self):
        self.px_per_sec = self.px_per_sec_orig


class Paddle(MovingRectangle):
    def __init__(self, height, right_sided, speed, amplitude, pitch):
        super().__init__(0, 0, 1, height, 0, 90)
        self.right_sided = right_sided
        self.amplitude = amplitude
        self.speed = speed
        self.center_at(
            (pitch.left - self.width if not self.right_sided
                else pitch.right + 1),
            pitch.get_center_y()
        )

    def update_position(self, elapsed_time, pitch):
        super().update_position(elapsed_time)
        if self.top < 0:
            self.move_at(self.left, 0)
        if self.bottom > pitch.height:
            self.move_at(self.left, pitch.height - self.height)

    def set_move_down(self):
        self.px_per_sec = self.speed
        self.angle = 90

    def set_move_up(self):
        self.px_per_sec = self.speed
        self.angle = 270

    def set_move_down_off(self):
        if self.angle == 90:
            self.px_per_sec = 0

    def set_move_up_off(self):
        if self.angle == 270:
            self.px_per_sec = 0


class Ball(MovingRectangle):
    def __init__(
        self,
        pitch,
        size,
        px_per_sec,
        start_amplitude,
        accelerate_factor_per_sec=None,
        px_per_sec_max=None
    ):
        super().__init__(
            0,
            0,
            size,
            size,
            px_per_sec,
            0,
            accelerate_factor_per_sec,
            px_per_sec_max
        )
        self.start_amplitude = start_amplitude
        self.engage_left = random.choice([True, False])
        self.reset(pitch)

    def update_position(self, elapsed_time, pitch):
        super().update_position(elapsed_time)
        if self.top < pitch.top:
            self.move_at(self.left, pitch.top)
        if self.bottom > pitch.bottom:
            self.move_at(self.left, pitch.height - self.height)
        if self.left < pitch.left:
            self.move_at(pitch.left, self.top)
        if self.right > pitch.right:
            self.move_at(pitch.width - self.width, self.top)

    def reset(self, pitch):
        super().reset()
        self.center_at(pitch.get_center_x(), pitch.get_center_y())
        self.engage_left = not self.engage_left
        self.angle = random.randint(
            -self.start_amplitude,
            self.start_amplitude
        )
        if self.engage_left:
            self.angle = (180 - self.angle) % 360

    def handle_wall_collisions(self, pitch):
        if self.top == pitch.top or self.bottom == pitch.bottom:
            self.angle = (360 - self.angle) % 360

    def handle_paddle_collision(self, paddle):
        size = self.height + paddle.height + 1
        distance = (self.get_center_y() - paddle.get_center_y())
        angle = (distance / (size / 2) * paddle.amplitude)
        if paddle.right_sided:
            angle = 180 - angle
        self.angle = angle % 360


class Player:
    def __init__(
        self,
        side,
        pitch,
        paddle_size,
        paddle_speed,
        paddle_amplitude
    ):
        self.score = 0
        self.side = side
        self.paddle = Paddle(
            paddle_size,
            False if self.side == 'left' else True,
            paddle_speed,
            paddle_amplitude,
            pitch
        )
        self.goal = Rectangle(
            pitch.left - 1 if self.side == 'left' else pitch.right + 1,
            pitch.top,
            1,
            pitch.height
        )

    def check_goal(self, ball, pitch, opponent):
        if (
            (self.side == 'left' and ball.left == pitch.left) or
            (self.side == 'right' and ball.right == pitch.right)
        ):
            if (
                ball.top <= self.paddle.bottom + 1 and
                ball.bottom >= self.paddle.top - 1
            ):
                ball.handle_paddle_collision(self.paddle)
            else:
                opponent.score += 1
                ball.reset(pitch)
                return True
        return False


class Chrono:
    def __init__(self):
        self.start_time = time.time()

    def get_time(self):
        return time.time() - self.start_time

    def reinit(self):
        self.start_time = time.time()


class GameLogic:

    def __init__(
        self,
        pitch_width,
        pitch_height,
        ball_size,
        ball_speed,
        start_amplitude,
        paddle_size,
        paddle_speed,
        paddle_amplitude,
        pause_duration,
        max_points,
        accelerator,
        max_acceleration
    ):
        self.finished = False
        self.paused = False
        self.pause_duration = pause_duration
        self.max_points = max_points
        self.pitch = Rectangle(0, 0, pitch_width, pitch_height)
        self.ball = Ball(
            self.pitch,
            ball_size,
            ball_speed,
            start_amplitude,
            accelerator,
            max_acceleration
        )
        self.player = {
            'left': Player(
                'left',
                self.pitch,
                paddle_size,
                paddle_speed,
                paddle_amplitude
            ),
            'right': Player(
                'right',
                self.pitch,
                paddle_size,
                paddle_speed,
                paddle_amplitude
            )
        }

    def start(self):
        self.chrono = Chrono()
        self.last_update = self.chrono.get_time()
        self.trigger_pause()

    def update(self):
        current_time = self.chrono.get_time()
        elapsed_time = current_time - self.last_update
        self.last_update = current_time

        self.check_finish()
        if not self.finished:
            for side in ['left', 'right']:
                self.player[side].paddle.update_position(
                    elapsed_time,
                    self.pitch
                )
            self.check_pause()
            if not self.paused:
                self.ball.update_position(elapsed_time, self.pitch)
                self.handle_collisions()

    def handle_collisions(self):
        self.ball.handle_wall_collisions(self.pitch)
        if (
            self.player['left'].check_goal(
                self.ball,
                self.pitch,
                self.player['right']
            ) or
            self.player['right'].check_goal(
                self.ball,
                self.pitch,
                self.player['left']
            )
        ):
            self.trigger_pause()

    def trigger_move(self, side, move):
        if side not in {'left', 'right'}:
            return
        paddle = self.player[side].paddle
        move_actions = {
            'up': paddle.set_move_up,
            'down': paddle.set_move_down,
            'up_off': paddle.set_move_up_off,
            'down_off': paddle.set_move_down_off
        }
        if move in move_actions:
            move_actions[move]()

    def trigger_pause(self):
        self.pause_start = self.chrono.get_time()
        self.paused = True

    def check_pause(self):
        if (
            self.paused and
            self.chrono.get_time() - self.pause_start >= self.pause_duration
        ):
            self.paused = False

    def check_finish(self):
        for side, player in self.player.items():
            if player.score == self.max_points:
                self.finished = True
