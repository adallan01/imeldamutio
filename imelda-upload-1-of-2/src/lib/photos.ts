import type { ImageMetadata } from 'astro';
import green from '../assets/photos/portrait-green.jpg';
import navy from '../assets/photos/portrait-navy.jpg';
import studioMic from '../assets/photos/studio-mic.jpg';
import speakingOrange from '../assets/photos/speaking-orange.jpg';
import crowdOrange from '../assets/photos/crowd-orange.jpg';
import roomOrange from '../assets/photos/room-orange.jpg';
import stageTrio from '../assets/photos/stage-trio.jpg';
import familyFest from '../assets/photos/family-fest.jpg';
import timerCoat from '../assets/photos/timer-coat.jpg';

import cutGreen from '../assets/cutouts/imelda-green.png';
import cutOrange from '../assets/cutouts/imelda-orange.png';
import cutCoat from '../assets/cutouts/imelda-coat.png';

import spotlight from '../assets/stage/spotlight.jpg';
import brick from '../assets/stage/brick.jpg';
import sparkle from '../assets/stage/sparkle.jpg';
import podium from '../assets/stage/podium.jpg';
import hexsphere from '../assets/stage/hexsphere.jpg';
import silhouettes from '../assets/stage/silhouettes.jpg';
import eventHall from '../assets/stage/event-hall.jpg';
import gala from '../assets/stage/gala.jpg';

/** Real photographs of Imelda. `pos` is the focal point used for object-position on any crop. */
export const photos = {
  'portrait-green': { src: green, alt: 'Imelda Mutio smiling in a green satin shirt, one hand in her hair', pos: '50% 18%' },
  'portrait-navy': { src: navy, alt: 'Imelda Mutio smiling in a green satin shirt', pos: '50% 18%' },
  'studio-mic': { src: studioMic, alt: 'Imelda Mutio smiling at the microphone in a radio studio, wearing headphones', pos: '45% 30%' },
  'speaking-orange': { src: speakingOrange, alt: 'Imelda Mutio in an orange blazer, speaking into a microphone', pos: '48% 30%' },
  'crowd-orange': { src: crowdOrange, alt: 'Imelda Mutio with a microphone among a seated audience', pos: '45% 35%' },
  'room-orange': { src: roomOrange, alt: 'Imelda Mutio hosting a session, the audience facing her', pos: '42% 30%' },
  'stage-trio': { src: stageTrio, alt: 'Imelda Mutio hosting on stage with two guests, a countdown screen behind them', pos: '45% 35%' },
  'family-fest': { src: familyFest, alt: 'Imelda Mutio on an outdoor festival stage with a live band behind her', pos: '50% 65%' },
  'timer-coat': { src: timerCoat, alt: 'Imelda Mutio in a beige trench coat, microphone in hand, beside a five-minute countdown', pos: '45% 40%' },
} as const;
export type PhotoKey = keyof typeof photos;

/** Imelda with the background removed, for placing under stage light. */
export const cutouts = {
  green: { src: cutGreen, alt: 'Imelda Mutio smiling in a green satin shirt' },
  orange: { src: cutOrange, alt: 'Imelda Mutio in an orange blazer, speaking into a microphone' },
  coat: { src: cutCoat, alt: 'Imelda Mutio in a beige trench coat, holding a microphone' },
} as const;
export type CutoutKey = keyof typeof cutouts;

/** Atmospheric stage backgrounds, graded to the brand blue (decorative, empty alt). */
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
/** Brand-blue duotone versions of every photo, keyed by photo name. */
export const duo = fromGlob(import.meta.glob('../assets/duo/*.jpg', { eager: true }));
