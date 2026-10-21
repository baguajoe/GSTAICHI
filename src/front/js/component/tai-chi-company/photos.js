import { uploadPicture } from "./uploader";

// Photos are made smaller in the browser before they are uploaded, so articles load fast on phones:
// at most 1600 pixels on the longest side (2000 for a cover), saved as WebP (JPEG where the browser cannot).
// Animated GIFs are kept as they are.

const QUALITY = 0.82;

const loadImage = (file) => new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => resolve({ img, done: () => URL.revokeObjectURL(url) });
    img.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error("This photo could not be opened. Please choose a JPG or PNG photo."));
    };
    img.src = url;
});

const toBlob = (canvas, type) => new Promise(resolve => canvas.toBlob(resolve, type, QUALITY));

export const preparePhoto = async (file, maxSide = 1600) => {
    if (file.type === "image/gif") return file;
    const { img, done } = await loadImage(file); // the browser turns phone photos the right way up
    try {
        const scale = Math.min(1, maxSide / Math.max(img.naturalWidth, img.naturalHeight));
        const canvas = document.createElement("canvas");
        canvas.width = Math.round(img.naturalWidth * scale);
        canvas.height = Math.round(img.naturalHeight * scale);
        canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
        let blob = await toBlob(canvas, "image/webp");
        if (!blob || blob.type !== "image/webp") blob = await toBlob(canvas, "image/jpeg");
        if (!blob) throw new Error("This photo could not be prepared. Please try another one.");
        // Already small and compressed: keep the original
        if (scale === 1 && blob.size >= file.size && /^image\/(jpeg|webp)$/.test(file.type)) return file;
        const ext = blob.type === "image/webp" ? "webp" : "jpg";
        return new File([blob], `${(file.name || "photo").replace(/\.[^.]+$/, "")}.${ext}`, { type: blob.type });
    } finally {
        done();
    }
};

// Resizes and uploads one photo. Private photos (inside articles) are only shown to members.
export const uploadPhoto = async (file, { cover = false } = {}) => {
    const prepared = await preparePhoto(file, cover ? 2000 : 1600);
    return uploadPicture(prepared, "/api/tcc/studio/images", cover ? {} : { private: true });
};
