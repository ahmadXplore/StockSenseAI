/**
 * Auth layout — intentionally bare.
 * No Navbar, no DeviceGate, no MarketContextBar, no footer.
 * The auth page is always publicly accessible so users can log in.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
