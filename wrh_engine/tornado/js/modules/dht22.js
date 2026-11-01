/* WRH – czujnik DHT22. Odpowiedź modułu: {"humidity": 55.1, "temperature": 21.4} (null przed pierwszym pomiarem). */
(function () {
    'use strict';

    function valueHtml(value, unit) {
        if (value === null || value === undefined) return '–';
        return WRH.escapeHtml(WRH.formatNumber(value, 1)) + '<span class="stat-unit">' + unit + '</span>';
    }

    WRH.defineModule('dht22', function (root, ctx) {
        const temperature = root.querySelector('[data-role="temperature"]');
        const humidity = root.querySelector('[data-role="humidity"]');

        return {
            async refresh() {
                try {
                    let data = await ctx.request('');
                    if (typeof data === 'string') data = WRH.legacy.dht22(data);
                    if (!data || typeof data !== 'object') throw new WRH.WrhError('invalid');
                    temperature.innerHTML = valueHtml(data.temperature, '°C');
                    humidity.innerHTML = valueHtml(data.humidity, '%');
                    const missing = data.temperature === null || data.humidity === null;
                    ctx.showError(missing ? 'Czujnik nie wykonał jeszcze pomiaru.' : null);
                } catch (err) {
                    temperature.textContent = humidity.textContent = '–';
                    ctx.showError(WRH.errorText(err));
                }
            }
        };
    });
})();
