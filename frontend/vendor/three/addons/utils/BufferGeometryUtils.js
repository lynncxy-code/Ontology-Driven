import { TriangleFanDrawMode, TriangleStripDrawMode } from 'three';

// GLTFLoader only needs this helper from the full Three.js utility bundle.
// Keep the vendored runtime small while still supporting strip/fan primitives.
function toTrianglesDrawMode(geometry, drawMode) {
    if (!geometry || drawMode === undefined) return geometry;

    const index = geometry.getIndex();
    const vertexCount = index
        ? index.count
        : geometry.attributes.position?.count || 0;
    const triangleCount = Math.max(0, vertexCount - 2);
    const newIndices = [];

    if (drawMode === TriangleFanDrawMode) {
        for (let i = 1; i <= triangleCount; i += 1) {
            newIndices.push(0, i, i + 1);
        }
    } else if (drawMode === TriangleStripDrawMode) {
        for (let i = 0; i < triangleCount; i += 1) {
            if (i % 2 === 0) newIndices.push(i, i + 1, i + 2);
            else newIndices.push(i + 2, i + 1, i);
        }
    } else {
        return geometry;
    }

    if (index) {
        const indexArray = index.array;
        for (let i = 0; i < newIndices.length; i += 1) {
            newIndices[i] = indexArray[newIndices[i]];
        }
    }

    geometry.setIndex(newIndices);
    geometry.clearGroups();
    return geometry;
}

export { toTrianglesDrawMode };
