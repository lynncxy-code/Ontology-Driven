/**
 * coord_transform.js — 纯 JS 仿射变换工具
 * 与 coord_transform.py 算法对称，无外部依赖
 * PRD 2.9: CAD 坐标标定工作台
 */

const CoordTransform = (() => {

    /**
     * 最小二乘法求解 2D 仿射变换矩阵
     * @param {Array<[number,number]>} srcPoints - 源坐标 (CAD mm 或像素)
     * @param {Array<[number,number]>} dstPoints - 目标坐标 (UE cm, X/Y only)
     * @returns {{ matrix: number[][], rmse: number, perAnchorResiduals: number[], scaleX: number, scaleY: number, scaleConsistencyPct: number }}
     */
    function calibrate(srcPoints, dstPoints) {
        const n = srcPoints.length;
        if (n < 2) throw new Error('至少需要 2 组锚点');
        if (n !== dstPoints.length) throw new Error('源点与目标点数量不一致');

        // 构造超定方程 A * params = b
        // [src_x, src_y, 1, 0, 0, 0] * [a,b,tx,c,d,ty]^T = dst_x
        // [0, 0, 0, src_x, src_y, 1]                       = dst_y
        const rows = 2 * n;
        const A = [];
        const b = [];
        for (let i = 0; i < n; i++) {
            const [sx, sy] = srcPoints[i];
            const [dx, dy] = dstPoints[i];
            A.push([sx, sy, 1, 0, 0, 0]);
            A.push([0, 0, 0, sx, sy, 1]);
            b.push(dx);
            b.push(dy);
        }

        // 求解 A^T A x = A^T b (正规方程)
        const params = solveNormalEquation(A, b, rows, 6);

        const matrix = [
            [params[0], params[1], params[2]],
            [params[3], params[4], params[5]],
            [0, 0, 1]
        ];

        // 计算各锚点残差
        const perAnchorResiduals = [];
        for (let i = 0; i < n; i++) {
            const pred = applyTransform(matrix, srcPoints[i]);
            const err = Math.sqrt(
                Math.pow(pred[0] - dstPoints[i][0], 2) +
                Math.pow(pred[1] - dstPoints[i][1], 2)
            );
            perAnchorResiduals.push(parseFloat(err.toFixed(2)));
        }

        const rmse = Math.sqrt(
            perAnchorResiduals.reduce((sum, e) => sum + e * e, 0) / n
        );

        // 提取缩放因子
        const scaleX = Math.sqrt(params[0] ** 2 + params[3] ** 2);
        const scaleY = Math.sqrt(params[1] ** 2 + params[4] ** 2);
        const avgScale = (scaleX + scaleY) / 2;
        const scaleConsistencyPct = avgScale > 0
            ? Math.abs(scaleX - scaleY) / avgScale * 100
            : 0;

        return {
            matrix,
            rmse: parseFloat(rmse.toFixed(2)),
            perAnchorResiduals,
            scaleX: parseFloat(scaleX.toFixed(6)),
            scaleY: parseFloat(scaleY.toFixed(6)),
            scaleConsistencyPct: parseFloat(scaleConsistencyPct.toFixed(2))
        };
    }

    /**
     * 应用 3×3 仿射矩阵变换一个 2D 点
     * @param {number[][]} matrix - 3×3 仿射矩阵
     * @param {[number,number]} point - [x, y]
     * @returns {[number, number]} 变换后的 [x, y]
     */
    function applyTransform(matrix, point) {
        const x = matrix[0][0] * point[0] + matrix[0][1] * point[1] + matrix[0][2];
        const y = matrix[1][0] * point[0] + matrix[1][1] * point[1] + matrix[1][2];
        return [parseFloat(x.toFixed(2)), parseFloat(y.toFixed(2))];
    }

    /**
     * 正规方程求解: (A^T A) x = A^T b
     */
    function solveNormalEquation(A, b, m, n) {
        // A^T A (n×n)
        const ATA = Array.from({ length: n }, () => new Array(n).fill(0));
        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                let sum = 0;
                for (let k = 0; k < m; k++) sum += A[k][i] * A[k][j];
                ATA[i][j] = sum;
            }
        }

        // A^T b (n×1)
        const ATb = new Array(n).fill(0);
        for (let i = 0; i < n; i++) {
            let sum = 0;
            for (let k = 0; k < m; k++) sum += A[k][i] * b[k];
            ATb[i] = sum;
        }

        // Gaussian elimination with partial pivoting
        const aug = ATA.map((row, i) => [...row, ATb[i]]);
        for (let col = 0; col < n; col++) {
            // pivot
            let maxRow = col;
            for (let row = col + 1; row < n; row++) {
                if (Math.abs(aug[row][col]) > Math.abs(aug[maxRow][col])) maxRow = row;
            }
            [aug[col], aug[maxRow]] = [aug[maxRow], aug[col]];

            if (Math.abs(aug[col][col]) < 1e-12) throw new Error('锚点数据退化（可能共线），无法求解');

            for (let row = col + 1; row < n; row++) {
                const factor = aug[row][col] / aug[col][col];
                for (let j = col; j <= n; j++) aug[row][j] -= factor * aug[col][j];
            }
        }

        // Back substitution
        const x = new Array(n).fill(0);
        for (let i = n - 1; i >= 0; i--) {
            x[i] = aug[i][n];
            for (let j = i + 1; j < n; j++) x[i] -= aug[i][j] * x[j];
            x[i] /= aug[i][i];
        }
        return x;
    }

    return { calibrate, applyTransform };
})();
