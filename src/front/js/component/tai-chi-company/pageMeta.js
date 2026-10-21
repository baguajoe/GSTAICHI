import { useEffect } from "react";

// The page title, description and link-preview tags for one page (an article), so search engines and shared
// links show that page instead of the site's general title. Everything is put back when the page closes.
// indexable: false asks search engines not to list the page (members-only articles show only a teaser).
// structuredData: schema.org JSON-LD describing the page, or null.

const ATTR = "data-tcc-meta";

const addTag = (tagName, attributes) => {
    const el = document.createElement(tagName);
    Object.entries(attributes).forEach(([name, value]) => el.setAttribute(name, value));
    el.setAttribute(ATTR, "");
    document.head.appendChild(el);
    return el;
};

export const usePageMeta = (meta) => {
    const key = meta ? JSON.stringify(meta) : "";
    useEffect(() => {
        if (!meta) return undefined;
        const previousTitle = document.title;
        // The page's own general tags step aside while this page shows its own
        const hidden = Array.from(document.head.querySelectorAll('meta[name="description"], meta[name="robots"], link[rel="canonical"]'))
            .filter(el => !el.hasAttribute(ATTR));
        hidden.forEach(el => el.remove());

        document.title = meta.title;
        if (meta.description) addTag("meta", { name: "description", content: meta.description });
        addTag("meta", { name: "robots", content: meta.indexable ? "index, follow" : "noindex, follow" });
        if (meta.url) addTag("link", { rel: "canonical", href: meta.url });
        addTag("meta", { property: "og:type", content: "article" });
        addTag("meta", { property: "og:title", content: meta.title });
        if (meta.description) addTag("meta", { property: "og:description", content: meta.description });
        if (meta.url) addTag("meta", { property: "og:url", content: meta.url });
        if (meta.image) addTag("meta", { property: "og:image", content: meta.image });
        addTag("meta", { name: "twitter:card", content: meta.image ? "summary_large_image" : "summary" });
        if (meta.structuredData) {
            addTag("script", { type: "application/ld+json" }).textContent = JSON.stringify(meta.structuredData);
        }

        return () => {
            document.head.querySelectorAll(`[${ATTR}]`).forEach(el => el.remove());
            hidden.forEach(el => document.head.appendChild(el));
            document.title = previousTitle;
        };
    }, [key]);
};
