/*
 * WRH – gniazdko ESP8266. Polecenia (bez zmian): "ON,<sekundy>", "OFF,<sekundy>", "STATE"; -1 = bez limitu czasu.
 * Odpowiedź na STATE: {"state": "ON"|"OFF"|"UNKNOWN"}
 */
(function () {
    'use strict';

    const MAX_SECONDS = 86400;

    WRH.defineModule('esp8266-socket', function (root, ctx) {
        const q = (sel) => root.querySelector(sel);
        const badge = q('[data-role="badge"]');
        const unlimited = q('[data-role="unlimited"]');
        const timeInput = q('[data-role="time"]');
        const timeHint = q('[data-role="time-hint"]');
        const timeField = q('[data-role="time-field"]');
        const buttons = Array.from(root.querySelectorAll('[data-command]'));
        const name = (q('.card-title') || {}).textContent || 'Gniazdko';

        function syncTime() {
            timeInput.disabled = unlimited.checked;
            timeField.classList.toggle('is-disabled', unlimited.checked);
            const seconds = WRH.readInt(timeInput);
            if (unlimited.checked) timeHint.textContent = 'bez limitu';
            else timeHint.textContent = seconds >= 1 && seconds <= MAX_SECONDS ? '= ' + WRH.formatDuration(seconds) : 'podaj liczbę sekund';
        }

        unlimited.addEventListener('change', () => {
            syncTime();
            if (!unlimited.checked) timeInput.focus();
        });
        timeInput.addEventListener('input', syncTime);
        syncTime();
        WRH.setBadge(badge, 'loading');

        buttons.forEach((button) => button.addEventListener('click', () => {
            const turnOn = button.dataset.command === 'ON';
            let seconds = -1;
            // Limit czasu dotyczy tylko włączenia; "Wyłącz" zawsze wyłącza na stałe (OFF,-1)
            if (turnOn && !unlimited.checked) {
                seconds = WRH.readInt(timeInput);
                if (!(seconds >= 1 && seconds <= MAX_SECONDS)) {
                    WRH.toast('Podaj czas w sekundach (od 1 do ' + MAX_SECONDS + ').', 'error');
                    timeInput.focus();
                    return;
                }
            }
            ctx.command({
                message: (turnOn ? 'ON' : 'OFF') + ',' + seconds,
                button: button,
                buttons: buttons,
                successText: name.trim() + ': wysłano polecenie ' + (turnOn ? 'włączenia' : 'wyłączenia')
            });
        }));

        return {
            async refresh() {
                try {
                    let data = await ctx.request('STATE');
                    if (typeof data === 'string') data = WRH.legacy.esp8266(data);
                    if (!data || typeof data !== 'object') throw new WRH.WrhError('invalid');
                    const state = WRH.stateFromModule(data.state);
                    WRH.setBadge(badge, state);
                    ctx.showError(state === 'unknown' ? 'Gniazdko nie odpowiada – stan nieznany.' : null);
                } catch (err) {
                    WRH.setBadge(badge, 'error');
                    ctx.showError(WRH.errorText(err));
                }
            }
        };
    });
})();
