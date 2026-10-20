// Moving watermark drawn on a canvas over the video: the member's email and member ID, semi-transparent,
// jumping to a random spot every 20 to 40 seconds. If someone deletes or hides it (for example with the
// browser's developer tools) it is put back; if it keeps disappearing, onGiveUp is called to pause playback.

const MIN_MOVE_MS = 20000;
const MAX_MOVE_MS = 40000;
const CHECK_MS = 2000;
const MAX_RESTORES = 3;
const RESTORE_WINDOW_MS = 10000;

const randomBetween = (a, b) => a + Math.random() * (b - a);

export default class Watermark {
    constructor(container, text, onGiveUp) {
        this.container = container;
        this.text = text;
        this.onGiveUp = onGiveUp;
        this.canvas = null;
        this.position = null;
        this.restores = [];
        this.stopped = false;
    }

    start() {
        this.create();
        this.observer = new MutationObserver(() => this.check());
        this.observer.observe(this.container, {
            childList: true, subtree: true, attributes: true, attributeFilter: ["style", "class", "hidden", "width", "height"]
        });
        this.resizeObserver = new ResizeObserver(() => this.draw(false));
        this.resizeObserver.observe(this.container);
        // Style changes made elsewhere (a stylesheet in <head>) do not trigger the observer, so also check regularly
        this.checkTimer = setInterval(() => this.check(), CHECK_MS);
        this.scheduleMove();
    }

    stop() {
        this.stopped = true;
        clearTimeout(this.moveTimer);
        clearInterval(this.checkTimer);
        if (this.observer) this.observer.disconnect();
        if (this.resizeObserver) this.resizeObserver.disconnect();
        if (this.canvas) this.canvas.remove();
        this.canvas = null;
    }

    create() {
        const canvas = document.createElement("canvas");
        canvas.setAttribute("aria-hidden", "true");
        canvas.className = "tcc-watermark";
        // Inline styles so a missing stylesheet cannot hide it
        canvas.style.cssText = "position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:6;display:block;visibility:visible;opacity:1;";
        this.canvas = canvas;
        this.container.appendChild(canvas);
        this.draw(this.position === null);
    }

    isHidden() {
        const c = this.canvas;
        if (!c || !this.container.contains(c)) return true;
        const style = window.getComputedStyle(c);
        return style.display === "none" || style.visibility !== "visible" || parseFloat(style.opacity) < 0.9
            || c.offsetWidth < 10 || c.offsetHeight < 10;
    }

    check() {
        if (this.stopped || !this.isHidden()) return;
        const now = Date.now();
        this.restores = this.restores.filter(t => now - t < RESTORE_WINDOW_MS);
        this.restores.push(now);
        if (this.observer) this.observer.disconnect();
        if (this.canvas) this.canvas.remove();
        this.create();
        if (this.observer) {
            this.observer.observe(this.container, {
                childList: true, subtree: true, attributes: true, attributeFilter: ["style", "class", "hidden", "width", "height"]
            });
        }
        if (this.restores.length > MAX_RESTORES || this.isHidden()) {
            this.onGiveUp();
        }
    }

    scheduleMove() {
        this.moveTimer = setTimeout(() => {
            if (this.stopped) return;
            this.draw(true);
            this.scheduleMove();
        }, randomBetween(MIN_MOVE_MS, MAX_MOVE_MS));
    }

    draw(newPosition) {
        const c = this.canvas;
        if (!c) return;
        const ratio = window.devicePixelRatio || 1;
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        if (!width || !height) return;
        c.width = Math.round(width * ratio);
        c.height = Math.round(height * ratio);
        const ctx = c.getContext("2d");
        ctx.scale(ratio, ratio);
        const fontSize = Math.max(13, Math.min(26, width / 36));
        ctx.font = `600 ${fontSize}px sans-serif`;
        const textWidth = ctx.measureText(this.text).width;
        if (newPosition || !this.position) {
            this.position = { x: Math.random(), y: Math.random() };
        }
        const x = 10 + this.position.x * Math.max(0, width - textWidth - 20);
        const y = fontSize + 10 + this.position.y * Math.max(0, height - fontSize - 30);
        ctx.lineWidth = 3;
        ctx.strokeStyle = "rgba(0, 0, 0, 0.35)";
        ctx.fillStyle = "rgba(255, 255, 255, 0.45)";
        ctx.strokeText(this.text, x, y);
        ctx.fillText(this.text, x, y);
    }
}
