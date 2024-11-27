export class Ball {
    constructor(pitch) {
        this.pitch = pitch;
        this.x = 0;
        this.y = 0;
        this.size = 0;
    }

    setCanvasSize(canvasWidth, canvasHeight) {
        this.canvasWidth = canvasWidth;
        this.canvasHeight = canvasHeight;
    }

    setBallSize() {
        this.size = this.pitch.ballToHeightRatio * this.canvasHeight;
    }

    update(pitchX, pitchY) {
        const normalisedX = pitchX / this.pitch.width;
        const widthFactor = 0.75 * this.canvasWidth; // pitch < canvas
        const offset = 0.125 * this.canvasWidth; // space behind paddles
        this.x = normalisedX * widthFactor + offset;
        const normalisedY = pitchY / this.pitch.height;
        this.y = normalisedY * this.canvasHeight;
    }

    rePosition(newCanvasWidth, newCanvasHeight) {
        this.x = this.x / this.canvasWidth * newCanvasWidth;
        this.y = this.y / this.canvasHeight * newCanvasHeight;
    }

    resize(newCanvasWidth, newCanvasHeight) {
        this.rePosition(newCanvasWidth, newCanvasHeight);
        this.setCanvasSize(newCanvasWidth, newCanvasHeight);
        this.setBallSize();
    }

    draw(ctx) {
        ctx.fillStyle = 'white';
        ctx.fillRect(this.x, this.y, this.size, this.size);
    }

    render(ctx, pitchX, pitchY) {
        this.update(pitchX, pitchY);
        this.draw(ctx);
    }


    cleanup() {
        this.pitch = null;
        this.canvasWidth = null;
        this.canvasHeight = null;
        this.size = null;
        this.x = null;
        this.y = null;
    }
}
