(function (global) {
  'use strict';

  const IDENTITY = [[1, 0], [0, 1]];
  const IMAGE_COORDINATE_CONTRACT = 'image_px_top_left_y_down_v1';
  const GRID_STEPS = [10, 25, 50, 100, 250, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000];

  function multiply2(a, b) {
    return [
      [
        a[0][0] * b[0][0] + a[0][1] * b[1][0],
        a[0][0] * b[0][1] + a[0][1] * b[1][1],
      ],
      [
        a[1][0] * b[0][0] + a[1][1] * b[1][0],
        a[1][0] * b[0][1] + a[1][1] * b[1][1],
      ],
    ];
  }

  function invert2(matrix) {
    const determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0];
    if (!Number.isFinite(determinant) || Math.abs(determinant) < 1e-12) return IDENTITY;
    return [
      [matrix[1][1] / determinant, -matrix[0][1] / determinant],
      [-matrix[1][0] / determinant, matrix[0][0] / determinant],
    ];
  }

  function buildDisplayMatrix(display) {
    const value = display || {};
    const axisMap = value.axis_map || { x: '+x', y: '+y' };
    const axisVector = specification => [
      String(specification).endsWith('x') ? 0 : 1,
      String(specification).startsWith('-') ? -1 : 1,
    ];
    const [xIndex, xSign] = axisVector(axisMap.x || '+x');
    const [yIndex, ySign] = axisVector(axisMap.y || '+y');
    const axis = [[0, 0], [0, 0]];
    axis[0][xIndex] = xSign;
    axis[1][yIndex] = ySign;
    const flip = value.flip ? [[-1, 0], [0, 1]] : IDENTITY;
    const radians = Number(value.rotation_deg || 0) * Math.PI / 180;
    const rotation = [
      [Math.cos(radians), -Math.sin(radians)],
      [Math.sin(radians), Math.cos(radians)],
    ];
    return multiply2(rotation, multiply2(flip, axis));
  }

  function orientVector(matrix, x, y) {
    return [
      matrix[0][0] * x + matrix[0][1] * y,
      matrix[1][0] * x + matrix[1][1] * y,
    ];
  }

  function canvasSize(canvas) {
    const ratio = global.devicePixelRatio || 1;
    return {
      width: canvas.width / ratio,
      height: canvas.height / ratio,
      ratio,
    };
  }

  function resizeCanvas(canvas) {
    const rect = canvas.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) return null;
    const ratio = global.devicePixelRatio || 1;
    const width = Math.round(rect.width * ratio);
    const height = Math.round(rect.height * ratio);
    if (canvas.width !== width) canvas.width = width;
    if (canvas.height !== height) canvas.height = height;
    return { width: rect.width, height: rect.height, ratio };
  }

  function project(point, options, yDown) {
    const matrix = options.displayMatrix || IDENTITY;
    const scale = Number(options.scale || 1);
    const dx = (Number(point[0]) - Number(options.cameraX || 0)) * scale;
    const dyValue = (Number(point[1]) - Number(options.cameraY || 0)) * scale;
    const [orientedX, orientedY] = orientVector(matrix, dx, yDown ? dyValue : -dyValue);
    return [
      Number(options.canvasWidth) / 2 + orientedX,
      Number(options.canvasHeight) / 2 + orientedY,
    ];
  }

  function unproject(point, options, yDown) {
    const inverse = options.displayMatrixInverse || invert2(options.displayMatrix || IDENTITY);
    const scale = Number(options.scale || 1);
    const centeredX = Number(point[0]) - Number(options.canvasWidth) / 2;
    const centeredY = Number(point[1]) - Number(options.canvasHeight) / 2;
    const [baseX, baseY] = orientVector(inverse, centeredX, centeredY);
    return [
      Number(options.cameraX || 0) + baseX / scale,
      Number(options.cameraY || 0) + (yDown ? baseY : -baseY) / scale,
    ];
  }

  function imageToScreen(point, options) {
    return project(point, options, true);
  }

  function screenToImage(point, options) {
    return unproject(point, options, true);
  }

  function worldToScreen(point, options) {
    return project(point, options, false);
  }

  function screenToWorld(point, options) {
    return unproject(point, options, false);
  }

  function fitImage(options) {
    const imageWidth = Math.max(1, Number(options.imageWidth || 1));
    const imageHeight = Math.max(1, Number(options.imageHeight || 1));
    const matrix = options.displayMatrix || IDENTITY;
    const halfWidth = imageWidth / 2;
    const halfHeight = imageHeight / 2;
    const corners = [
      orientVector(matrix, -halfWidth, -halfHeight),
      orientVector(matrix, halfWidth, -halfHeight),
      orientVector(matrix, -halfWidth, halfHeight),
      orientVector(matrix, halfWidth, halfHeight),
    ];
    const xs = corners.map(point => point[0]);
    const ys = corners.map(point => point[1]);
    const displayWidth = Math.max(1, Math.max(...xs) - Math.min(...xs));
    const displayHeight = Math.max(1, Math.max(...ys) - Math.min(...ys));
    const padding = Number(options.padding || 0.95);
    return {
      cameraX: imageWidth / 2,
      cameraY: imageHeight / 2,
      scale: Math.max(
        0.00001,
        Math.min(
          Number(options.canvasWidth) / displayWidth,
          Number(options.canvasHeight) / displayHeight,
        ) * padding,
      ),
    };
  }

  function drawImage(ctx, image, options) {
    if (!image) return;
    const matrix = options.displayMatrix || IDENTITY;
    const scale = Number(options.scale || 1);
    const a = matrix[0][0] * scale;
    const b = matrix[1][0] * scale;
    const c = matrix[0][1] * scale;
    const d = matrix[1][1] * scale;
    const e = Number(options.canvasWidth) / 2
      - a * Number(options.cameraX || 0)
      - c * Number(options.cameraY || 0);
    const f = Number(options.canvasHeight) / 2
      - b * Number(options.cameraX || 0)
      - d * Number(options.cameraY || 0);
    ctx.save();
    ctx.transform(a, b, c, d, e, f);
    ctx.drawImage(image, 0, 0);
    ctx.restore();
  }

  function gridStep(scale, targetPixels) {
    const target = Number(targetPixels || 40);
    return GRID_STEPS.find(step => step * scale >= target) || GRID_STEPS[GRID_STEPS.length - 1];
  }

  function drawGrid(ctx, options) {
    const width = Number(options.canvasWidth);
    const height = Number(options.canvasHeight);
    const toScreen = options.toScreen;
    const fromScreen = options.fromScreen;
    if (!width || !height || typeof toScreen !== 'function' || typeof fromScreen !== 'function') return;
    const step = Number(options.step || gridStep(Number(options.scale || 1)));
    const corners = [fromScreen([0, 0]), fromScreen([width, 0]), fromScreen([0, height]), fromScreen([width, height])];
    const xs = corners.map(point => point[0]);
    const ys = corners.map(point => point[1]);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const startX = Math.floor(minX / step) * step;
    const startY = Math.floor(minY / step) * step;

    ctx.save();
    ctx.lineWidth = 1;
    ctx.setLineDash([]);
    for (let x = startX; x <= maxX + step; x += step) {
      const start = toScreen([x, minY]);
      const end = toScreen([x, maxY]);
      ctx.strokeStyle = Math.abs(x % (step * 5)) < 1e-6
        ? 'rgba(60,60,60,.18)'
        : 'rgba(60,60,60,.08)';
      ctx.beginPath();
      ctx.moveTo(start[0], start[1]);
      ctx.lineTo(end[0], end[1]);
      ctx.stroke();
    }
    for (let y = startY; y <= maxY + step; y += step) {
      const start = toScreen([minX, y]);
      const end = toScreen([maxX, y]);
      ctx.strokeStyle = Math.abs(y % (step * 5)) < 1e-6
        ? 'rgba(60,60,60,.18)'
        : 'rgba(60,60,60,.08)';
      ctx.beginPath();
      ctx.moveTo(start[0], start[1]);
      ctx.lineTo(end[0], end[1]);
      ctx.stroke();
    }
    ctx.restore();
  }

  global.OntoTwinSpatialCanvas = Object.freeze({
    IMAGE_COORDINATE_CONTRACT,
    IDENTITY,
    buildDisplayMatrix,
    invert2,
    resizeCanvas,
    canvasSize,
    imageToScreen,
    screenToImage,
    worldToScreen,
    screenToWorld,
    fitImage,
    drawImage,
    gridStep,
    drawGrid,
  });
})(window);
