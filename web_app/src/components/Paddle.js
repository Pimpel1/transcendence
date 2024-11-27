export class Paddle {
    constructor(position, pitch) {
        this.position = position;
        this.pitch = pitch;
        this.x = 0;
        this.y = 0;
        this.width = 0;
        this.height = 0;
    }

    setCanvasSize(canvasWidth, canvasHeight) {
        this.canvasWidth = canvasWidth;
        this.canvasHeight = canvasHeight;
    }

    setPaddleSize() {
        this.width = 0.01 * this.canvasWidth;
        this.height = this.pitch.paddleToHeightRatio * this.canvasHeight;
        if (this.position === 'left') {
            this.offset = this.width;
        } else {
            this.offset = 0;
        }
    }

    update(pitchY) {
        const normalisedY = pitchY / this.pitch.height;
        this.y = normalisedY * this.canvasHeight;
    }

    rePosition(newCanvasWidth, newCanvasHeight) {
        this.y = this.y / this.canvasHeight * newCanvasHeight;
        if (this.position === 'left') {
            this.x = 0.125 * newCanvasWidth;
        } else {
            this.x = 0.875 * newCanvasWidth;
        }
    }

    resize(newCanvasWidth, newCanvasHeight) {
        this.rePosition(newCanvasWidth, newCanvasHeight);
        this.setCanvasSize(newCanvasWidth, newCanvasHeight);
        this.setPaddleSize();
    }

    draw(ctx) {
        ctx.fillStyle = 'white';
        ctx.fillRect(this.x - this.offset, this.y, this.width, this.height);
    }

    render(ctx, pitchY) {
        this.update(pitchY);
        this.draw(ctx);
    }

    cleanup() {
        this.x = 0;
        this.y = 0;
        this.width = 0;
        this.height = 0;
        this.canvasWidth = 0;
        this.canvasHeight = 0;
        this.offset = 0;
    }
}
