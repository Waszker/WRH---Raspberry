/*
 * WRH – wspólny skrypt interfejsu. Czysty JavaScript (ES2017+, Safari iOS 15+), bez zależności.
 *
 * Moduły opisują się w swoim repr.html atrybutami:
 *     <article data-wrh-module="esp8266-socket" data-port="{port}"> ... </article>
 * a logika każdego typu modułu jest w jednym pliku js/modules/<typ>.js, który rejestruje się przez
 *     WRH.defineModule('esp8266-socket', function (root, ctx) { ...; return { refresh: async () => {...} }; });
 *
 * Ten plik zapewnia: wrhRequest() do komunikacji z modułami, toasty, plakietki stanu, blokowanie przycisków,
 * auto-odświeżanie co 60 s (z pauzą, gdy karta jest w tle) oraz stare funkcje getRequest/postRequest/...
 * dla zgodności ze starszymi repr.html.
 */
(function () {
    'use strict';

    const WRH = window.WRH = window.WRH || {};

    const REFRESH_INTERVAL_MS = 60 * 1000;
    const COMMAND_REFRESH_DELAY_MS = 700;
    const COMMAND_TIMEOUT_MS = 15000;

    const ERROR_TEXTS = {
        timeout: 'Brak odpowiedzi od urządzenia.',
        connection_refused: 'Moduł jest niedostępny (nie działa lub uruchamia się).',
        network: 'Brak połączenia z Raspberry. Sprawdź Wi‑Fi.',
        invalid: 'Urządzenie zwróciło nieprawidłową odpowiedź.',
        unknown: 'Wystąpił nieoczekiwany błąd.'
    };

    class WrhError extends Error {
        constructor(code, status) {
            super(code);
            this.name = 'WrhError';
            this.code = code;
            this.status = status || 0;
        }
    }

    /* ---------- Komunikacja ---------- */

    async function fetchWithTimeout(url, { method = 'GET', body, timeoutMs = 6000 } = {}) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);
        try {
            const response = await fetch(url, { method, body, signal: controller.signal, cache: 'no-store' });
            const text = await response.text();
            return { response, text };
        } catch (err) {
            throw new WrhError(err && err.name === 'AbortError' ? 'timeout' : 'network');
        } finally {
            clearTimeout(timer);
        }
    }

    /** Zwraca sparsowany JSON, tekst (stare moduły) albo null dla pustej odpowiedzi. Rzuca WrhError. */
    function parseResponse({ response, text }) {
        if (!response.ok) {
            let code = 'http';
            try { code = JSON.parse(text).error || code; } catch (e) { /* treść nie jest JSON-em */ }
            throw new WrhError(code, response.status);
        }
        if (!text) return null;
        const type = response.headers.get('Content-Type') || '';
        if (type.indexOf('application/json') !== -1) {
            try { return JSON.parse(text); } catch (e) { throw new WrhError('invalid', response.status); }
        }
        return text;
    }

    /**
     * Wysyła wiadomość do modułu nasłuchującego na porcie `port` (przez /request na serwerze Tornado).
     * @returns {Promise<object|string|null>} JSON z odpowiedzią modułu (null, gdy moduł nic nie odesłał)
     */
    async function wrhRequest(port, message = '', { timeoutMs = 6000, host = 'localhost' } = {}) {
        const body = new URLSearchParams({ host: host, port: String(port), message: message == null ? '' : String(message) });
        return parseResponse(await fetchWithTimeout('request', { method: 'POST', body, timeoutMs }));
    }

    async function fetchJson(url, options) {
        return parseResponse(await fetchWithTimeout(url, options));
    }

    function errorText(err) {
        const code = err && err.code;
        if (ERROR_TEXTS[code]) return ERROR_TEXTS[code];
        if (err && err.status) return 'Błąd serwera (' + err.status + ').';
        return ERROR_TEXTS.unknown;
    }

    /* ---------- Pomocnicze ---------- */

    function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    }

    function icon(name, extraClass) {
        return '<svg class="icon' + (extraClass ? ' ' + extraClass : '') + '" aria-hidden="true" focusable="false"><use href="#i-' + name + '"></use></svg>';
    }

    /** Polska odmiana: plural(2, 'cykl', 'cykle', 'cykli') -> 'cykle' */
    function plural(n, one, few, many) {
        if (n === 1) return one;
        const d = n % 10, dd = n % 100;
        return (d >= 2 && d <= 4 && (dd < 12 || dd > 14)) ? few : many;
    }

    function formatNumber(value, digits) {
        if (value === null || value === undefined || value === '' || isNaN(Number(value))) return '–';
        return Number(value).toLocaleString('pl-PL', { minimumFractionDigits: digits, maximumFractionDigits: digits });
    }

    /** "300" -> "5 min", "80" -> "1 min 20 s" */
    function formatDuration(seconds) {
        seconds = Number(seconds);
        if (!isFinite(seconds) || seconds <= 0) return '';
        const m = Math.floor(seconds / 60), s = seconds % 60;
        if (!m) return s + ' s';
        return m + ' min' + (s ? ' ' + s + ' s' : '');
    }

    /** Pole liczbowe: tylko cyfry; zwraca liczbę lub NaN. */
    function readInt(input) {
        const digits = String(input.value).replace(/[^0-9]/g, '');
        if (digits !== input.value) input.value = digits;
        return digits === '' ? NaN : parseInt(digits, 10);
    }

    function stateFromModule(value) {
        const v = String(value == null ? '' : value).toUpperCase();
        if (v === 'ON') return 'on';
        if (v === 'OFF') return 'off';
        return 'unknown';
    }

    const BADGES = {
        off: { icon: 'check', text: 'Wyłączone' },
        on: { icon: 'power', text: 'Włączone' },
        unknown: { icon: 'warning', text: 'Stan nieznany' },
        error: { icon: 'warning', text: 'Brak odpowiedzi' },
        loading: { icon: null, text: 'Sprawdzam…' }
    };

    /** Plakietka stanu: zawsze kolor + ikona + tekst. state: on | off | unknown | error | loading */
    function setBadge(el, state, text) {
        const badge = BADGES[state] || BADGES.unknown;
        el.dataset.state = BADGES[state] ? state : 'unknown';
        el.innerHTML = (badge.icon ? icon(badge.icon) : '<span class="spinner" aria-hidden="true"></span>') +
            '<span>' + escapeHtml(text || badge.text) + '</span>';
    }

    function setBusy(buttons, busyButton, busy) {
        buttons.forEach((b) => { b.disabled = busy; });
        if (busyButton) {
            busyButton.classList.toggle('is-busy', busy);
            busyButton.setAttribute('aria-busy', busy ? 'true' : 'false');
        }
    }

    /* ---------- Toasty ---------- */

    function toast(message, kind, durationMs) {
        const box = document.getElementById('wrh-toasts');
        if (!box) return;
        const iconName = kind === 'error' ? 'warning' : kind === 'ok' ? 'check' : null;
        const el = document.createElement('div');
        el.className = 'toast' + (kind ? ' toast--' + kind : '');
        el.innerHTML = (iconName ? icon(iconName) : '') + '<span>' + escapeHtml(message) + '</span>';
        while (box.children.length >= 3) box.removeChild(box.firstChild);
        box.appendChild(el);
        setTimeout(() => {
            el.classList.add('is-leaving');
            setTimeout(() => el.remove(), 250);
        }, durationMs || (kind === 'error' ? 5000 : 3000));
    }

    /* ---------- Rejestr modułów i odświeżanie ---------- */

    const factories = {};
    const instances = [];
    let lastRefresh = 0;
    let refreshingAll = null;

    function defineModule(type, factory) {
        factories[type] = factory;
    }

    /**
     * Wysyła polecenie do modułu: blokuje przyciski, pokazuje spinner i toast, po ~700 ms odświeża stan modułu.
     */
    async function runCommand({ port, message, button, buttons, successText, refresh }) {
        const group = buttons || (button ? [button] : []);
        setBusy(group, button, true);
        let ok = false;
        try {
            await wrhRequest(port, message, { timeoutMs: COMMAND_TIMEOUT_MS });
            toast(successText || 'Wysłano polecenie', 'ok');
            ok = true;
        } catch (err) {
            toast(errorText(err), 'error');
        } finally {
            setBusy(group, button, false);
        }
        // Odśwież także po błędzie - polecenie mogło dotrzeć mimo braku odpowiedzi
        if (refresh) setTimeout(refresh, COMMAND_REFRESH_DELAY_MS);
        return ok;
    }

    function createContext(root) {
        const port = root.dataset.port;
        const errorBox = root.querySelector('[data-role="error"]');
        const ctx = {
            root: root,
            port: port,
            request: (message, options) => wrhRequest(port, message, options),
            showError(text) {
                if (!errorBox) return;
                if (text) {
                    errorBox.innerHTML = icon('warning') + '<span>' + escapeHtml(text) + '</span>';
                    errorBox.hidden = false;
                } else {
                    errorBox.hidden = true;
                }
            },
            command: (options) => runCommand(Object.assign({ port: port, refresh: () => ctx.refresh() }, options)),
            refresh: () => Promise.resolve()
        };
        return ctx;
    }

    function mountModule(root) {
        const type = root.dataset.wrhModule;
        const factory = factories[type];
        if (!factory) {
            console.warn('WRH: brak obsługi modułu typu', type);
            return;
        }
        const ctx = createContext(root);
        let api;
        try {
            api = factory(root, ctx) || {};
        } catch (err) {
            console.error(err);
            ctx.showError('Błąd interfejsu tego modułu.');
            return;
        }
        const instance = { root: root, type: type, running: null };
        instance.run = function () {
            if (instance.running) return instance.running;
            root.classList.add('is-refreshing');
            instance.running = Promise.resolve()
                .then(() => api.refresh && api.refresh())
                .catch((err) => console.error(err))
                .then(() => {
                    instance.running = null;
                    root.classList.remove('is-refreshing');
                });
            return instance.running;
        };
        ctx.refresh = instance.run;
        root.querySelectorAll('[data-action="refresh"]').forEach((b) => b.addEventListener('click', () => instance.run()));
        instances.push(instance);
    }

    function refreshAll() {
        if (refreshingAll) return refreshingAll;
        document.documentElement.classList.add('is-refreshing-all');
        refreshingAll = Promise.all(instances.map((i) => i.run())).then(() => {
            lastRefresh = Date.now();
            refreshingAll = null;
            document.documentElement.classList.remove('is-refreshing-all');
            updateAgeLabel();
        });
        return refreshingAll;
    }

    function refreshType(type) {
        return Promise.all(instances.filter((i) => i.type === type).map((i) => i.run()));
    }

    function updateAgeLabel() {
        const label = document.getElementById('wrh-updated');
        if (!label || !lastRefresh) return;
        const seconds = Math.max(0, Math.round((Date.now() - lastRefresh) / 1000));
        let text;
        if (seconds < 5) text = 'zaktualizowano przed chwilą';
        else if (seconds < 60) text = 'zaktualizowano ' + seconds + ' s temu';
        else text = 'zaktualizowano ' + Math.floor(seconds / 60) + ' min temu';
        label.textContent = text;
    }

    function tick() {
        updateAgeLabel();
        if (!document.hidden && Date.now() - lastRefresh >= REFRESH_INTERVAL_MS) refreshAll();
    }

    function boot() {
        document.querySelectorAll('[data-wrh-module]').forEach(mountModule);

        const refreshButton = document.getElementById('wrh-refresh-all');
        if (refreshButton) refreshButton.addEventListener('click', refreshAll);

        // Aktywna zakładka widoczna na przewijanym pasku
        const activeTab = document.querySelector('.tab[aria-current="page"]');
        if (activeTab && activeTab.scrollIntoView) activeTab.scrollIntoView({ block: 'nearest', inline: 'center' });

        refreshAll();
        setInterval(tick, 5000);
        // iPhone: strona wraca z tła ze starym stanem - odśwież od razu
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && Date.now() - lastRefresh > 3000) refreshAll();
        });
        window.addEventListener('pageshow', (event) => { if (event.persisted) refreshAll(); });
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
    else setTimeout(boot, 0);

    /* ---------- Publiczne API ---------- */

    Object.assign(WRH, {
        WrhError, request: wrhRequest, fetchJson, errorText, escapeHtml, icon, plural, formatNumber, formatDuration,
        readInt, stateFromModule, setBadge, setBusy, toast, defineModule, runCommand, refreshAll, refreshType
    });
    window.wrhRequest = wrhRequest;

    /* ---------- Zgodność wsteczna (stare repr.html poza repozytorium) ---------- */

    function legacyRequest(host, port, message, callback) {
        const body = new URLSearchParams({ host: host || 'localhost', port: String(port), message: message == null ? '' : String(message) });
        fetch('request', { method: 'POST', body: body, cache: 'no-store' })
            .then((r) => (r.ok ? r.text() : Promise.reject(new WrhError('http', r.status))))
            .then((text) => { if (typeof callback === 'function') callback(text); })
            .catch((err) => console.warn('WRH:', err));
    }

    window.getRequest = legacyRequest;
    window.postRequest = legacyRequest;
    window.sendRequest = (host, port, message) => legacyRequest(host, port, message, null);
    window.getUptime = () => refreshType('system');
    window.getRestart = () => (WRH.restart ? WRH.restart() : undefined);
})();
