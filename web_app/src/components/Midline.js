export class Midline{
    constructor(){
        this.x = 0;
        this.y = 0;
        this.width = 0;
        this.height = 0;
    }

    setCanvasSize(canvasWidth, canvasHeight){
        this.canvasWidth = canvasWidth;
        this.canvasHeight = canvasHeight;
    }

    setMidlineSize(){
        this.width = 0.002 * this.canvasWidth;
        if (this.width < 1){
            this.width = 1;
        }
        this.height = this.canvasHeight * 0.9;
        this.offset = this.width / 2;
    }

    rePosition(newCanvasWidth, newCanvasHeight){
        this.x = newCanvasWidth / 2;
        this.y = newCanvasHeight * 0.05;
    }

    resize(newCanvasWidth, newCanvasHeight){
        this.rePosition(newCanvasWidth, newCanvasHeight);
        this.setCanvasSize(newCanvasWidth, newCanvasHeight);
        this.setMidlineSize();
    }

    draw(ctx) {
        ctx.beginPath();
        ctx.strokeStyle = 'white';
        ctx.setLineDash([10, 10]);
        ctx.lineWidth = this.width;
        ctx.moveTo(this.x, this.y - this.offset);
        ctx.lineTo(this.x, this.y - this.offset + this.height);
        ctx.stroke();
    }

    render(ctx){
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
