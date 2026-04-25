/**
 * Vellum Theme Contract
 * =====================
 *
 * Defines the visual identity for any Vellum UI consumer.
 * Consumers provide their own theme values; the SDK renders accordingly.
 *
 * Mirrors the backend's zero-dependency philosophy:
 * the SDK defines the interface, the consumer provides the implementation.
 */

export interface VellumTheme {
  colors: VellumColors;
  typography: VellumTypography;
  spacing: VellumSpacing;
  borderRadius: VellumBorderRadius;
  shadows: VellumShadows;
  zIndex: VellumZIndex;
}

export interface VellumColors {
  /** Primary brand color (buttons, links, active states) */
  primary: string;
  primaryDark: string;
  primaryLight: string;

  /** Text hierarchy */
  textPrimary: string;
  textSecondary: string;
  textMuted: string;

  /** Surfaces */
  background: string;
  backgroundPaper: string;
  backgroundSubtle: string;
  surfaceRaised: string;

  /** Borders */
  divider: string;
  borderLight: string;

  /** Form inputs */
  inputBackground: string;

  /** Semantic status */
  success: string;
  successBg: string;
  successText: string;
  error: string;
  errorBg: string;
  errorText: string;
  warning: string;
  warningBg: string;
  warningText: string;
}

export interface VellumTypography {
  fontFamily: string;
  headingFontFamily: string;
  scale: {
    h1: TypographySpec;
    h2: TypographySpec;
    h3: TypographySpec;
    h4: TypographySpec;
    h5: TypographySpec;
    h6: TypographySpec;
    body1: TypographySpec;
    body2: TypographySpec;
    caption: TypographySpec;
  };
}

export interface TypographySpec {
  fontSize: string;
  fontWeight: number;
  lineHeight: string;
  letterSpacing?: string;
}

export interface VellumSpacing {
  xs: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
  xxl: string;
}

export interface VellumBorderRadius {
  none: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
  full: string;
}

export interface VellumShadows {
  none: string;
  subtle: string;
  card: string;
  elevated: string;
}

export interface VellumZIndex {
  base: number;
  raised: number;
  dropdown: number;
  sticky: number;
  modal: number;
  toast: number;
}
