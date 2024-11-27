import { Canvas } from '../components/Canvas.js';
import { Paddle } from '../components/Paddle.js';
import { Ball } from '../components/Ball.js';
import { Midline } from '../components/Midline.js';
import { Score } from '../components/Score.js';
import { Pitch } from '../components/Pitch.js';
import { Overlay } from '../components/Overlay.js';

export class PongGame {
    constructor(canvasID) {
        this.canvas = new Canvas(canvasID);
        this.isInitialised = false;
        window.addEventListener('resize', () => this.resize());
    }

    reinit(canvasID) {
        this.canvas.init(canvasID);
        this.resize();
    }

    initialise(pitchWidth, pitchHeight, paddleSize, ballSize) {
        if (this.isInitialised) return;
        this.pitch = new Pitch(pitchWidth, pitchHeight, paddleSize, ballSize);
        // make canvas wider than pitch to create space behind paddles:
        this.canvas.aspectRatio = pitchWidth / (pitchHeight * 0.75);

        this.paddleLeft = new Paddle('left', this.pitch);
        this.paddleRight = new Paddle('right', this.pitch);
        this.ball = new Ball(this.pitch);
        this.midline = new Midline();
        this.scoreLeft = new Score('left');
        this.scoreRight = new Score('right');
        this.overlay = new Overlay();

        this.components = [
            this.paddleLeft,
            this.paddleRight,
            this.ball,
            this.midline,
            this.scoreLeft,
            this.scoreRight,
            this.overlay
        ];
        this.isInitialised = true;
        this.resize();
    }

    resizeComponents() {
        for (const component of this.components) {
            component.resize(this.canvas.id.width, this.canvas.id.height);
        }
    }

    resize() {
        this.canvas.resize();
        if (this.isInitialised)
            this.resizeComponents();
    }

    updateComponents(
        paddleLeftY,
        paddleRightY,
        ballX,
        ballY,
        scoreLeft,
        scoreRight
    ) {
        this.paddleLeft.update(paddleLeftY);
        this.paddleRight.update(paddleRightY);
        this.ball.update(ballX, ballY);
        this.scoreLeft.update(scoreLeft);
        this.scoreRight.update(scoreRight);
    }

    draw() {
        this.canvas.clear();
        this.canvas.fill('black');

        const ctx = this.canvas.ctx;
        for (const component of this.components) {
            component.draw(ctx);
        }
    }

    endGameOverlay(status) {
        const ctx = this.canvas.ctx;
        const words = status.split('_');
        for (let i = 0; i < words.length; i++) {
            words[i] = words[i][0].toUpperCase() + words[i].substr(1);
        }
        let message = words.join(" ");
        this.overlay.render(ctx, message);
    }

    render(
        paddleLeftY,
        paddleRightY,
        ballX,
        ballY,
        scoreLeft,
        scoreRight
    ) {
        this.updateComponents(
            paddleLeftY,
            paddleRightY,
            ballX,
            ballY,
            scoreLeft,
            scoreRight
        );
        this.draw();
    }

    clear() {
        this.canvas.clear();
    }

    cleanup() {
        window.removeEventListener('resize', this.resizeListener);

        if (this.canvas) {
            this.canvas.clear();
            this.canvas = null;
        }

        if (this.components) {
            this.components.forEach(component => {
                if (component.cleanup) component.cleanup();
            });
            this.components = [];
        }

        this.pitch = null;
        this.paddleLeft = null;
        this.paddleRight = null;
        this.ball = null;
        this.midline = null;
        this.scoreLeft = null;
        this.scoreRight = null;
        this.overlay = null;
        this.isInitialised = false;
    }
}
