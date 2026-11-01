/*
 * WRH – Rango Iryga (nawadnianie). Markup w modules/rango_iryga/html/repr.html:
 *   <section data-wrh-module="rango-iryga" data-port="...">
 *     <article class="card" data-gpio="5" data-time="300" data-cycles="1" data-label="Linia 1"></article> ...
 * Polecenia (bez zmian względem starej wersji): "ON,<gpio>,<sekundy>,<cykle>", "OFF,<gpio>,-1,-1", "STATE".
 * Odpowiedź na STATE: {"relays": [{"gpio": 5, "state": "ON"|"OFF"|"UNKNOWN", "repeats": N}, ...]}
 */
(function () {
    'use strict';

    const PRESETS = [60, 180, 300, 600];
    const MIN_SECONDS = 1, MAX_SECONDS = 3600;
    const MIN_CYCLES = 1, MAX_CYCLES = 20;
    let uid = 0;

    function lineMarkup(id, label) {
        const I = WRH.icon;
        return '' +
            '<header class="card-head">' +
            '  <span class="card-icon">' + I('drop') + '</span>' +
            '  <h3 class="card-title">' + WRH.escapeHtml(label) + '</h3>' +
            '  <span class="badge" data-role="badge"></span>' +
            '</header>' +
            '<p class="note" data-role="note" hidden></p>' +
            '<div class="field">' +
            '  <span class="field-label" id="' + id + '-time-label">Czas trwania</span>' +
            '  <div class="seg" role="group" aria-labelledby="' + id + '-time-label">' +
            PRESETS.map((s) => '<button type="button" data-preset="' + s + '" aria-pressed="false">' + (s / 60) + ' min</button>').join('') +
            '  </div>' +
            '  <div class="input-row">' +
            '    <label class="input-suffix">' +
            '      <input class="input" type="text" inputmode="numeric" pattern="[0-9]*" maxlength="4" autocomplete="off"' +
            '             data-role="time" aria-label="Czas trwania w sekundach">' +
            '      <span class="input-suffix-text">sek.</span>' +
            '    </label>' +
            '    <span class="hint" data-role="time-hint"></span>' +
            '  </div>' +
            '</div>' +
            '<div class="field field--row">' +
            '  <label class="field-label" for="' + id + '-cycles">Liczba cykli</label>' +
            '  <div class="stepper">' +
            '    <button type="button" class="stepper-btn" data-step="-1" aria-label="Mniej cykli">' + I('minus') + '</button>' +
            '    <input class="input" id="' + id + '-cycles" type="text" inputmode="numeric" pattern="[0-9]*" maxlength="2"' +
            '           autocomplete="off" data-role="cycles">' +
            '    <button type="button" class="stepper-btn" data-step="1" aria-label="Więcej cykli">' + I('plus') + '</button>' +
            '  </div>' +
            '</div>' +
            '<div class="actions">' +
            '  <button type="button" class="btn btn-primary" data-command="on">' + I('power') + '<span>Włącz</span></button>' +
            '  <button type="button" class="btn btn-secondary" data-command="off">Wyłącz</button>' +
            '</div>';
    }

    function remainingText(n) {
        return WRH.plural(n, 'pozostał', 'pozostały', 'pozostało') + ' ' + n + ' ' + WRH.plural(n, 'cykl', 'cykle', 'cykli');
    }

    function setupLine(card, ctx) {
        const gpio = parseInt(card.dataset.gpio, 10);
        const label = card.dataset.label || ('GPIO ' + gpio);
        card.innerHTML = lineMarkup('rango-' + (++uid), label);

        const q = (sel) => card.querySelector(sel);
        const badge = q('[data-role="badge"]');
        const note = q('[data-role="note"]');
        const timeInput = q('[data-role="time"]');
        const timeHint = q('[data-role="time-hint"]');
        const cyclesInput = q('[data-role="cycles"]');
        const presetButtons = Array.from(card.querySelectorAll('[data-preset]'));
        const stepButtons = Array.from(card.querySelectorAll('[data-step]'));
        const commandButtons = Array.from(card.querySelectorAll('[data-command]'));

        function syncTime() {
            const seconds = WRH.readInt(timeInput);
            presetButtons.forEach((b) => b.setAttribute('aria-pressed', String(Number(b.dataset.preset) === seconds)));
            timeHint.textContent = seconds >= MIN_SECONDS && seconds <= MAX_SECONDS ? '= ' + WRH.formatDuration(seconds) : 'od 1 do 3600 sek.';
        }

        function setCycles(value) {
            const n = Math.min(MAX_CYCLES, Math.max(MIN_CYCLES, isNaN(value) ? MIN_CYCLES : value));
            cyclesInput.value = String(n);
            stepButtons[0].disabled = n <= MIN_CYCLES;
            stepButtons[1].disabled = n >= MAX_CYCLES;
            return n;
        }

        timeInput.value = card.dataset.time || '300';
        syncTime();
        setCycles(parseInt(card.dataset.cycles, 10));
        WRH.setBadge(badge, 'loading');

        presetButtons.forEach((b) => b.addEventListener('click', () => {
            timeInput.value = b.dataset.preset;
            syncTime();
        }));
        timeInput.addEventListener('input', syncTime);
        stepButtons.forEach((b) => b.addEventListener('click', () => {
            setCycles(WRH.readInt(cyclesInput) + Number(b.dataset.step));
        }));
        cyclesInput.addEventListener('change', () => setCycles(WRH.readInt(cyclesInput)));
        cyclesInput.addEventListener('blur', () => setCycles(WRH.readInt(cyclesInput)));

        commandButtons.forEach((button) => button.addEventListener('click', () => {
            let message, successText;
            if (button.dataset.command === 'on') {
                const seconds = WRH.readInt(timeInput);
                if (!(seconds >= MIN_SECONDS && seconds <= MAX_SECONDS)) {
                    WRH.toast('Podaj czas trwania od 1 do 3600 sekund.', 'error');
                    timeInput.focus();
                    return;
                }
                const cycles = setCycles(WRH.readInt(cyclesInput));
                message = 'ON,' + gpio + ',' + seconds + ',' + cycles;
                successText = label + ': wysłano polecenie włączenia';
            } else {
                message = 'OFF,' + gpio + ',-1,-1';
                successText = label + ': wysłano polecenie wyłączenia';
            }
            ctx.command({ message: message, button: button, buttons: commandButtons, successText: successText });
        }));

        return {
            gpio: gpio,
            show(relay) {
                if (!relay) {
                    WRH.setBadge(badge, 'error');
                    note.hidden = true;
                    return;
                }
                const state = WRH.stateFromModule(relay.state);
                const repeats = Math.max(0, parseInt(relay.repeats, 10) || 0);
                WRH.setBadge(badge, state);
                if (repeats > 0) {
                    note.innerHTML = WRH.icon('clock') + '<span>' + (state === 'off' ? 'Przerwa · ' : '') + remainingText(repeats) + '</span>';
                    note.hidden = false;
                } else {
                    note.hidden = true;
                }
            }
        };
    }

    WRH.defineModule('rango-iryga', function (root, ctx) {
        const lines = Array.from(root.querySelectorAll('[data-gpio]')).map((card) => setupLine(card, ctx));

        return {
            async refresh() {
                try {
                    let data = await ctx.request('STATE');
                    if (typeof data === 'string') data = WRH.legacy.rango(data, lines.map((l) => l.gpio));
                    if (!data || !Array.isArray(data.relays)) throw new WRH.WrhError('invalid');
                    let unknown = false;
                    lines.forEach((line) => {
                        const relay = data.relays.find((r) => Number(r.gpio) === line.gpio);
                        line.show(relay || { state: 'UNKNOWN', repeats: 0 });
                        if (!relay || WRH.stateFromModule(relay.state) === 'unknown') unknown = true;
                    });
                    ctx.showError(unknown ? 'Sterownik nawadniania nie odpowiada – stan linii jest nieznany.' : null);
                } catch (err) {
                    lines.forEach((line) => line.show(null));
                    ctx.showError(WRH.errorText(err));
                }
            }
        };
    });
})();
