/* WRH – widok "System": statystyki Raspberry (/uptime, JSON) i restart (POST /restart). */
(function () {
    'use strict';

    const CPU_WARN_TEMP = 70;

    async function restart(button) {
        if (!window.confirm('Czy na pewno uruchomić ponownie Raspberry?\n\nStrona będzie niedostępna przez około minutę, a kolejne zaplanowane cykle nawadniania nie zostaną uruchomione.')) return;
        if (button) WRH.setBusy([button], button, true);
        try {
            await WRH.fetchJson('restart', { method: 'POST', timeoutMs: 8000 });
            WRH.toast('Raspberry uruchamia się ponownie…', 'ok', 8000);
        } catch (err) {
            WRH.toast('Nie udało się zlecić restartu. ' + WRH.errorText(err), 'error');
            if (button) WRH.setBusy([button], button, false);
        }
    }

    WRH.restart = () => restart(document.getElementById('wrh-restart'));

    document.addEventListener('click', (event) => {
        const button = event.target.closest && event.target.closest('[data-action="restart"]');
        if (button) restart(button);
    });

    WRH.defineModule('system', function (root, ctx) {
        const field = (name) => root.querySelector('[data-role="' + name + '"]');
        const cpuTile = field('cpu-tile');

        return {
            async refresh() {
                try {
                    const stats = await WRH.fetchJson('uptime');
                    if (!stats || typeof stats !== 'object') throw new WRH.WrhError('invalid');
                    field('date').textContent = stats.date || '–';
                    field('time').textContent = stats.time || '–';
                    field('uptime').textContent = stats.uptime || '–';
                    const hasTemp = stats.cpu_temp !== null && stats.cpu_temp !== undefined;
                    field('cpu_temp').innerHTML = hasTemp
                        ? WRH.escapeHtml(WRH.formatNumber(stats.cpu_temp, 1)) + '<span class="stat-unit">°C</span>'
                        : '–';
                    cpuTile.classList.toggle('stat--warn', hasTemp && Number(stats.cpu_temp) >= CPU_WARN_TEMP);
                    ctx.showError(null);
                } catch (err) {
                    ctx.showError('Nie udało się pobrać danych systemu. ' + WRH.errorText(err));
                }
            }
        };
    });
})();
