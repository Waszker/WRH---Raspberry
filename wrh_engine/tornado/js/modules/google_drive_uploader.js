/* WRH – Google Drive Uploader. Odpowiedź modułu: {"minutes_ago": 12} albo {"minutes_ago": null} (brak uploadu). */
(function () {
    'use strict';

    function agoText(minutes) {
        const p = WRH.plural;
        if (minutes < 1) return 'przed chwilą';
        if (minutes < 60) return minutes + ' ' + p(minutes, 'minutę', 'minuty', 'minut') + ' temu';
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return hours + ' ' + p(hours, 'godzinę', 'godziny', 'godzin') + ' temu';
        const days = Math.floor(hours / 24);
        return days + ' ' + (days === 1 ? 'dzień' : 'dni') + ' temu';
    }

    WRH.defineModule('google-drive-uploader', function (root, ctx) {
        const label = root.querySelector('[data-role="last-upload"]');

        return {
            async refresh() {
                try {
                    const data = await ctx.request('');
                    if (!data || typeof data !== 'object') throw new WRH.WrhError('invalid');
                    const minutes = data.minutes_ago;
                    label.textContent = minutes === null || minutes === undefined
                        ? 'jeszcze nie było (od uruchomienia modułu)'
                        : agoText(Math.max(0, parseInt(minutes, 10) || 0));
                    ctx.showError(null);
                } catch (err) {
                    label.textContent = '–';
                    ctx.showError(WRH.errorText(err));
                }
            }
        };
    });
})();
