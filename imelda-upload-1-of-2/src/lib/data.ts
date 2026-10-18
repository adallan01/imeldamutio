import library from '../../data/media-library.json';
import siteData from '../../data/site.json';
import servicesData from '../../data/services.json';

export type Entry = (typeof library.entries)[number] & {
  youtubeId?: string; venue?: string; author?: string; conflict?: string; eventDate?: string; publishedDate?: string;
};

export const site = siteData;
export const services = servicesData;

/** Only entries cleared for publication ever reach a page. */
export const published: Entry[] = (library.entries as Entry[]).filter((e) => e.publish === true);

const sortKey = (e: Entry) => e.eventDate || e.publishedDate || '';
export const byNewest = (a: Entry, b: Entry) => sortKey(b).localeCompare(sortKey(a));

export const engagements = published.filter((e) => e.section === 'engagement').sort(byNewest);
export const awards = published.filter((e) => e.section === 'award').sort(byNewest);
export const mediaItems = published.filter((e) => e.section === 'media').sort(byNewest);
export const featuredMedia = mediaItems.filter((e) => e.featured);
export const shows = published.filter((e) => e.section === 'show');
const videoOrder: string[] = [];
const vRank = (e: Entry) => { const i = videoOrder.indexOf(e.id); return i === -1 ? 99 : i; };
export const videos = published.filter((e) => e.youtubeId).sort((a, b) => vRank(a) - vRank(b));
export const videoGroup = (g: string) => videos.filter((v) => (v as any).videoGroup === g);
export const withTag = (tag: string) => published.filter((e) => e.tags?.includes(tag)).sort(byNewest);

/** Distinguishes what a credit actually is — booking, award or media appearance. */
export function kindOf(e: Entry): { label: string; cls: string } {
  if (e.section === 'engagement') return { label: 'Hosted', cls: 'badge--booking' };
  if (e.section === 'award') return { label: 'Award', cls: 'badge--award' };
  const map: Record<string, string> = { podcast: 'Podcast', video: 'Video', press: 'Press', interview: 'Interview', tv: 'Television', radio: 'Radio', byline: 'Byline' };
  return { label: map[e.type] || 'Media', cls: 'badge--media' };
}

/** Allow line breaks after slashes in long titles (e.g. 'Arrangement/Score/Adaptation'). */
export const soft = (s: string) => s.replace(/\//g, '/\u200B');

export const ctaHref = '/contact/';
export const showreelReady = Boolean(site.showreel.youtubeId);
