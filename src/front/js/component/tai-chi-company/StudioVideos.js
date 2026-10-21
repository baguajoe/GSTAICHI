import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTcc } from "./TccContext";
import { apiFetch, formatDuration } from "./api";
import { FormMessage } from "./FormField";
import StudioVideoForm from "./StudioVideoForm";

const STATUS_HELP = {
    "Waiting for video": "No video file yet. Members see Coming Soon.",
    Uploading: "The upload has not finished. Choose the same file again to continue.",
    Processing: "Being prepared for streaming. This usually takes 10 to 30 minutes.",
    Ready: "Ready, but hidden from members.",
    Scheduled: "Ready. It will appear for members on the date shown.",
    Published: "Members can watch it now.",
    Failed: "Could not be prepared. See the reason, then press Retry or upload the file again."
};

const statusClass = (status) => ({
    Published: "tcc-badge-free", Scheduled: "tcc-badge-soon", Ready: "tcc-badge-soon",
    Failed: "tcc-badge-locked", Processing: "tcc-badge-soon", Uploading: "tcc-badge-soon"
}[status] || "tcc-badge-soon");

const shortDate = (iso) => (iso ? new Date(`${iso}Z`).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }) : "");

export const StatusBadge = ({ status }) => <span className={`tcc-badge ${statusClass(status)}`}>{status}</span>;

const VideoRow = ({ video, sectionLabel, onAction, busy }) => {
    const [confirmDelete, setConfirmDelete] = useState(false);
    const needsFile = ["Waiting for video", "Uploading", "Failed"].includes(video.studio_status);
    return (
        <li className="tcc-studio-item">
            <div className="tcc-studio-item-main">
                {video.thumbnail_url
                    ? <img src={video.thumbnail_url} alt="" className="tcc-studio-thumb" />
                    : <div className="tcc-studio-thumb tcc-thumb-placeholder" aria-hidden="true"><span>{sectionLabel(video.section)}</span></div>}
                <div>
                    <h3>{video.title}</h3>
                    <p className="tcc-badges">
                        <StatusBadge status={video.studio_status} />
                        <span className="tcc-badge tcc-badge-soon">{sectionLabel(video.section)}</span>
                        {video.is_free_sample && <span className="tcc-badge tcc-badge-free">Free sample</span>}
                        {video.show_in_library === false && <span className="tcc-badge tcc-badge-soon">In an article only</span>}
                    </p>
                    <p className="tcc-field-hint">{STATUS_HELP[video.studio_status]}</p>
                    {video.studio_status === "Scheduled" && <p>Appears on {shortDate(video.publish_at)}</p>}
                    {video.studio_status === "Failed" && video.failure_reason && <p className="tcc-error">{video.failure_reason}</p>}
                    {video.duration_seconds && <p>Length: {formatDuration(video.duration_seconds)}</p>}
                </div>
            </div>
            <div className="tcc-button-row tcc-left">
                {["Published", "Scheduled", "Ready"].includes(video.studio_status) && (
                    <Link to={`/tai-chi-company/watch/${video.slug}`} className="tcc-btn tcc-btn-outline">Watch</Link>
                )}
                <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => onAction("edit", video)}>Edit details</button>
                {needsFile && (
                    <button type="button" className="custom-btn1 tcc-btn" onClick={() => onAction("file", video)}>
                        {video.studio_status === "Uploading" ? "Continue the upload" : "Upload the video file"}
                    </button>
                )}
                {video.studio_status === "Failed" && video.original_filename && (
                    <button type="button" className="tcc-btn tcc-btn-outline" disabled={busy} onClick={() => onAction("retry", video)}>Retry</button>
                )}
                {["Published", "Scheduled"].includes(video.studio_status) && (
                    <button type="button" className="tcc-btn tcc-btn-outline" disabled={busy} onClick={() => onAction("unpublish", video)}>Hide from members</button>
                )}
                {video.studio_status === "Ready" && (
                    <button type="button" className="tcc-btn tcc-btn-outline" disabled={busy} onClick={() => onAction("publish", video)}>Show to members</button>
                )}
                {!confirmDelete
                    ? <button type="button" className="tcc-btn tcc-btn-outline tcc-btn-danger" onClick={() => setConfirmDelete(true)}>Delete</button>
                    : (
                        <div className="tcc-notice tcc-confirm">
                            <p>Delete "{video.title}" for good? Members will no longer see it. This cannot be undone.</p>
                            <div className="tcc-button-row tcc-left">
                                <button type="button" className="custom-btn1 tcc-btn" disabled={busy} onClick={() => onAction("delete", video)}>Yes, delete it</button>
                                <button type="button" className="tcc-btn tcc-btn-outline" onClick={() => setConfirmDelete(false)}>No, keep it</button>
                            </div>
                        </div>
                    )}
            </div>
        </li>
    );
};

const StudioVideos = ({ prefill, onPrefillUsed }) => {
    const { sectionLabel } = useTcc();
    const [videos, setVideos] = useState(null);
    const [panel, setPanel] = useState(null); // {mode, video}
    const [message, setMessage] = useState(null);
    const [error, setError] = useState(null);
    const [busy, setBusy] = useState(false);
    const [filter, setFilter] = useState("all");

    const load = () => apiFetch("/api/tcc/studio/videos").then(setVideos).catch(e => setError(e.message));
    useEffect(() => { load(); }, []);
    useEffect(() => {
        if (prefill) {
            setPanel({ mode: "new", defaults: prefill.defaults, questionId: prefill.questionId });
            onPrefillUsed();
        }
    }, [prefill]);
    // Refresh while something is being prepared
    useEffect(() => {
        if (!videos || !videos.some(v => v.studio_status === "Processing")) return undefined;
        const timer = setInterval(load, 20000);
        return () => clearInterval(timer);
    }, [videos]);

    const act = async (action, video) => {
        setMessage(null);
        setError(null);
        if (action === "edit" || action === "file") {
            setPanel({ mode: action, video });
            window.scrollTo(0, 0);
            return;
        }
        setBusy(true);
        try {
            if (action === "delete") {
                setMessage((await apiFetch(`/api/tcc/studio/videos/${video.id}`, { method: "DELETE" })).msg);
            } else if (action === "retry") {
                await apiFetch(`/api/tcc/studio/videos/${video.id}/retry`, { method: "POST" });
                setMessage(`"${video.title}" will be tried again. This usually takes 10 to 30 minutes.`);
            } else {
                await apiFetch(`/api/tcc/studio/videos/${video.id}`, { method: "PUT", body: { is_published: action === "publish" } });
                setMessage(action === "publish" ? `"${video.title}" is now shown to members.` : `"${video.title}" is now hidden from members.`);
            }
            await load();
        } catch (e) {
            setError(e.message);
        }
        setBusy(false);
    };

    if (panel) {
        return (
            <StudioVideoForm mode={panel.mode} video={panel.video} defaults={panel.defaults} questionId={panel.questionId}
                onCancel={() => setPanel(null)}
                onDone={(_saved, msg) => { setPanel(null); setMessage(msg); load(); window.scrollTo(0, 0); }} />
        );
    }

    const filters = [["all", "All"], ["Waiting for video", "Waiting for video"], ["Processing", "Processing"],
        ["Published", "Published"], ["Scheduled", "Scheduled"], ["Failed", "Failed"]];
    const shown = !videos ? [] : filter === "all" ? videos : videos.filter(v => v.studio_status === filter);

    return (
        <section>
            <FormMessage error={error} success={message} />
            <button type="button" className="custom-btn1 tcc-btn tcc-btn-big" onClick={() => setPanel({ mode: "new" })}>Add a new video</button>
            <h2 className="tcc-section">My Videos</h2>
            <div className="tcc-tabs" role="group" aria-label="Show videos by status">
                {filters.map(([key, label]) => (
                    <button key={key} type="button" aria-pressed={filter === key} className={`tcc-tab${filter === key ? " active" : ""}`}
                        onClick={() => setFilter(key)}>
                        {label}{videos && key !== "all" ? ` (${videos.filter(v => v.studio_status === key).length})` : ""}
                    </button>
                ))}
            </div>
            {!videos && !error && <p>Loading…</p>}
            {videos && shown.length === 0 && <p className="tcc-notice">No videos here.</p>}
            <ul className="tcc-studio-list">
                {shown.map(v => <VideoRow key={v.id} video={v} sectionLabel={sectionLabel} onAction={act} busy={busy} />)}
            </ul>
        </section>
    );
};

export default StudioVideos;
