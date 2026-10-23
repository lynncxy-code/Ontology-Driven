(function (global) {
    'use strict';

    const DEFAULT_MAX_BYTES = 500 * 1024 * 1024;

    function defaultName(filename) {
        return String(filename || '').replace(/\.glb$/i, '').trim();
    }

    async function validateGlb(file, maxBytes = DEFAULT_MAX_BYTES) {
        if (!file) throw new Error('请选择 GLB 模型文件。');
        if (!/\.glb$/i.test(file.name || '')) throw new Error('第一版只支持单个 GLB 模型文件。');
        if (!file.size) throw new Error('模型文件为空。');
        if (file.size > maxBytes) throw new Error(`模型文件不能超过 ${Math.floor(maxBytes / 1024 / 1024)} MB。`);
        const header = await file.slice(0, 12).arrayBuffer();
        if (header.byteLength < 12) throw new Error('GLB 文件内容不完整。');
        const view = new DataView(header);
        if (view.getUint32(0, true) !== 0x46546c67 || view.getUint32(4, true) !== 2) {
            throw new Error('文件不是有效的 GLB 2.0 模型。');
        }
        if (view.getUint32(8, true) !== file.size) {
            throw new Error('GLB 声明长度与实际文件不一致，文件可能已损坏。');
        }
    }

    async function upload(options) {
        const file = options.file;
        const name = String(options.name || '').trim();
        const description = String(options.description || '').trim();
        const visibility = options.visibility === 'private' ? 'private' : 'public';
        if (!name) throw new Error('请输入资产名称。');
        if (name.length > 64) throw new Error('资产名称不能超过 64 个字符。');
        if (description.length > 1000) throw new Error('资产描述不能超过 1000 个字符。');

        options.onState?.('checking', 0);
        await validateGlb(file, options.maxBytes || DEFAULT_MAX_BYTES);

        // 封面生成是增强能力：浏览器不支持 WebGL、模型材质异常或渲染失败时，
        // 仍继续上传 GLB，ArtStudio 会使用默认占位图。
        let cover = null;
        try {
            if (global.OntoTwinAssetCover?.generate) {
                cover = await global.OntoTwinAssetCover.generate(file, {
                    onState: (stage, progress) => options.onState?.(stage, progress),
                });
            } else {
                options.onState?.('cover_failed', 100);
            }
        } catch (_) {
            options.onState?.('cover_failed', 100);
        }

        const form = new FormData();
        form.append('file', file, file.name);
        if (cover) form.append('cover', cover, `${name || defaultName(file.name)}-cover.jpg`);
        form.append('name', name);
        form.append('description', description);
        form.append('visibility', visibility);
        options.onState?.('uploading', 0);

        const response = await axios.post('/api/v2/assets/uploads', form, {
            onUploadProgress(event) {
                if (!event.total) return;
                const progress = Math.min(100, Math.round(event.loaded / event.total * 100));
                options.onState?.(progress >= 100 ? 'publishing' : 'uploading', progress);
            },
        });
        options.onState?.('done', 100);
        const result = response.data;
        if (cover && result?.asset && !result.asset.cover_url) {
            // 上游封面地址可能异步生成；先用本地预览让新资产立即可识别。
            result.asset.cover_url = URL.createObjectURL(cover);
            result.asset._local_cover = true;
        }
        return result;
    }

    global.OntoTwinAssetUpload = {
        DEFAULT_MAX_BYTES,
        defaultName,
        validateGlb,
        upload,
    };
})(window);
