"use client";

import { useEffect, useState } from 'react';
import { api } from '@/lib/api/client';
import { cn, formatDate } from '@/lib/utils';
import { Users, Zap, TrendingUp, AlertCircle, Clock, ChevronRight } from 'lucide-react';
import Link from 'next/link';

export default function Dashboard() {
  const [stats, setStats] = useState({
    competitors: 0,
    activeSources: 0,
    recentEvents: 0,
  });
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [comps, evs] = await Promise.all([
          api.getCompetitors(),
          api.getEvents({ limit: 5 })
        ]);

        setStats({
          competitors: comps.data.length,
          activeSources: comps.data.reduce((acc: number, c: any) => acc + (c.sources?.length || 0), 0),
          recentEvents: evs.data.length,
        });
        setEvents(evs.data);
      } catch (err) {
        console.error("Failed to fetch dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) return <div className="animate-pulse">Loading dashboard...</div>;

  return (
    <div className="space-y-10 animate-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">Welcome back</h1>
        <p className="text-muted-foreground">Here's what's happening across your competitor landscape.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { name: 'Total Competitors', value: stats.competitors, icon: Users, color: 'text-blue-500' },
          { name: 'Monitored Sources', value: stats.activeSources || 12, icon: Zap, color: 'text-amber-500' },
          { name: 'Recent Changes', value: stats.recentEvents, icon: TrendingUp, color: 'text-purple-500' },
        ].map((stat) => (
          <div key={stat.name} className="bg-card/30 border border-border p-6 rounded-2xl hover:border-primary/50 transition-colors">
            <div className="flex justify-between items-start mb-4">
              <div className={cn("p-2 rounded-xl bg-muted/50", stat.color)}>
                <stat.icon className="w-5 h-5" />
              </div>
            </div>
            <p className="text-muted-foreground text-sm font-medium">{stat.name}</p>
            <p className="text-3xl font-bold mt-1 tracking-tight">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <section className="bg-card/20 border border-border rounded-2xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary" />
              Recent Events
            </h2>
            <Link href="/events" className="text-primary text-sm font-medium flex items-center gap-1 hover:underline">
              View all <ChevronRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="space-y-4">
            {events.length > 0 ? events.map((event: any) => (
              <div key={event.id} className="group p-4 rounded-xl border border-border/50 bg-muted/20 hover:bg-muted/40 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500 uppercase tracking-wider">
                    {event.source_type || 'Update'}
                  </span>
                  <span className="text-xs text-muted-foreground">{formatDate(event.created_at)}</span>
                </div>
                <p className="text-sm font-medium mb-1 line-clamp-1">{event.diff_summary || 'Changes detected in source'}</p>
                <Link href={`/events/${event.id}`} className="text-xs text-primary font-medium hover:underline">View details</Link>
              </div>
            )) : (
              <div className="py-10 text-center text-muted-foreground bg-muted/10 rounded-xl border border-dashed border-border">
                No recent events detected.
              </div>
            )}
          </div>
        </section>

        <section className="bg-card/20 border border-border rounded-2xl p-6">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-amber-500" />
            System Insights
          </h2>
          <div className="space-y-4">
            <div className="p-4 rounded-xl border border-border/50 bg-amber-500/5 flex gap-4">
              <div className="w-10 h-10 rounded-full bg-amber-500/10 flex items-center justify-center shrink-0">
                <Users className="w-5 h-5 text-amber-500" />
              </div>
              <div>
                <p className="text-sm font-semibold">Low coverage for competitors</p>
                <p className="text-xs text-muted-foreground mt-1">3 competitors have less than 2 monitoring sources. Consider adding more URLs for better tracking.</p>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-border/50 bg-blue-500/5 flex gap-4">
              <div className="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center shrink-0">
                <Zap className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <p className="text-sm font-semibold">AI Analysis ready</p>
                <p className="text-xs text-muted-foreground mt-1">New changes detected in OpenAI's pricing page. AI has generated a draft battlecard update.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
