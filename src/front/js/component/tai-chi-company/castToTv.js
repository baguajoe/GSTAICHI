// Chromecast support (Chrome on Android and computers). AirPlay is handled by Safari's own player.
// The TV fetches the video itself with the same signed link, and its key with the link's token.

const CAST_SDK = "https://www.gstatic.com/cv/js/sender/v1/cast_sender.js?loadCastFramework=1";
let sdkPromise = null;

const isChrome = () => /Chrome\//.test(navigator.userAgent) && !/Edg\/|OPR\//.test(navigator.userAgent)
    && !/iPhone|iPad|iPod/.test(navigator.userAgent);

// Resolves to true when the Cast framework is ready (false on browsers without Chromecast support).
export const loadCastSdk = () => {
    if (!isChrome()) return Promise.resolve(false);
    if (sdkPromise) return sdkPromise;
    sdkPromise = new Promise((resolve) => {
        window.__onGCastApiAvailable = (available) => {
            if (!available || !window.cast || !window.cast.framework) {
                resolve(false);
                return;
            }
            window.cast.framework.CastContext.getInstance().setOptions({
                receiverApplicationId: window.chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID,
                autoJoinPolicy: window.chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED
            });
            resolve(true);
        };
        const script = document.createElement("script");
        script.src = CAST_SDK;
        script.async = true;
        script.onerror = () => resolve(false);
        document.head.appendChild(script);
    });
    return sdkPromise;
};

// Calls onChange(true/false) when a Chromecast is (not) available on the network. Returns an unsubscribe function.
export const watchCastDevices = (onChange) => {
    const framework = window.cast && window.cast.framework;
    if (!framework) return () => {};
    const context = framework.CastContext.getInstance();
    const update = () => onChange(context.getCastState() !== framework.CastState.NO_DEVICES_AVAILABLE);
    context.addEventListener(framework.CastContextEventType.CAST_STATE_CHANGED, update);
    update();
    return () => context.removeEventListener(framework.CastContextEventType.CAST_STATE_CHANGED, update);
};

// Asks the member to pick a TV, then starts the video there. onEnded is called when casting stops.
export const castVideo = async ({ url, title, startTime, onEnded }) => {
    const framework = window.cast.framework;
    const context = framework.CastContext.getInstance();
    await context.requestSession();
    const session = context.getCurrentSession();
    const media = window.chrome.cast.media;
    const info = new media.MediaInfo(url, "application/x-mpegurl");
    info.streamType = media.StreamType.BUFFERED;
    info.hlsSegmentFormat = media.HlsSegmentFormat.TS;
    info.metadata = new media.GenericMediaMetadata();
    info.metadata.title = title;
    const request = new media.LoadRequest(info);
    request.currentTime = startTime || 0;
    await session.loadMedia(request);

    const onSessionState = (event) => {
        if (event.sessionState === framework.SessionState.SESSION_ENDED) {
            context.removeEventListener(framework.CastContextEventType.SESSION_STATE_CHANGED, onSessionState);
            onEnded();
        }
    };
    context.addEventListener(framework.CastContextEventType.SESSION_STATE_CHANGED, onSessionState);
};

export const stopCasting = () => {
    const framework = window.cast && window.cast.framework;
    if (framework) framework.CastContext.getInstance().endCurrentSession(true);
};
