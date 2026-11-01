/* WRH – test prędkości internetu. Odpowiedź modułu: {"download": 52.3, "upload": 9.8, "unit": "Mbit/s"}. */
(function () {
    'use strict';

    const UNIT_LABELS = { 'Mbit/s': 'Mb/s', 'Mbyte/s': 'MB/s' };

    function valueHtml(value, unit) {
        if (value === null || value === undefined) return '–';
        return WRH.escapeHtml(WRH.formatNumber(value, 1)) + '<span class="stat-unit">' + WRH.escapeHtml(unit) + '</span>';
    }

    WRH.defineModule('speed-test', function (root, ctx) {
        const download = root.querySelector('[data-role="download"]');
        const upload = root.querySelector('[data-role="upload"]');

        return {
            async refresh() {
                try {
                    const data = await ctx.request('');
                    if (!data || typeof data !== 'object') throw new WRH.WrhError('invalid');
                    const unit = UNIT_LABELS[data.unit] || data.unit || 'Mb/s';
                    download.innerHTML = valueHtml(data.download, unit);
                    upload.innerHTML = valueHtml(data.upload, unit);
                    const missing = data.download === null || data.upload === null;
                    ctx.showError(missing ? 'Pomiar jeszcze się nie odbył.' : null);
                } catch (err) {
                    download.textContent = upload.textContent = '–';
                    ctx.showError(WRH.errorText(err));
                }
            }
        };
    });
})();
