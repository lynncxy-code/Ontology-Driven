(function (root, factory) {
    const api = factory();
    if (typeof module === 'object' && module.exports) module.exports = api;
    root.OntoTwinHierarchyMenu = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
    const DEFAULT_UNASSIGNED_LABEL = '未分类';

    function normalizePath(value, fallbackLabel = DEFAULT_UNASSIGNED_LABEL) {
        const source = Array.isArray(value)
            ? value
            : (typeof value === 'string' ? value.replace(/\\/g, '/').split('/') : []);
        const path = source.map(part => String(part || '').trim()).filter(Boolean);
        return path.length ? path : [fallbackLabel];
    }

    function pathKey(path) {
        return normalizePath(path).join('\u001f');
    }

    function pathLabel(path) {
        return normalizePath(path).join(' / ');
    }

    function leafLabel(path) {
        const normalized = normalizePath(path);
        return normalized[normalized.length - 1];
    }

    function comparePaths(left, right) {
        const leftUnassigned = left.length === 1 && left[0] === DEFAULT_UNASSIGNED_LABEL;
        const rightUnassigned = right.length === 1 && right[0] === DEFAULT_UNASSIGNED_LABEL;
        if (leftUnassigned !== rightUnassigned) return leftUnassigned ? 1 : -1;
        return pathLabel(left).localeCompare(pathLabel(right), 'zh-Hans-CN');
    }

    function groupItems(items, getPath, getItemLabel) {
        const groups = new Map();
        for (const item of items || []) {
            const path = normalizePath(getPath(item));
            const key = pathKey(path);
            if (!groups.has(key)) {
                groups.set(key, {
                    key,
                    path,
                    label: leafLabel(path),
                    fullLabel: pathLabel(path),
                    items: [],
                });
            }
            groups.get(key).items.push(item);
        }
        const result = Array.from(groups.values());
        for (const group of result) {
            group.items.sort((a, b) => String(getItemLabel(a) || '').localeCompare(
                String(getItemLabel(b) || ''), 'zh-Hans-CN'
            ));
        }
        result.sort((a, b) => comparePaths(a.path, b.path));
        return result;
    }

    function dominantPathsByType(instances) {
        const countsByType = new Map();
        for (const instance of instances || []) {
            const rid = String(instance.object_type_rid || '').trim();
            if (!rid) continue;
            const path = normalizePath(instance.hierarchy_path);
            const key = pathKey(path);
            if (!countsByType.has(rid)) countsByType.set(rid, new Map());
            const counts = countsByType.get(rid);
            const current = counts.get(key) || { key, path, count: 0 };
            current.count += 1;
            counts.set(key, current);
        }
        const result = new Map();
        for (const [rid, counts] of countsByType.entries()) {
            const candidates = Array.from(counts.values()).sort((a, b) => {
                if (a.count !== b.count) return b.count - a.count;
                if (a.path.length !== b.path.length) return a.path.length - b.path.length;
                return comparePaths(a.path, b.path);
            });
            if (candidates.length) result.set(rid, candidates[0].path);
        }
        return result;
    }

    function groupObjectTypes(objectTypes, instances) {
        const pathsByType = dominantPathsByType(instances);
        return groupItems(
            objectTypes,
            item => pathsByType.get(item.rid) || [DEFAULT_UNASSIGNED_LABEL],
            item => item.name || item.rid
        );
    }

    function groupInstances(instances) {
        return groupItems(
            instances,
            item => item.hierarchy_path,
            item => item.display_name || item.id
        );
    }

    return {
        DEFAULT_UNASSIGNED_LABEL,
        normalizePath,
        pathKey,
        pathLabel,
        leafLabel,
        dominantPathsByType,
        groupObjectTypes,
        groupInstances,
    };
});
