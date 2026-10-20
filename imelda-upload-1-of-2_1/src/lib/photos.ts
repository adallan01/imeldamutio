import type { ImageMetadata } from 'astro';
import green from '../assets/photos/portrait-green.jpg';
import iPink from '../assets/photos/imelda-pink.jpg';
import iCoral from '../assets/photos/imelda-coral.jpg';
import iTrench from '../assets/photos/imelda-trench.jpg';
import iVest from '../assets/photos/imelda-vest.jpg';
import iStripes from '../assets/photos/imelda-stripes.jpg';
import iCardigan from '../assets/photos/imelda-cardigan.jpg';
import iGroup from '../assets/photos/imelda-group.jpg';
import iOverhead from '../assets/photos/imelda-overhead.jpg';
import speakingOrange from '../assets/photos/speaking-orange.jpg';
import crowdOrange from '../assets/photos/crowd-orange.jpg';
import roomOrange from '../assets/photos/room-orange.jpg';
import stageTrio from '../assets/photos/stage-trio.jpg';
import familyFest from '../assets/photos/family-fest.jpg';
import timerCoat from '../assets/photos/timer-coat.jpg';

import cutPink from '../assets/cutouts/imelda-pink.png';
import cutCoral from '../assets/cutouts/imelda-coral.png';
import cutTrench from '../assets/cutouts/imelda-trench.png';
import cutVest from '../assets/cutouts/imelda-vest.png';
import cutStripes from '../assets/cutouts/imelda-stripes.png';
import cutCardigan from '../assets/cutouts/imelda-cardigan.png';

import spotlight from '../assets/stage/spotlight.jpg';
import brick from '../assets/stage/brick.jpg';
import sparkle from '../assets/stage/sparkle.jpg';
import podium from '../assets/stage/podium.jpg';
import hexsphere from '../assets/stage/hexsphere.jpg';
import silhouettes from '../assets/stage/silhouettes.jpg';
import eventHall from '../assets/stage/event-hall.jpg';
import gala from '../assets/stage/gala.jpg';

/** Real photographs of Imelda. `pos` is the focal point used for object-position on any crop.
 *  The imelda-* portraits are her studio photos with the studio removed and an original colour backdrop
 *  (scripts/prepare-studio-photos.py). Nothing about her is changed; only what is behind her. */
export const photos = {
  'portrait-green': { src: green, alt: 'Imelda Mutio smiling in a green satin shirt, one hand in her hair', pos: '50% 18%' },
  'imelda-pink': { src: iPink, alt: 'Imelda Mutio in a pink blazer, lowering her glasses and pointing at the camera', pos: '50% 20%' },
  'imelda-coral': { src: iCoral, alt: 'Imelda Mutio smiling in an orange pinstripe blazer', pos: '50% 20%' },
  'imelda-trench': { src: iTrench, alt: 'Imelda Mutio smiling in a beige trench coat', pos: '50% 22%' },
  'imelda-vest': { src: iVest, alt: 'Imelda Mutio laughing in a cream button-up vest, one hand at her ear', pos: '46% 20%' },
  'imelda-stripes': { src: iStripes, alt: 'Imelda Mutio in a green and blue striped top, holding up a microphone', pos: '45% 25%' },
  'imelda-cardigan': { src: iCardigan, alt: 'Imelda Mutio standing in a black cardigan and jeans, thumbs in her pockets', pos: '50% 22%' },
  'imelda-group': { src: iGroup, alt: 'Imelda Mutio with three guests after a conversation', pos: '50% 40%' },
  'imelda-overhead': { src: iOverhead, alt: 'Imelda Mutio seen from above, smiling up at the camera and making a peace sign', pos: '62% 35%' },
  'speaking-orange': { src: speakingOrange, alt: 'Imelda Mutio in an orange blazer, speaking into a microphone', pos: '48% 30%' },
  'crowd-orange': { src: crowdOrange, alt: 'Imelda Mutio with a microphone among a seated audience', pos: '45% 35%' },
  'room-orange': { src: roomOrange, alt: 'Imelda Mutio hosting a session, the audience facing her', pos: '42% 30%' },
  'stage-trio': { src: stageTrio, alt: 'Imelda Mutio hosting on stage with two guests, a countdown screen behind them', pos: '45% 35%' },
  'family-fest': { src: familyFest, alt: 'Imelda Mutio on an outdoor festival stage with a live band behind her', pos: '50% 65%' },
  'timer-coat': { src: timerCoat, alt: 'Imelda Mutio in a beige trench coat, microphone in hand, beside a five-minute countdown', pos: '45% 40%' },
} as const;
export type PhotoKey = keyof typeof photos;

/** Imelda with the background removed, for layering over the site's own backdrops. */
export const cutouts = {
  pink: { src: cutPink, alt: 'Imelda Mutio in a pink blazer, lowering her glasses and pointing at you' },
  coral: { src: cutCoral, alt: 'Imelda Mutio smiling in an orange pinstripe blazer' },
  trench: { src: cutTrench, alt: 'Imelda Mutio smiling in a beige trench coat' },
  vest: { src: cutVest, alt: 'Imelda Mutio laughing in a cream vest, one hand at her ear' },
  stripes: { src: cutStripes, alt: 'Imelda Mutio in a striped top, holding up a microphone' },
  cardigan: { src: cutCardigan, alt: 'Imelda Mutio standing in a black cardigan and jeans' },
} as const;
export type CutoutKey = keyof typeof cutouts;

/** Atmospheric stage backgrounds, graded plum to rose (decorative, empty alt). */
export const stages = { spotlight, brick, sparkle, podium, hexsphere, silhouettes, 'event-hall': eventHall, gala } as const;
export type StageKey = keyof typeof stages;
/** Where the light is in each background, for object-position. */
export const stagePos: Record<StageKey, string> = { spotlight: '50% 20%', brick: '50% 15%', sparkle: '50% 20%', podium: '50% 30%', hexsphere: '50% 40%', silhouettes: '50% 70%', 'event-hall': '50% 45%', gala: '50% 88%' };

const fromGlob = (g: Record<string, { default: ImageMetadata }>, prefix = '') =>
  Object.fromEntries(Object.entries(g).map(([k, v]) => [k.split('/').pop()!.replace(/\.jpg$/, '').replace(prefix, ''), v.default]));

/** YouTube thumbnails saved locally, keyed by video id (none yet). */
export const thumbs = fromGlob(import.meta.glob('../assets/thumbs/*.jpg', { eager: true }));
/** Event photos, keyed by file name (none yet; event credits use `photos`). */
export const events = fromGlob(import.meta.glob('../assets/events/*.jpg', { eager: true }));
