/**
 * Self-hosted photography (Unsplash licence: free to use, no attribution
 * required). Each photo ships as AVIF + WebP at the widths below, generated
 * from the originals; `color` is its average tone, shown while it loads.
 */
export const PHOTO_WIDTHS = [480, 960, 1600, 2200] as const

export const PHOTOS = {
  port: { w: 2400, h: 1600, color: '#92948E' },
  ship: { w: 2400, h: 1600, color: '#858E93' },
  cranes: { w: 2400, h: 1600, color: '#8B8D8D' },
  plane: { w: 2400, h: 1594, color: '#AAB0B4' },
  train: { w: 2400, h: 1415, color: '#706652' },
  truck: { w: 2400, h: 1600, color: '#3A839C' },
  highway: { w: 2400, h: 1591, color: '#90A395' },
  parcel: { w: 2400, h: 3000, color: '#4A5D68', maxWidth: 1600 },
  warehouse: { w: 2400, h: 1600, color: '#867A58' },
  night: { w: 2400, h: 1277, color: '#353536' },
  contract: { w: 2400, h: 1602, color: '#D1C0B3' },
} as const satisfies Record<string, { w: number; h: number; color: string; maxWidth?: number }>

export type PhotoKey = keyof typeof PHOTOS

/** Which photo stands for each transport mode (by mode code). */
export const MODE_PHOTOS: Record<string, PhotoKey> = {
  sea_fcl: 'ship',
  sea_lcl: 'cranes',
  air: 'plane',
  road_ftl: 'truck',
  road_ltl: 'highway',
  rail: 'train',
  courier: 'parcel',
  project: 'port',
}
