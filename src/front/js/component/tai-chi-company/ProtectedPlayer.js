import React, { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from "react";
import { useTcc } from "./TccContext";
import { apiFetch, getToken } from "./api";
import Watermark from "./watermark";
import { loadCastSdk, watchCastDevices, castVideo, stopCasting } from "./castToTv";

// Protected video player: AES-128 HLS through hls.js, or Safari's own player on Apple devices,
// with a moving watermark (when switched on in admin settings), the 2-device limit, heartbeats, and casting to TVs.

const isAppleDevice = () => {
    const ua = navigator.userAgent;
    if (/iPhone|iPad|iPod/.test(ua)) return true;
    if (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1) return true; // iPad in desktop mode
    return /Safari\//.test(ua) && /Macintosh/.test(ua) && !/Chrome|Chromium|Edg\/|Firefox/.test(ua);
};

const formatTime = (seconds) => {
    const s = Math.max(0, Math.floor(seconds));
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = String(s % 60).padStart(2, "0");
    return h ? `${h}:${String(m).padStart(2, "0")}:${sec}` : `${m}:${sec}`;
};

// Hook for future DRM (FairPlay / Widevine). The backend sends drm: null for AES-128 HLS today.
const drmConfigFor = (drm) => (drm ? { emeEnabled: true } : {});

const stopSessionInBackground = (sessionId) => {
    if (!sessionId) return;
    try {
        fetch(`${process.env.BACKEND_URL}/api/tcc/stop/${sessionId}`, {
            method: "POST", keepalive: true, headers: { Authorization: `Bearer ${getToken()}` }
        });
    } catch (e) {
        // The session also ends by itself 60 seconds after the last heartbeat
    }
};

// showChapters: false when the page shows its own chapter list (the Studio's Review chapters).
// The ref gives seek(seconds) and currentTime(); a seek before the video has started waits for it to start.
const ProtectedPlayer = forwardRef(({ video, showChapters = true }, ref) => {
    const { user } = useTcc();
    const stageRef = useRef(null);
    const videoRef = useRef(null);
    const hlsRef = useRef(null);
    const playInfoRef = useRef(null);
    const sessionRef = useRef(null);
    const heartbeatRef = useRef(null);
    const watermarkRef = useRef(null);
    const castingRef = useRef(null);
    const pendingSeekRef = useRef(null);

    const [phase, setPhase] = useState("notice"); // notice | starting | playing | limit | stopped
    const [message, setMessage] = useState(null);
    const [otherSessions, setOtherSessions] = useState([]);
    const [chapters, setChapters] = useState(video.chapters || []);
    const [pseudoFullscreen, setPseudoFullscreen] = useState(false);
    const [canCast, setCanCast] = useState(false);
    const [canAirPlay, setCanAirPlay] = useState(false);
    const [casting, setCasting] = useState(null); // "tv" | "airplay" | null

    const ratio = video.width && video.height ? video.width / video.height : 16 / 9;

    const teardown = useCallback((stopOnServer = true) => {
        clearInterval(heartbeatRef.current);
        heartbeatRef.current = null;
        if (watermarkRef.current) watermarkRef.current.stop();
        watermarkRef.current = null;
        if (hlsRef.current) hlsRef.current.destroy();
        hlsRef.current = null;
        const v = videoRef.current;
        if (v) {
            v.pause();
            v.removeAttribute("src");
            v.load();
        }
        if (stopOnServer) stopSessionInBackground(sessionRef.current);
        sessionRef.current = null;
    }, []);

    // endedByServer: the server already ended the session (another device, plan change), so don't stop it again
    const showStopped = useCallback((text, endedByServer = false) => {
        teardown(!endedByServer);
        setMessage(text);
        setPhase("stopped");
    }, [teardown]);

    const startWatermark = useCallback((text) => {
        if (watermarkRef.current) watermarkRef.current.stop();
        watermarkRef.current = new Watermark(stageRef.current, text, () => {
            if (videoRef.current) videoRef.current.pause();
            showStopped("Playback was paused because the member watermark was removed. Please reload the page.");
        });
        watermarkRef.current.start();
    }, [showStopped]);

    const startHeartbeat = useCallback((seconds) => {
        clearInterval(heartbeatRef.current);
        heartbeatRef.current = setInterval(async () => {
            const sessionId = sessionRef.current;
            if (!sessionId) return;
            try {
                await apiFetch(`/api/tcc/heartbeat/${sessionId}`, {
                    method: "POST", body: { position: Math.floor((videoRef.current && videoRef.current.currentTime) || 0) }
                });
            } catch (e) {
                if (e.status === 410 || e.status === 403 || e.status === 404 || e.status === 401) {
                    if (castingRef.current === "tv") stopCasting();
                    showStopped(e.message, true);
                }
                // Other errors (a moment without internet): try again at the next heartbeat
            }
        }, seconds * 1000);
    }, [showStopped]);

    const attachSource = useCallback(async (info) => {
        const v = videoRef.current;
        const useNative = isAppleDevice() && v.canPlayType("application/vnd.apple.mpegurl");
        if (useNative) {
            // Safari's own player (needed for AirPlay and iPhone). The Worker put the token on the key address.
            v.src = info.url;
        } else {
            const { default: Hls } = await import(/* webpackChunkName: "hls" */ "hls.js");
            if (!Hls.isSupported()) {
                showStopped("This browser cannot play the video. Please update your browser, or try Chrome, Safari or Edge.");
                return false;
            }
            const hls = new Hls({
                ...drmConfigFor(info.drm),
                maxBufferLength: 30,
                xhrSetup: (xhr, url) => {
                    // Only the key request goes to our API; video pieces go to the media Worker with their token
                    if (url.includes("/api/tcc/key/")) {
                        xhr.setRequestHeader("Authorization", `Bearer ${getToken()}`);
                        xhr.setRequestHeader("X-Playback-Session", sessionRef.current);
                    }
                }
            });
            let mediaRecoveries = 0;
            hls.on(Hls.Events.ERROR, (_event, data) => {
                if (!data.fatal) return;
                if (data.type === Hls.ErrorTypes.MEDIA_ERROR && mediaRecoveries < 2) {
                    mediaRecoveries += 1;
                    hls.recoverMediaError();
                    return;
                }
                const code = data.response && data.response.code;
                showStopped(code === 403
                    ? "This video link has expired. Please press Play again."
                    : "The video stopped because of a connection problem. Please check your internet and press Play again.");
            });
            hls.loadSource(info.url);
            hls.attachMedia(v);
            hlsRef.current = hls;
        }
        return true;
    }, [showStopped]);

    const applyPendingSeek = useCallback(() => {
        const v = videoRef.current;
        const t = pendingSeekRef.current;
        if (!v || t === null) return;
        pendingSeekRef.current = null;
        if (v.readyState >= 1) v.currentTime = t;
        else v.addEventListener("loadedmetadata", () => { v.currentTime = t; }, { once: true });
    }, []);

    const start = useCallback(async (extra = {}) => {
        setMessage(null);
        setPhase("starting");
        let info;
        try {
            info = await apiFetch(`/api/tcc/play/${encodeURIComponent(video.slug)}`, { method: "POST", body: extra });
        } catch (e) {
            if (e.status === 409 && e.data && e.data.code === "stream_limit") {
                setOtherSessions(e.data.sessions || []);
                setMessage(e.data.msg);
                setPhase("limit");
                return;
            }
            setMessage(e.message);
            setPhase("stopped");
            return;
        }
        playInfoRef.current = info;
        sessionRef.current = info.session_id;
        setChapters(info.chapters || []);
        setPhase("playing");
        if (info.watermark_text) startWatermark(info.watermark_text); // no text: the watermark is switched off in admin
        startHeartbeat(info.heartbeat_seconds || 20);
        if (!(await attachSource(info))) return;
        applyPendingSeek();
        try {
            await videoRef.current.play();
        } catch (e) {
            // Some phones need a second tap on the video's own play button; the controls are showing
        }
    }, [video.slug, attachSource, startWatermark, startHeartbeat, applyPendingSeek]);

    // Pause when the member switches to another tab or app (unless the video is playing on a TV)
    useEffect(() => {
        const onVisibility = () => {
            const v = videoRef.current;
            if (!document.hidden || !v) return;
            if (castingRef.current || v.webkitCurrentPlaybackTargetIsWireless) return;
            v.pause();
        };
        document.addEventListener("visibilitychange", onVisibility);
        return () => document.removeEventListener("visibilitychange", onVisibility);
    }, []);

    // Keep the watermark visible in full screen: never let the bare video element go full screen
    useEffect(() => {
        const v = videoRef.current;
        const onFullscreen = () => {
            const el = document.fullscreenElement || document.webkitFullscreenElement;
            if (el && el === v) {
                const exit = document.exitFullscreen || document.webkitExitFullscreen;
                Promise.resolve(exit && exit.call(document)).then(() => enterFullscreen()).catch(() => setPseudoFullscreen(true));
            }
        };
        const onIosFullscreen = () => {
            // iPhone's own full screen hides the watermark, so use our full-screen view instead
            if (v.webkitExitFullscreen) v.webkitExitFullscreen();
            setPseudoFullscreen(true);
        };
        document.addEventListener("fullscreenchange", onFullscreen);
        document.addEventListener("webkitfullscreenchange", onFullscreen);
        v.addEventListener("webkitbeginfullscreen", onIosFullscreen);
        return () => {
            document.removeEventListener("fullscreenchange", onFullscreen);
            document.removeEventListener("webkitfullscreenchange", onFullscreen);
            v.removeEventListener("webkitbeginfullscreen", onIosFullscreen);
        };
    }, []);

    // AirPlay (Safari) and Chromecast (Chrome) buttons
    useEffect(() => {
        const v = videoRef.current;
        let unwatch = () => {};
        let cancelled = false;
        const onAirPlayAvailability = (e) => setCanAirPlay(e.availability === "available");
        const onWireless = () => {
            const wireless = !!v.webkitCurrentPlaybackTargetIsWireless;
            castingRef.current = wireless ? "airplay" : null;
            setCasting(wireless ? "airplay" : null);
        };
        if (window.WebKitPlaybackTargetAvailabilityEvent) {
            v.addEventListener("webkitplaybacktargetavailabilitychanged", onAirPlayAvailability);
            v.addEventListener("webkitcurrentplaybacktargetiswirelesschanged", onWireless);
        } else {
            loadCastSdk().then((ready) => {
                if (ready && !cancelled) unwatch = watchCastDevices(setCanCast);
            });
        }
        return () => {
            cancelled = true;
            unwatch();
            v.removeEventListener("webkitplaybacktargetavailabilitychanged", onAirPlayAvailability);
            v.removeEventListener("webkitcurrentplaybacktargetiswirelesschanged", onWireless);
        };
    }, []);

    // Stop cleanly when leaving the page
    useEffect(() => {
        const onLeave = () => stopSessionInBackground(sessionRef.current);
        window.addEventListener("pagehide", onLeave);
        return () => {
            window.removeEventListener("pagehide", onLeave);
            teardown(true);
        };
    }, [teardown]);

    const enterFullscreen = () => {
        const stage = stageRef.current;
        const request = stage.requestFullscreen || stage.webkitRequestFullscreen;
        if (request) {
            Promise.resolve(request.call(stage)).catch(() => setPseudoFullscreen(true));
        } else {
            setPseudoFullscreen(true);
        }
    };

    const toggleFullscreen = () => {
        const current = document.fullscreenElement || document.webkitFullscreenElement;
        if (current) {
            (document.exitFullscreen || document.webkitExitFullscreen).call(document);
        } else if (pseudoFullscreen) {
            setPseudoFullscreen(false);
        } else {
            enterFullscreen();
        }
    };

    const castToTv = async () => {
        const info = playInfoRef.current;
        if (!info) return;
        try {
            await castVideo({
                url: info.url, title: video.title, startTime: videoRef.current.currentTime,
                onEnded: () => {
                    castingRef.current = null;
                    setCasting(null);
                }
            });
            videoRef.current.pause();
            castingRef.current = "tv";
            setCasting("tv");
        } catch (e) {
            // The member closed the TV picker; nothing to do
        }
    };

    const seek = useCallback((seconds) => {
        const v = videoRef.current;
        if (!v || phase !== "playing") {
            pendingSeekRef.current = seconds; // used when the video starts
            return;
        }
        v.currentTime = seconds;
        v.play().catch(() => {});
    }, [phase]);

    useImperativeHandle(ref, () => ({
        seek,
        currentTime: () => (videoRef.current ? videoRef.current.currentTime : 0),
        isPlaying: () => phase === "playing"
    }), [seek, phase]);

    const licensedTo = user.name || user.email;
    return (
        <div className="tcc-player-wrap">
            <div
                ref={stageRef}
                className={`tcc-player-stage${pseudoFullscreen ? " tcc-player-pseudo-full" : ""}`}
                style={{ "--tcc-ratio": ratio }}
                onContextMenu={(e) => e.preventDefault()}
            >
                <video
                    ref={videoRef}
                    className="tcc-video"
                    controls={phase === "playing"}
                    playsInline
                    preload="none"
                    controlsList="nodownload nofullscreen"
                    disablePictureInPicture
                    x-webkit-airplay="allow"
                    aria-label={video.title}
                />

                {phase === "notice" && (
                    <div className="tcc-player-overlay">
                        <p className="tcc-player-title">Before you watch</p>
                        <p>This video is licensed to <strong>{licensedTo}</strong>. Recording or sharing is prohibited and traceable.</p>
                        <button type="button" className="custom-btn1 tcc-btn tcc-btn-big" onClick={() => start()}>
                            I understand, play the video
                        </button>
                    </div>
                )}
                {phase === "starting" && <div className="tcc-player-overlay"><p className="tcc-player-title">Starting the video…</p></div>}
                {phase === "limit" && (
                    <div className="tcc-player-overlay">
                        <p className="tcc-player-title">Playing on another device</p>
                        <p>{message}</p>
                        <p>To watch here, stop the video on the other device:</p>
                        {otherSessions.map(s => (
                            <button key={s.id} type="button" className="custom-btn1 tcc-btn tcc-btn-block tcc-spaced"
                                onClick={() => start({ end_session_id: s.id })}>
                                Stop it on the {s.device}{s.video_title ? ` (${s.video_title})` : ""} and watch here
                            </button>
                        ))}
                    </div>
                )}
                {phase === "stopped" && (
                    <div className="tcc-player-overlay">
                        <p className="tcc-player-title">The video has stopped</p>
                        <p>{message}</p>
                        <button type="button" className="custom-btn1 tcc-btn" onClick={() => start()}>Play again</button>
                    </div>
                )}
                {casting && phase === "playing" && (
                    <div className="tcc-player-overlay tcc-player-overlay-light">
                        <p className="tcc-player-title">Playing on your TV</p>
                        {casting === "tv" && (
                            <button type="button" className="tcc-btn tcc-btn-outline" onClick={stopCasting}>Stop playing on the TV</button>
                        )}
                    </div>
                )}
                {pseudoFullscreen && (
                    <button type="button" className="tcc-btn tcc-btn-outline tcc-exit-full" onClick={() => setPseudoFullscreen(false)}>
                        Exit full screen
                    </button>
                )}
            </div>

            {phase === "playing" && (
                <div className="tcc-player-buttons">
                    <button type="button" className="tcc-btn tcc-btn-outline" onClick={toggleFullscreen}>Full screen</button>
                    {canCast && !casting && (
                        <button type="button" className="tcc-btn tcc-btn-outline" onClick={castToTv}>Play on TV (Chromecast)</button>
                    )}
                    {canAirPlay && (
                        <button type="button" className="tcc-btn tcc-btn-outline"
                            onClick={() => videoRef.current.webkitShowPlaybackTargetPicker()}>
                            Play on Apple TV (AirPlay)
                        </button>
                    )}
                </div>
            )}

            {showChapters && chapters.length > 0 && (
                <section className="tcc-chapters" aria-label="Chapters">
                    <h2>Chapters</h2>
                    <ol>
                        {chapters.map((c, i) => (
                            <li key={i}>
                                <button type="button" className="tcc-chapter" onClick={() => seek(c.start)} disabled={phase !== "playing"}>
                                    <span className="tcc-chapter-time">{formatTime(c.start)}</span> {c.label}
                                </button>
                            </li>
                        ))}
                    </ol>
                </section>
            )}
        </div>
    );
});

export default ProtectedPlayer;
