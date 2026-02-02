"use client";

import { useEffect, useState } from 'react';
import { api } from '@/lib/api/client';
import { formatDate } from '@/lib/utils';
import { Zap, ThumbsUp, ThumbsDown, Filter, Search, ChevronDown, Monitor } from 'lucide-react';

export default function Events() {
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);

    async function fetchEvents() {
        try {
            const res = await api.getEvents({ limit: 50 });
            setEvents(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        fetchEvents();
    }, []);

    const handleFeedback = async (id: string, useful: boolean) => {
        try {
            await api.feedbackEvent(id, useful);
            // Refresh or update local state
            alert("Feedback submitted");
        } catch (err) {
            console.error(err);
        }
    };

    if (loading) return <div className="animate-pulse">Loading events...</div>;

    return (
        <div className="space-y-8 animate-in">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight mb-2">Event Feed</h1>
                    <p className="text-muted-foreground">Real-time detection of changes and developments.</p>
                </div>
                <div className="flex gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <input className="bg-muted border border-border rounded-xl pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary w-64" placeholder="Search events..." />
                    </div>
                    <button className="bg-muted border border-border rounded-xl px-4 py-2 text-sm font-medium flex items-center gap-2 hover:bg-muted/80">
                        <Filter className="w-4 h-4" />
                        Filter
                        <ChevronDown className="w-4 h-4" />
                    </button>
                </div>
            </div>

            <div className="space-y-4">
                {events.map((event: any) => (
                    <div key={event.id} className="bg-card/30 border border-border rounded-2xl overflow-hidden hover:border-border/80 transition-all">
                        <div className="p-6">
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-primary/10 text-primary">
                                        <Zap className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-lg">{event.diff_summary || 'Changes Detected'}</h3>
                                        <p className="text-sm text-muted-foreground flex items-center gap-2">
                                            {formatDate(event.created_at)}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => handleFeedback(event.id, true)}
                                        className="p-2 rounded-lg hover:bg-green-500/10 text-muted-foreground hover:text-green-500 transition-colors"
                                        title="Helpful"
                                        aria-label="Helpful"
                                    >
                                        <ThumbsUp className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => handleFeedback(event.id, false)}
                                        className="p-2 rounded-lg hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition-colors"
                                        title="Not Helpful"
                                        aria-label="Not Helpful"
                                    >
                                        <ThumbsDown className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>

                            {event.diff_chunks ? (
                                <div className="mt-4 bg-black/50 rounded-xl p-4 font-mono text-xs border border-border/50 max-h-64 overflow-auto">
                                    {event.diff_chunks.map((chunk: any, i: number) => (
                                        <div key={i} className="mb-4 last:mb-0">
                                            <div className="text-muted-foreground mb-1 border-b border-border/30 pb-1">@@ Chunk {i + 1} @@</div>
                                            {chunk.added && <div className="text-green-400 bg-green-500/5 py-0.5 px-2 rounded whitespace-pre-wrap">+ {chunk.added}</div>}
                                            {chunk.removed && <div className="text-red-400 bg-red-500/5 py-0.5 px-2 rounded whitespace-pre-wrap">- {chunk.removed}</div>}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="mt-4 p-4 rounded-xl border border-dashed border-border bg-muted/10 text-center text-sm text-muted-foreground">
                                    View full snapshot in details to see specific content changes.
                                </div>
                            )}

                            <div className="mt-6 pt-6 border-t border-border/50 flex justify-between items-center">
                                <div className="flex items-center gap-4">
                                    <span className="text-xs font-semibold px-2 py-1 rounded bg-muted text-muted-foreground border border-border/50">
                                        SENSITIVITY: {event.sensitivity || 'MEDIUM'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}

                {events.length === 0 && (
                    <div className="py-20 text-center text-muted-foreground grayscale">
                        <Monitor className="w-12 h-12 mx-auto mb-4 opacity-20" />
                        <p className="text-lg font-medium">Listening for changes...</p>
                        <p className="text-sm">Once your sources are crawled, events will appear here.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
