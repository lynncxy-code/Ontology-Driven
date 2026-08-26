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

        const form = new FormData();
        form.append('file', file, file.name);
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
        return response.data;
    }

    global.OntoTwinAssetUpload = {
        DEFAULT_MAX_BYTES,
        defaultName,
        validateGlb,
        upload,
    };
})(window);
