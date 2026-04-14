"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { navigation } from "@/data/navigation";
import { branding } from "@/data/branding";
import { logout } from "@/app/auth/actions";
import { HomeIcon, SearchIcon, ChatIcon, FavoritesIcon, SettingsIcon, LogoutIcon } from "@/components/ui/icons";

const iconMap: Record<string, React.ComponentType<React.SVGProps<SVGSVGElement>>> = {
  home: HomeIcon,
  search: SearchIcon,
  chat: ChatIcon,
  favorites: FavoritesIcon,
  settings: SettingsIcon,
};

export function Sidebar() {
  const pathname = usePathname();

  return (
    <>
      {/* Desktop sidebar */}
      <nav className="sidebar" aria-label="Main navigation">
        <div className="sidebar-brand">
          <Image
            src="/logo.png"
            alt={branding.appName}
            width={32}
            height={32}
            className="sidebar-logo"
          />
          <span className="sidebar-brand-text">{branding.appName}</span>
        </div>

        <div className="sidebar-nav">
          {navigation.items.map((item) => {
            const Icon = iconMap[item.icon];
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`sidebar-item${isActive ? " active" : ""}`}
                title={item.label}
              >
                <Icon />
                <span className="sidebar-label">{item.label}</span>
              </Link>
            );
          })}
        </div>

        <form action={logout} className="sidebar-logout">
          <button type="submit" className="sidebar-item" title="Sign Out">
            <LogoutIcon />
            <span className="sidebar-label">Sign Out</span>
          </button>
        </form>
      </nav>

      {/* Mobile bottom nav */}
      <nav className="mobile-nav" aria-label="Main navigation">
        {navigation.items.map((item) => {
          const Icon = iconMap[item.icon];
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`mobile-nav-item${isActive ? " active" : ""}`}
            >
              <Icon width={22} height={22} />
            </Link>
          );
        })}
      </nav>
    </>
  );
}
