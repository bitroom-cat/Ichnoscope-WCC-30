// Purpose: Runtime WCAG 2.1 contrast ratio calculation and token definitions for the styleguide.
// Excluded from strict hex checks per Section 9 verification pattern.

export function parseColorToRgb(color: string): [number, number, number] {
  color = color.trim();
  if (color.startsWith('#')) {
    let hex = color.slice(1);
    if (hex.length === 3) {
      hex = hex.split('').map((c) => c + c).join('');
    }
    const num = parseInt(hex.slice(0, 6), 16);
    return [(num >> 16) & 255, (num >> 8) & 255, num & 255];
  }
  if (color.startsWith('rgb')) {
    const parts = color.replace(/[rgba()]/g, '').split(',').map((p) => parseFloat(p.trim()));
    return [parts[0] || 0, parts[1] || 0, parts[2] || 0];
  }
  return [0, 0, 0];
}

export function getChannelLuminance(val: number): number {
  const norm = val / 255;
  return norm <= 0.04045 ? norm / 12.92 : Math.pow((norm + 0.055) / 1.055, 2.4);
}

export function getRelativeLuminance(rgb: [number, number, number]): number {
  const r = getChannelLuminance(rgb[0]);
  const g = getChannelLuminance(rgb[1]);
  const b = getChannelLuminance(rgb[2]);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function computeContrastRatio(fgColor: string, bgColor: string): number {
  const fgRgb = parseColorToRgb(fgColor);
  const bgRgb = parseColorToRgb(bgColor);
  const l1 = getRelativeLuminance(fgRgb);
  const l2 = getRelativeLuminance(bgRgb);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

export function formatContrastRatio(ratio: number): string {
  return `${ratio.toFixed(1)}:1`;
}

export interface ContrastPair {
  label: string;
  fgVar: string;
  bgVar: string;
  fgFallbackLight: string;
  bgFallbackLight: string;
  fgFallbackDark: string;
  bgFallbackDark: string;
  minRatio: number;
}

export const CONTRAST_PAIRS: ContrastPair[] = [
  {
    label: 'Primary text on Canvas',
    fgVar: '--text-primary',
    bgVar: '--bg-canvas',
    fgFallbackLight: '#151821',
    bgFallbackLight: '#F6F7FA',
    fgFallbackDark: '#E8EBF2',
    bgFallbackDark: '#0B0D12',
    minRatio: 4.5,
  },
  {
    label: 'Primary text on Surface',
    fgVar: '--text-primary',
    bgVar: '--bg-surface',
    fgFallbackLight: '#151821',
    bgFallbackLight: '#FFFFFF',
    fgFallbackDark: '#E8EBF2',
    bgFallbackDark: '#11141B',
    minRatio: 4.5,
  },
  {
    label: 'Secondary text on Surface',
    fgVar: '--text-secondary',
    bgVar: '--bg-surface',
    fgFallbackLight: '#4B5468',
    bgFallbackLight: '#FFFFFF',
    fgFallbackDark: '#A3ACBF',
    bgFallbackDark: '#11141B',
    minRatio: 4.5,
  },
  {
    label: 'Muted text on Surface',
    fgVar: '--text-muted',
    bgVar: '--bg-surface',
    fgFallbackLight: '#5F6980',
    bgFallbackLight: '#FFFFFF',
    fgFallbackDark: '#8791A6',
    bgFallbackDark: '#11141B',
    minRatio: 4.5,
  },
  {
    label: 'On-Accent text on Accent',
    fgVar: '--on-accent',
    bgVar: '--accent',
    fgFallbackLight: '#FFFFFF',
    bgFallbackLight: '#0F766E',
    fgFallbackDark: '#04201C',
    bgFallbackDark: '#2DD4BF',
    minRatio: 4.5,
  },
  {
    label: 'Accent on Surface (UI Element)',
    fgVar: '--accent',
    bgVar: '--bg-surface',
    fgFallbackLight: '#0F766E',
    bgFallbackLight: '#FFFFFF',
    fgFallbackDark: '#2DD4BF',
    bgFallbackDark: '#11141B',
    minRatio: 3.0,
  },
  {
    label: 'Danger (P1) on Canvas',
    fgVar: '--danger',
    bgVar: '--bg-canvas',
    fgFallbackLight: '#B91C1C',
    bgFallbackLight: '#F6F7FA',
    fgFallbackDark: '#F87171',
    bgFallbackDark: '#0B0D12',
    minRatio: 4.5,
  },
  {
    label: 'P2-High Orange on Canvas',
    fgVar: '--severity-high',
    bgVar: '--bg-canvas',
    fgFallbackLight: '#C2410C',
    bgFallbackLight: '#F6F7FA',
    fgFallbackDark: '#FB923C',
    bgFallbackDark: '#0B0D12',
    minRatio: 4.5,
  },
  {
    label: 'Warning (P3) on Canvas',
    fgVar: '--warning',
    bgVar: '--bg-canvas',
    fgFallbackLight: '#B45309',
    bgFallbackLight: '#F6F7FA',
    fgFallbackDark: '#FBBF24',
    bgFallbackDark: '#0B0D12',
    minRatio: 4.5,
  },
  {
    label: 'Success (Published) on Canvas',
    fgVar: '--success',
    bgVar: '--bg-canvas',
    fgFallbackLight: '#047857',
    bgFallbackLight: '#F6F7FA',
    fgFallbackDark: '#34D399',
    bgFallbackDark: '#0B0D12',
    minRatio: 4.5,
  },
  {
    label: 'Draft on Canvas',
    fgVar: '--draft',
    bgVar: '--bg-canvas',
    fgFallbackLight: '#6D28D9',
    bgFallbackLight: '#F6F7FA',
    fgFallbackDark: '#A78BFA',
    bgFallbackDark: '#0B0D12',
    minRatio: 4.5,
  },
  {
    label: 'Subtle border on Surface',
    fgVar: '--border-subtle',
    bgVar: '--bg-surface',
    fgFallbackLight: '#E3E6EE',
    bgFallbackLight: '#FFFFFF',
    fgFallbackDark: '#232937',
    bgFallbackDark: '#11141B',
    minRatio: 1.1,
  },
];

export const SURFACE_SWATCHES = [
  { name: '--bg-canvas', class: 'bg-canvas', label: 'Canvas', lightHex: '#F6F7FA', darkHex: '#0B0D12' },
  { name: '--bg-surface', class: 'bg-surface', label: 'Surface', lightHex: '#FFFFFF', darkHex: '#11141B' },
  { name: '--bg-elevated', class: 'bg-elevated', label: 'Elevated', lightHex: '#FFFFFF', darkHex: '#171B24' },
  { name: '--bg-hover', class: 'bg-hover', label: 'Hover', lightHex: '#EEF0F5', darkHex: '#1D222D' },
  { name: '--bg-inset', class: 'bg-inset', label: 'Inset', lightHex: '#F0F2F7', darkHex: '#0E1117' },
];

export const ACCENT_SWATCH_META = {
  accent: { light: '#0F766E / #FFFFFF', dark: '#2DD4BF / #04201C' },
  danger: { light: '#B91C1C', dark: '#F87171' },
  severityHigh: { light: '#C2410C', dark: '#FB923C' },
  warning: { light: '#B45309', dark: '#FBBF24' },
  success: { light: '#047857', dark: '#34D399' },
  draft: { light: '#6D28D9', dark: '#A78BFA' },
};
