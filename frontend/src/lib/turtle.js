export class Turtle {
  constructor(canvas, indicatorElement = null) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.indicatorElement = indicatorElement;

    this.x = canvas.width / 2;
    this.y = canvas.height / 2;
    this.heading = 0;
    this.penDown = true;
    this.penColor = '#000000';
    this.penWidth = 2;
    this.speed = 5;
    this.visible = true;
    this.fillColor = '#000000';
    this.filling = false;
    this.fillPath = [];

    this.clear();
  }

  forward(distance) {
    const rad = this.heading * Math.PI / 180;
    const newX = this.x + distance * Math.cos(rad);
    const newY = this.y - distance * Math.sin(rad);

    if (this.penDown) {
      this.ctx.beginPath();
      this.ctx.moveTo(this.x, this.y);
      this.ctx.lineTo(newX, newY);
      this.ctx.strokeStyle = this.penColor;
      this.ctx.lineWidth = this.penWidth;
      this.ctx.lineCap = 'round';
      this.ctx.stroke();
    }

    if (this.filling) this.fillPath.push({ x: newX, y: newY });

    this.x = newX;
    this.y = newY;
    this._updateIndicator();
    return `Moved forward ${distance} pixels`;
  }

  fd(distance) { return this.forward(distance); }
  backward(distance) { return this.forward(-distance); }
  bk(distance) { return this.backward(distance); }
  back(distance) { return this.backward(distance); }

  right(angle) {
    this.heading = (this.heading - angle) % 360;
    this._updateIndicator();
    return `Turned right ${angle} degrees`;
  }

  rt(angle) { return this.right(angle); }

  left(angle) {
    this.heading = (this.heading + angle) % 360;
    this._updateIndicator();
    return `Turned left ${angle} degrees`;
  }

  lt(angle) { return this.left(angle); }

  goto(x, y) {
    if (y === undefined && Array.isArray(x)) { y = x[1]; x = x[0]; }

    const canvasX = this.canvas.width / 2 + x;
    const canvasY = this.canvas.height / 2 - y;

    if (this.penDown) {
      this.ctx.beginPath();
      this.ctx.moveTo(this.x, this.y);
      this.ctx.lineTo(canvasX, canvasY);
      this.ctx.strokeStyle = this.penColor;
      this.ctx.lineWidth = this.penWidth;
      this.ctx.lineCap = 'round';
      this.ctx.stroke();
    }

    if (this.filling) this.fillPath.push({ x: canvasX, y: canvasY });

    this.x = canvasX;
    this.y = canvasY;
    this._updateIndicator();
    return `Moved to (${x}, ${y})`;
  }

  setpos(x, y) { return this.goto(x, y); }
  setposition(x, y) { return this.goto(x, y); }

  setx(x) {
    const canvasX = this.canvas.width / 2 + x;
    if (this.penDown) {
      this.ctx.beginPath();
      this.ctx.moveTo(this.x, this.y);
      this.ctx.lineTo(canvasX, this.y);
      this.ctx.strokeStyle = this.penColor;
      this.ctx.lineWidth = this.penWidth;
      this.ctx.stroke();
    }
    this.x = canvasX;
    this._updateIndicator();
    return `Set x to ${x}`;
  }

  sety(y) {
    const canvasY = this.canvas.height / 2 - y;
    if (this.penDown) {
      this.ctx.beginPath();
      this.ctx.moveTo(this.x, this.y);
      this.ctx.lineTo(this.x, canvasY);
      this.ctx.strokeStyle = this.penColor;
      this.ctx.lineWidth = this.penWidth;
      this.ctx.stroke();
    }
    this.y = canvasY;
    this._updateIndicator();
    return `Set y to ${y}`;
  }

  setheading(angle) {
    this.heading = angle;
    this._updateIndicator();
    return `Heading set to ${angle} degrees`;
  }

  seth(angle) { return this.setheading(angle); }

  home() {
    this.goto(0, 0);
    this.setheading(0);
    return 'Returned home';
  }

  position() {
    const x = Math.round(this.x - this.canvas.width / 2);
    const y = Math.round(this.canvas.height / 2 - this.y);
    return `Position: (${x}, ${y})`;
  }

  pos() { return this.position(); }
  xcor() { return Math.round(this.x - this.canvas.width / 2); }
  ycor() { return Math.round(this.canvas.height / 2 - this.y); }
  getHeading() { return this.heading; }
  isdown() { return this.penDown; }
  isFilling() { return this.filling; }

  distance(x, y) {
    if (y === undefined && Array.isArray(x)) { y = x[1]; x = x[0]; }
    const canvasX = this.canvas.width / 2 + x;
    const canvasY = this.canvas.height / 2 - y;
    const dx = canvasX - this.x;
    const dy = canvasY - this.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  towards(x, y) {
    if (y === undefined && Array.isArray(x)) { y = x[1]; x = x[0]; }
    const canvasX = this.canvas.width / 2 + x;
    const canvasY = this.canvas.height / 2 - y;
    const dx = canvasX - this.x;
    const dy = -(canvasY - this.y);
    return Math.atan2(dy, dx) * 180 / Math.PI;
  }

  write(text, move = false, align = 'left', font = '12px Arial') {
    this.ctx.font = font;
    this.ctx.fillStyle = this.penColor;
    this.ctx.textAlign = align;
    this.ctx.fillText(String(text), this.x, this.y);
    return `Wrote: ${text}`;
  }

  undo() { return 'Undo not implemented'; }

  penup() { this.penDown = false; return 'Pen up'; }
  pu() { return this.penup(); }
  up() { return this.penup(); }

  pendown() { this.penDown = true; return 'Pen down'; }
  pd() { return this.pendown(); }
  down() { return this.pendown(); }

  pensize(width) {
    if (width !== undefined) { this.penWidth = width; return `Pen size set to ${width}`; }
    return `Pen size: ${this.penWidth}`;
  }

  width(w) { return this.pensize(w); }

  pencolor(color) {
    if (color !== undefined) { this.penColor = color; return `Pen color set to ${color}`; }
    return `Pen color: ${this.penColor}`;
  }

  color(pencolor, fillcolor) {
    if (pencolor !== undefined) {
      this.penColor = pencolor;
      if (fillcolor !== undefined) {
        this.fillColor = fillcolor;
        return `Pen: ${pencolor}, Fill: ${fillcolor}`;
      }
      return `Color set to ${pencolor}`;
    }
    return `Pen: ${this.penColor}, Fill: ${this.fillColor}`;
  }

  fillcolor(color) {
    if (color !== undefined) { this.fillColor = color; return `Fill color set to ${color}`; }
    return `Fill color: ${this.fillColor}`;
  }

  begin_fill() {
    this.filling = true;
    this.fillPath = [{ x: this.x, y: this.y }];
    return 'Begin fill';
  }

  end_fill() {
    if (this.filling && this.fillPath.length > 2) {
      this.ctx.beginPath();
      this.ctx.moveTo(this.fillPath[0].x, this.fillPath[0].y);
      for (let i = 1; i < this.fillPath.length; i++) {
        this.ctx.lineTo(this.fillPath[i].x, this.fillPath[i].y);
      }
      this.ctx.closePath();
      this.ctx.fillStyle = this.fillColor;
      this.ctx.fill();
    }
    this.filling = false;
    this.fillPath = [];
    return 'End fill';
  }

  circle(radius, extent = 360, steps = null) {
    if (steps === null) steps = Math.max(Math.abs(Math.round(extent / 5)), 1);

    const stepAngle = extent / steps;
    const stepLength = 2 * Math.PI * radius * Math.abs(extent) / 360 / steps;
    const direction = radius > 0 ? 1 : -1;

    for (let i = 0; i < steps; i++) {
      this.left(stepAngle / 2 * direction);
      this.forward(stepLength);
      this.left(stepAngle / 2 * direction);
    }
    return `Drew circle with radius ${radius}`;
  }

  dot(size = null, color = null) {
    const dotSize = size || Math.max(this.penWidth + 4, 2 * this.penWidth);
    const dotColor = color || this.penColor;
    this.ctx.beginPath();
    this.ctx.arc(this.x, this.y, dotSize / 2, 0, 2 * Math.PI);
    this.ctx.fillStyle = dotColor;
    this.ctx.fill();
    return `Drew dot with size ${dotSize}`;
  }

  stamp() { this._drawTurtle(); return 'Stamped turtle'; }

  showturtle() { this.visible = true; this._updateIndicator(); return 'Turtle visible'; }
  st() { return this.showturtle(); }

  hideturtle() { this.visible = false; this._updateIndicator(); return 'Turtle hidden'; }
  ht() { return this.hideturtle(); }

  isvisible() { return this.visible; }

  speed(s) {
    if (s !== undefined) { this.speed = Math.min(Math.max(s, 0), 10); return `Speed set to ${this.speed}`; }
    return `Speed: ${this.speed}`;
  }

  clear() {
    this.ctx.fillStyle = '#ffffff';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    this._updateIndicator();
    return 'Canvas cleared';
  }

  reset() {
    this.clear();
    this.x = this.canvas.width / 2;
    this.y = this.canvas.height / 2;
    this.heading = 0;
    this.penDown = true;
    this.penColor = '#000000';
    this.penWidth = 2;
    this.fillColor = '#000000';
    this.filling = false;
    this.fillPath = [];
    this._updateIndicator();
    return 'Turtle reset';
  }

  bgcolor(color) {
    if (color !== undefined) {
      this.ctx.fillStyle = color;
      this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      return `Background color set to ${color}`;
    }
    return 'Background color';
  }

  _drawTurtle() {
    const size = 12;
    const rad = this.heading * Math.PI / 180;

    this.ctx.save();
    this.ctx.translate(this.x, this.y);
    this.ctx.rotate(-rad + Math.PI / 2);

    this.ctx.beginPath();
    this.ctx.moveTo(0, -size);
    this.ctx.lineTo(size / 2, size / 2);
    this.ctx.lineTo(0, size / 4);
    this.ctx.lineTo(-size / 2, size / 2);
    this.ctx.closePath();

    this.ctx.fillStyle = '#024A14';
    this.ctx.fill();
    this.ctx.strokeStyle = '#01350e';
    this.ctx.lineWidth = 1;
    this.ctx.stroke();
    this.ctx.restore();
  }

  _updateIndicator() {
    if (!this.indicatorElement) return;

    if (!this.visible) {
      this.indicatorElement.style.display = 'none';
      return;
    }

    this.indicatorElement.style.display = 'block';
    const wrapper = this.canvas.parentElement;
    if (!wrapper) return;

    const canvasRect = this.canvas.getBoundingClientRect();
    const wrapperRect = wrapper.getBoundingClientRect();
    const offsetX = canvasRect.left - wrapperRect.left;
    const offsetY = canvasRect.top - wrapperRect.top;

    this.indicatorElement.style.left = `${offsetX + this.x}px`;
    this.indicatorElement.style.top = `${offsetY + this.y}px`;
    this.indicatorElement.style.transform = `translate(-50%, -100%) rotate(${-this.heading + 90}deg)`;
  }

  setIndicatorElement(element) {
    this.indicatorElement = element;
    this._updateIndicator();
  }
}

export default Turtle;
