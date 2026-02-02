"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { LayoutDashboard, Users, Zap, ScrollText, Settings } from 'lucide-react';

const navItems = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Competitors', href: '/competitors', icon: Users },
    { name: 'Events', href: '/events', icon: Zap },
    { name: 'Battlecards', href: '/battlecards', icon: ScrollText },
];

export default function Navbar() {
    const pathname = usePathname();

    return (
        <nav className="fixed left-0 top-0 h-full w-64 border-r border-border bg-card/50 backdrop-blur-xl p-6 hidden md:block">
            <div className="flex items-center gap-2 mb-10 px-2">
                <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                    <Zap className="text-white w-5 h-5" />
                </div>
                <span className="text-xl font-bold tracking-tight">Molt Intel</span>
            </div>

            <div className="space-y-1">
                {navItems.map((item) => {
                    const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group",
                                isActive
                                    ? "bg-primary/10 text-primary shadow-[0_0_20px_rgba(59,130,246,0.1)]"
                                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                            )}
                        >
                            <item.icon className={cn(
                                "w-5 h-5",
                                isActive ? "text-primary" : "group-hover:text-foreground"
                            )} />
                            <span className="font-medium">{item.name}</span>
                        </Link>
                    );
                })}
            </div>

            <div className="absolute bottom-6 left-6 right-6 space-y-2">
                <Link
                    href="/settings"
                    className={cn(
                        "flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group text-muted-foreground hover:bg-muted hover:text-foreground",
                        pathname === '/settings' && "bg-primary/10 text-primary"
                    )}
                >
                    <Settings className="w-5 h-5" />
                    <span className="font-medium">Settings</span>
                </Link>

                <div className="bg-muted/50 rounded-2xl p-4 border border-border/50">
                    <p className="text-xs text-muted-foreground mb-2 whitespace-nowrap overflow-hidden text-ellipsis">System Status</p>
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                        <span className="text-sm font-medium">All systems active</span>
                    </div>
                </div>
            </div>
        </nav>
    );
}
