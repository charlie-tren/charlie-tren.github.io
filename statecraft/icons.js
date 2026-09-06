// One mark per domain, drawn rather than borrowed.
//
// WHY NOT EMOJI. A bare emoji reads as a character in a sentence, changes shape
// with whoever is looking at it, and cannot take the domain's own colour. These
// are thirteen paths on a shared 24x24 grid taking `currentColor`, so each one
// arrives in its section's hue with no second palette to keep in step.
//
// ONE DRAWING CONVENTION, so the set reads as a set: 24x24, 1.9 stroke, round
// caps and joins, no fills except where a solid shape IS the idea (the ballot
// mark, the pill). Anything that needed more than about five strokes was cut
// down until it did not, because these render at 18px beside a heading and fine
// detail turns to mush at that size. Tested at 18px before shipping.
//
// The failure mode to avoid is a mark that needs a caption. Each of these sits
// beside the domain's own name, so it has to be recognisable at a glance rather
// than be a rebus that can be solved.

const P = (d, extra = '') => `<path d="${d}" fill="none" stroke="currentColor"
  stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" ${extra}/>`;

export const DOMAIN_ICONS = {
  // Scales: the balance between what is raised and what is redistributed.
  tax: `${P('M12 4v16')}${P('M5 8h14')}${P('M5 8l-2.6 5.2a3 3 0 0 0 5.2 0z')}${P('M19 8l-2.6 5.2a3 3 0 0 0 5.2 0z')}`,
  // A cross in a rounded field, the sign a hospital already wears.
  healthcare: `${P('M12 7.5v9')}${P('M7.5 12h9')}${P('M4 6.2a2.2 2.2 0 0 1 2.2-2.2h11.6A2.2 2.2 0 0 1 20 6.2v11.6a2.2 2.2 0 0 1-2.2 2.2H6.2A2.2 2.2 0 0 1 4 17.8z')}`,
  // A mortarboard, read off the cap rather than the tassel.
  education: `${P('M2.5 9.2 12 5l9.5 4.2L12 13.4z')}${P('M6.6 11v4.6c0 1.5 2.4 2.7 5.4 2.7s5.4-1.2 5.4-2.7V11')}`,
  // A roof over a door.
  housing: `${P('M3.6 10.6 12 4l8.4 6.6')}${P('M5.8 12.4v6.4a1.2 1.2 0 0 0 1.2 1.2h10a1.2 1.2 0 0 0 1.2-1.2v-6.4')}${P('M10 20v-4.6h4V20')}`,
  // An hourglass: the domain is entirely about time and what is left.
  retirement: `${P('M7 3.6h10')}${P('M7 20.4h10')}${P('M7.6 3.6v3.1L12 12l-4.4 5.3v3.1')}${P('M16.4 3.6v3.1L12 12l4.4 5.3v3.1')}`,
  // A leaf on a stem, the cleanest one-stroke reading of a grid getting cleaner.
  energy: `${P('M12 20.4V11')}${P('M12 11c0-4 2.6-7 7.4-7.4C19.8 8.4 17 11.4 12 11z')}${P('M12 14.6c-3.4 0-5.6-2.1-6-5.6 3.6.3 5.7 2.3 6 5.6z')}`,
  // A speech bubble with a line running out of it.
  speech: `${P('M4 5.6a1.6 1.6 0 0 1 1.6-1.6h9.8A1.6 1.6 0 0 1 17 5.6v6.2a1.6 1.6 0 0 1-1.6 1.6H9l-3.6 3v-3H5.6A1.6 1.6 0 0 1 4 11.8z')}${P('M19.4 8.2c1.4 1.1 1.4 4.5 0 5.6')}`,
  // A ballot going into a box. The tick is the one solid mark in the set.
  voting: `${P('M4.2 12.6h15.6v6.2a1.2 1.2 0 0 1-1.2 1.2H5.4a1.2 1.2 0 0 1-1.2-1.2z')}${P('M7.4 12.6V4.8a.8.8 0 0 1 .8-.8h7.6a.8.8 0 0 1 .8.8v7.8')}${P('M9.9 8.3l1.7 1.7 3-3.3')}`,
  // Two figures, because the domain is bargaining rather than employment.
  work: `${P('M9 11.4a2.7 2.7 0 1 0 0-5.4 2.7 2.7 0 0 0 0 5.4z')}${P('M3.6 19.6c0-3 2.4-4.8 5.4-4.8s5.4 1.8 5.4 4.8')}${P('M16.2 7.4a2.2 2.2 0 1 1 0 4.4')}${P('M17.4 14.9c1.8.5 3 1.9 3 4.1')}`,
  // A shield, the one shape nobody misreads.
  defence: `${P('M12 3.6 5 6.2v5.3c0 4 2.9 7.4 7 8.9 4.1-1.5 7-4.9 7-8.9V6.2z')}`,
  // A passport stamp: a mark inside a border.
  immigration: `${P('M4.4 5.6a1.4 1.4 0 0 1 1.4-1.4h12.4a1.4 1.4 0 0 1 1.4 1.4v12.8a1.4 1.4 0 0 1-1.4 1.4H5.8a1.4 1.4 0 0 1-1.4-1.4z')}${P('M12 7.6a2.4 2.4 0 1 0 0 4.8 2.4 2.4 0 0 0 0-4.8z')}${P('M8 16.4h8')}`,
  // A gavel. Read off the head and the block, with the handle kept short.
  justice: `${P('M4.6 19.4h8.2')}${P('M6.4 12.2l4.4 4.4')}${P('M13.2 4.6l6.2 6.2')}${P('M15.4 2.9 21 8.5l-2.1 2.1-5.6-5.6z')}${P('M11.3 7 17 12.7l-2.4 2.4L8.9 9.4z')}`,
  // Two figures, one small, hand in hand.
  family: `${P('M8.6 8.4a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z')}${P('M4.4 20.4v-4.6c0-2.5 1.8-4.2 4.2-4.2s4.2 1.7 4.2 4.2v4.6')}${P('M16.6 13.4a1.9 1.9 0 1 0 0-3.8 1.9 1.9 0 0 0 0 3.8z')}${P('M13.6 20.4v-3.2c0-1.8 1.3-3 3-3s3 1.2 3 3v3.2')}`,
};

/** The mark for a domain, or an empty string where there is none. */
export function domainIcon(id) {
  const paths = DOMAIN_ICONS[id];
  if (!paths) return '';
  return `<svg class="d-ico" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${paths}</svg>`;
}
