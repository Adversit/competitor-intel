"use client";

import { useEffect, useState, use } from 'react';
import { api } from '@/lib/api/client';
import { formatDate } from '@/lib/utils';
import { ChevronLeft, Globe, Zap, Plus, Settings, Activity, Trash2, ExternalLink } from 'lucide-react';
import Link from 'next/link';

export default function CompetitorDetail({ params: paramsPromise }: { params: Promise<{ id: string }> }) {
    const params = use(paramsPromise);
    const [competitor, setCompetitor] = useState<any>(null);
    const [sources, setSources] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isAddSourceOpen, setIsAddSourceOpen] = useState(false);
    const [newSource, setNewSource] = useState({ url: '', source_type: 'homepage', fetch_mode: 'http' });

    async function fetchData() {
        try {
            const [compRes, sourcesRes] = await Promise.all([
                api.getCompetitor(params.id),
                api.getSources(params.id)
            ]);
            setCompetitor(compRes.data);
            setSources(sourcesRes.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        fetchData();
    }, [params.id]);

    const handleAddSource = async (e: any) => {
        e.preventDefault();
        try {
            await api.createSource({ ...newSource, competitor_id: params.id });
            setIsAddSourceOpen(false);
            setNewSource({ url: '', source_type: 'homepage', fetch_mode: 'http' });
            fetchData();
        } catch (err) {
            alert("Error adding source");
        }
    };

    const handleTestFetch = async (sourceId: string) => {
        try {
            alert("Triggering fetch... this might take a few seconds.");
            await api.testSource(sourceId);
            alert("Successful fetch!");
        } catch (err) {
            alert("Fetch failed. Check URL or firewall settings.");
        }
    };

    if (loading) return <div className="p-8">Loading competitor details...</div>;

    return (
        <div className="space-y-10 animate-in">
            <div className="flex items-center gap-4">
                <Link href="/competitors" className="p-2 rounded-xl hover:bg-muted transition-colors">
                    <ChevronLeft className="w-5 h-5" />
                </Link>
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">{competitor?.name}</h1>
                    <div className="flex items-center gap-4 mt-1">
                        <a href={competitor?.website} target="_blank" className="text-sm text-primary flex items-center gap-1 hover:underline">
                            <Globe className="w-3.5 h-3.5" />
                            {competitor?.website}
                            <ExternalLink className="w-3 h-3" />
                        </a>
                        <span className="text-muted-foreground text-sm">• {competitor?.category}</span>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-8">
                    <section className="bg-card/20 border border-border rounded-3xl p-8">
                        <div className="flex justify-between items-center mb-8">
                            <h2 className="text-xl font-bold flex items-center gap-2">
                                <Activity className="w-5 h-5 text-primary" />
                                Monitoring Sources
                            </h2>
                            <button
                                onClick={() => setIsAddSourceOpen(true)}
                                className="bg-primary/10 text-primary px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2 hover:bg-primary/20 transition-all"
                            >
                                <Plus className="w-4 h-4" />
                                Add URL
                            </button>
                        </div>

                        <div className="space-y-4">
                            {sources.length > 0 ? sources.map((source: any) => (
                                <div key={source.id} className="p-5 rounded-2xl border border-border/50 bg-muted/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
                                    <div className="space-y-1 overflow-hidden">
                                        <div className="flex items-center gap-2">
                                            <span className="text-[10px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-500 border border-blue-500/20">
                                                {source.source_type}
                                            </span>
                                            <span className="text-xs text-muted-foreground">{source.fetch_mode === 'headless' ? 'Headless Browser' : 'HTTP/JSON'}</span>
                                        </div>
                                        <p className="text-sm font-medium truncate max-w-md">{source.url}</p>
                                    </div>

                                    <div className="flex items-center gap-3 shrink-0">
                                        <button
                                            onClick={() => handleTestFetch(source.id)}
                                            className="px-3 py-1.5 rounded-lg border border-border hover:bg-muted text-xs font-semibold transition-colors"
                                        >
                                            Test Fetch
                                        </button>
                                        <button
                                            className="p-2 rounded-lg text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                                            title="Settings"
                                            aria-label="Settings"
                                        >
                                            <Settings className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            )) : (
                                <div className="py-12 text-center text-muted-foreground bg-muted/10 rounded-2xl border border-dashed border-border">
                                    No sources monitored for this competitor.
                                </div>
                            )}
                        </div>
                    </section>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <Link
                            href={`/battlecards/${params.id}`}
                            className="group bg-primary/5 border border-primary/20 rounded-2xl p-6 hover:bg-primary/10 transition-all"
                        >
                            <ScrollText className="w-8 h-8 text-primary mb-4" />
                            <h3 className="font-bold text-lg">View Battlecard</h3>
                            <p className="text-sm text-muted-foreground mt-2">See current strengths, weaknesses and market positioning.</p>
                        </Link>
                        <div className="bg-card/20 border border-border rounded-2xl p-6">
                            <Zap className="w-8 h-8 text-amber-500 mb-4" />
                            <h3 className="font-bold text-lg">Trigger Scan</h3>
                            <p className="text-sm text-muted-foreground mt-2">Force a full system crawl of all associated monitoring sources.</p>
                        </div>
                    </div>
                </div>

                <aside className="space-y-6">
                    <div className="bg-card/20 border border-border rounded-2xl p-6">
                        <h3 className="font-bold mb-4">Competitor Metadata</h3>
                        <div className="space-y-4">
                            <div className="space-y-1">
                                <p className="text-xs text-muted-foreground">Owner Team</p>
                                <p className="text-sm font-medium">{competitor?.owner_team || 'Corporate Strategy'}</p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-xs text-muted-foreground">Tags</p>
                                <div className="flex flex-wrap gap-2 pt-1">
                                    {(competitor?.tags || ['Enterprise', 'LLM']).map((tag: string) => (
                                        <span key={tag} className="px-2 py-0.5 bg-muted rounded text-[10px] font-bold uppercase border border-border/50">{tag}</span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </aside>
            </div>

            {isAddSourceOpen && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-card border border-border w-full max-w-md rounded-3xl p-8 animate-in">
                        <h2 className="text-2xl font-bold mb-6">Add Monitoring URL</h2>
                        <form onSubmit={handleAddSource} className="space-y-5">
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-muted-foreground">URL</label>
                                <input
                                    required
                                    value={newSource.url}
                                    onChange={e => setNewSource({ ...newSource, url: e.target.value })}
                                    className="w-full bg-muted border border-border rounded-xl px-4 py-3 font-medium"
                                    placeholder="https://..."
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-muted-foreground">Type</label>
                                    <select
                                        value={newSource.source_type}
                                        onChange={e => setNewSource({ ...newSource, source_type: e.target.value })}
                                        className="w-full bg-muted border border-border rounded-xl px-4 py-3 appearance-none font-medium"
                                        aria-label="Source Type"
                                        title="Source Type"
                                    >
                                        {['homepage', 'pricing', 'changelog', 'docs', 'news'].map(t => (
                                            <option key={t} value={t}>{t}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-muted-foreground">Fetch Mode</label>
                                    <select
                                        value={newSource.fetch_mode}
                                        onChange={e => setNewSource({ ...newSource, fetch_mode: e.target.value })}
                                        className="w-full bg-muted border border-border rounded-xl px-4 py-3 appearance-none font-medium"
                                        aria-label="Fetch Mode"
                                        title="Fetch Mode"
                                    >
                                        <option value="http">Fast HTTP</option>
                                        <option value="headless">Headless (JS)</option>
                                    </select>
                                </div>
                            </div>
                            <div className="flex gap-4 pt-4">
                                <button type="button" onClick={() => setIsAddSourceOpen(false)} className="flex-1 px-4 py-3 rounded-xl border border-border font-bold">Cancel</button>
                                <button type="submit" className="flex-1 bg-primary text-white px-4 py-3 rounded-xl font-bold">Add Source</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

const ScrollText = ({ className }: { className?: string }) => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
    >
        <path d="M7 12h10" />
        <path d="M7 16h10" />
        <path d="M7 8h10" />
        <path d="M19 21V5a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v16l3.5-2 3.5 2 3.5-2Z" />
    </svg>
);
